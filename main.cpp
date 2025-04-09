#include "mbed.h"
#include "LCDi2c.h"
#include <stdio.h>
#include <cstring> // Required for strlen()

// Create I2C interface
I2C i2c(PTE25, PTE24); // SDA, SCL

// Create LCD object
LCDi2c lcd(PTE25, PTE24, LCD20x4, 0x27);

// Initialize the digital pin LED1 as an output
DigitalOut led(LED1);

// Button for sensor reading
InterruptIn button(PTC3);
volatile bool buttonPressed = false;

// Display mode that will automatically cycle
int displayMode = 0;     // 0 = Env Data, 1 = Air Quality, 2 = Combined View, 3 = Particle Data, 4 = WiFi Status, 5 = API Results
int numDisplayModes = 6; // Total number of display modes (added API Results mode)

// Define PMS5003 pins using Arduino pin names for better compatibility
// PTC17 = D1 (TX) and PTC16 = D0 (RX) on K64F board
// Serial connections for PMS5003
BufferedSerial pms5003(D1, D0, 9600);

// Using UART2 (PTD3, PTD2) for ESP8266 to avoid conflicts
static BufferedSerial esp8266(PTD3, PTD2, 115200); // TX: PTD3, RX: PTD2

// WiFi connection status flag
bool wifi_connected = false;
char ip_address[16] = "Not Connected";

// I2C addresses
#define BME680_ADDR 0x76
#define ENS160_ADDR 0x53 // Use the address that worked in your standalone code

// BME680 registers
#define BME680_REG_CHIP_ID 0xD0
#define BME680_REG_RESET 0xE0
#define BME680_REG_CTRL_HUM 0x72
#define BME680_REG_CTRL_MEAS 0x74
#define BME680_REG_CONFIG 0x75
#define BME680_REG_STATUS 0x73
#define BME680_REG_TEMP_MSB 0x22
#define BME680_REG_TEMP_LSB 0x23
#define BME680_REG_TEMP_XLSB 0x24
#define BME680_REG_PRESS_MSB 0x1F
#define BME680_REG_PRESS_LSB 0x20
#define BME680_REG_PRESS_XLSB 0x21
#define BME680_REG_HUM_MSB 0x25
#define BME680_REG_HUM_LSB 0x26

// ENS160 Register addresses
#define ENS160_REG_PART_ID 0x00
#define ENS160_REG_OP_MODE 0x10
#define ENS160_REG_STATUS 0x20
#define ENS160_REG_DATA_AQI 0x21
#define ENS160_REG_DATA_TVOC 0x22
#define ENS160_REG_DATA_ECO2 0x24
#define ENS160_REG_TEMP_IN 0x30
#define ENS160_REG_RH_IN 0x32

// ENS160 Operation modes
#define ENS160_OPMODE_IDLE 0x01
#define ENS160_OPMODE_STD 0x02

// Temperature calibration offset for BME680
#define TEMP_CALIB_OFFSET -700 // -70.0 degrees, using fixed-point

// Variables to store sensor readings
int32_t temp_x10 = 0;
int32_t pressure_x10 = 0;
int32_t humidity_x10 = 0;
uint8_t aqi = 1;     // Default AQI (excellent)
uint16_t tvoc = 0;   // Default TVOC
uint16_t eco2 = 400; // Default eCO2

// Variables for PMS5003 readings
uint16_t pm1_0 = 0;
uint16_t pm2_5 = 0;
uint16_t pm10 = 0;
uint16_t particles_03um = 0;
uint16_t particles_05um = 0;
uint16_t particles_10um = 0;
uint16_t particles_25um = 0;
uint16_t particles_50um = 0;
uint16_t particles_100um = 0;
int reading_counter = 0; // Counter for PMS5003 readings

// API related variables
bool air_quality_unsafe = false;
float air_quality_probability = 0.0;
bool fire_detected = false;
float fire_probability = 0.0;
char api_message[100] = "No data from API";

// Flags for sensor initialization status
bool bme680_ok = false;
bool ens160_ok = false;
bool pms5003_ok = false;
bool esp8266_ok = false;

// Time of last sensor reading
Timer sensorReadTimer;

// Function to send data over UART to ESP8266
// Function to send data over UART to ESP8266 with improved reliability
void sendESP8266Command(const char *cmd)
{
    // Clear any pending data first
    char buffer;
    while (esp8266.readable())
    {
        esp8266.read(&buffer, 1);
    }

    // Send command
    esp8266.write(cmd, strlen(cmd));
    esp8266.write("\r\n", 2);
    printf("Sent: %s\n", cmd);

    // Short delay to ensure command is processed
    ThisThread::sleep_for(100ms);
}

// Function to read ESP8266 response with better timeout handling
bool readESP8266Response(int timeout_ms = 10000, const char *success_msg = "OK")
{
    char response[1024] = {0}; // Buffer for response
    int i = 0;
    Timer t;
    t.start();

    // Wait for at least one character to arrive before starting timeout
    int initial_wait = 0;
    while (!esp8266.readable() && initial_wait < 1000)
    {
        ThisThread::sleep_for(10ms);
        initial_wait += 10;
    }

    // If nothing received in initial wait, return false
    if (initial_wait >= 1000 && !esp8266.readable())
    {
        printf("No response from ESP8266 during initial wait\n");
        return false;
    }

    // Read response with timeout
    while (t.elapsed_time() < chrono::milliseconds(timeout_ms))
    {
        if (esp8266.readable())
        {
            if (i < 1023)
            {
                esp8266.read(&response[i], 1);
                printf("%c", response[i]); // Echo to console
                i++;

                // Exit early if success message found
                if (i >= strlen(success_msg))
                {
                    if (strstr(response + i - strlen(success_msg), success_msg))
                    {
                        break;
                    }
                }
            }
            else
            {
                printf("\nWarning: Buffer Full\n");
                break;
            }
        }
        else
        {
            // Small sleep when no data available to prevent CPU hogging
            ThisThread::sleep_for(5ms);
        }
    }

    response[i] = '\0';
    printf("\nResponse: [%s]\n", response); // Add brackets to see entire response including whitespace

    // Check for success message
    if (strstr(response, success_msg))
    {
        return true;
    }

    return false;
}

// Simplified function to send HTTP request to API
bool sendAPIRequest(const char *path, const char *json_data)
{
    if (!wifi_connected)
    {
        printf("Cannot send data: WiFi not connected\n");
        strcpy(api_message, "WiFi not connected");
        return false;
    }

    // Reset ESP8266 to ensure clean state
    printf("Resetting ESP8266 before API request...\n");
    timeout_safe_esp8266_command("AT+RST");
    ThisThread::sleep_for(2000ms);

    // Test if ESP8266 is responsive
    printf("Testing ESP8266...\n");
    sendESP8266Command("AT");
    if (!readESP8266Response(2000))
    {
        printf("ESP8266 not responding\n");
        strcpy(api_message, "ESP not responding");
        return false;
    }

    // Set WiFi mode to station
    printf("Setting WiFi mode...\n");
    sendESP8266Command("AT+CWMODE=1");
    if (!readESP8266Response(2000))
    {
        printf("Failed to set WiFi mode\n");
        return false;
    }

    // Reconnect to WiFi if needed
    if (!wifi_connected)
    {
        printf("Connecting to WiFi...\n");
        sendESP8266Command("AT+CWJAP=\"arvin armand\",\"tehran77\"");
        if (!readESP8266Response(20000, "WIFI GOT IP"))
        {
            printf("Failed to connect to WiFi\n");
            return false;
        }
        wifi_connected = true;
    }

    // Setup the TCP connection
    printf("Setting up TCP connection...\n");
    sendESP8266Command("AT+CIPSTART=\"TCP\",\"embedapi.botechgida.com\",80");
    if (!readESP8266Response(5000, "OK"))
    {
        printf("Failed to establish TCP connection\n");
        strcpy(api_message, "TCP conn failed");
        return false;
    }

    // Prepare the HTTP request
    char request[1024];
    snprintf(request, sizeof(request),
             "POST %s HTTP/1.1\r\n"
             "Host: embedapi.botechgida.com\r\n"
             "Content-Type: application/json\r\n"
             "Content-Length: %d\r\n"
             "Connection: close\r\n"
             "\r\n"
             "%s",
             path, strlen(json_data), json_data);

    // Send the request length
    char cmd[32];
    snprintf(cmd, sizeof(cmd), "AT+CIPSEND=%d", strlen(request));
    sendESP8266Command(cmd);
    if (!readESP8266Response(5000, ">"))
    {
        printf("Failed to get send prompt\n");
        strcpy(api_message, "Send failed");
        return false;
    }

    // Send the actual request
    printf("Sending HTTP request...\n");
    for (size_t i = 0; i < strlen(request); i++)
    {
        esp8266.write(&request[i], 1);
        ThisThread::sleep_for(1ms); // Small delay to prevent overflowing ESP8266 buffer
    }
    printf("Request sent: %s\n", request);

    // Read response with a longer timeout
    char response[1024] = {0};
    int i = 0;
    Timer t;
    t.start();
    bool json_found = false;
    int json_start = 0;

    printf("Reading response...\n");
    while (t.elapsed_time() < chrono::milliseconds(15000))
    {
        if (esp8266.readable())
        {
            if (i < 1023)
            {
                esp8266.read(&response[i], 1);
                printf("%c", response[i]); // Print character to console for debugging

                // Look for start of JSON - typically after blank line following headers
                if (i >= 3 && response[i - 3] == '\r' && response[i - 2] == '\n' &&
                    response[i - 1] == '\r' && response[i] == '\n')
                {
                    json_start = i + 1;
                }

                // If we found JSON start and then a closing brace, we likely have complete JSON
                if (json_start > 0 && response[i] == '}')
                {
                    json_found = true;
                    i++;
                    break;
                }

                i++;
            }
            else
            {
                printf("\nBuffer full!\n");
                break;
            }
        }
        else
        {
            ThisThread::sleep_for(5ms);
        }
    }

    response[i] = '\0';
    printf("\nFull Response: [%s]\n", response);

    // Extract and parse JSON from response
    char *json_response = NULL;
    if (json_found && json_start < i)
    {
        json_response = &response[json_start];
        printf("Extracted JSON: %s\n", json_response);

        // For debugging - print the entire JSON response as hex to see special characters
        printf("JSON as hex: ");
        for (int j = 0; j < strlen(json_response); j++)
        {
            printf("%02X ", (unsigned char)json_response[j]);
        }
        printf("\n");
    }

    // Close the connection
    sendESP8266Command("AT+CIPCLOSE");
    readESP8266Response(1000);

    if (!json_response)
    {
        printf("No JSON response found\n");
        strcpy(api_message, "No JSON found");
        return false;
    }

    return true;
}

// Initialize ESP8266 and connect to WiFi
// Initialize ESP8266 and connect to WiFi with improved reset handling
bool initESP8266()
{
    printf("\nInitializing ESP8266 module...\n");

    // Wait for ESP8266 to boot up
    ThisThread::sleep_for(2000ms);

    // Clear any pending data first
    char buffer;
    while (esp8266.readable())
    {
        esp8266.read(&buffer, 1);
    }

    // Test AT command with retries
    int retries = 3;
    bool at_ok = false;

    while (retries > 0 && !at_ok)
    {
        printf("Testing ESP8266 (attempt %d)...\n", 4 - retries);
        sendESP8266Command("AT");
        at_ok = readESP8266Response(1000);
        if (!at_ok)
        {
            ThisThread::sleep_for(1000ms);
        }
        retries--;
    }

    if (!at_ok)
    {
        printf("ESP8266 not responding to AT command after multiple attempts\n");
        return false;
    }

    printf("ESP8266 is responsive\n");

    // Reset module with timeout protection
    printf("Resetting ESP8266...\n");
    timeout_safe_esp8266_command("AT+RST");

    // Don't wait for a response from reset - it may not come back properly
    printf("Waiting for ESP8266 to reboot...\n");
    ThisThread::sleep_for(5000ms);

    // Clear buffer again after reset
    while (esp8266.readable())
    {
        esp8266.read(&buffer, 1);
    }

    // Verify ESP8266 is responsive again after reset
    printf("Checking ESP8266 after reset...\n");

    // Multiple attempts to check if ESP8266 is responding after reset
    at_ok = false;
    retries = 5; // More retries after reset

    while (retries > 0 && !at_ok)
    {
        sendESP8266Command("AT");
        at_ok = readESP8266Response(1000);
        if (!at_ok)
        {
            printf("ESP8266 not responsive yet, waiting...\n");
            ThisThread::sleep_for(1000ms);
        }
        retries--;
    }

    if (!at_ok)
    {
        printf("ESP8266 not responding after reset\n");
        return false;
    }

    printf("ESP8266 successfully reset and responding\n");

    // Set WiFi mode to station with retries
    retries = 3;
    bool mode_ok = false;

    while (retries > 0 && !mode_ok)
    {
        printf("Setting WiFi mode (attempt %d)...\n", 4 - retries);
        sendESP8266Command("AT+CWMODE=1");
        mode_ok = readESP8266Response(2000);
        if (!mode_ok)
        {
            ThisThread::sleep_for(1000ms);
        }
        retries--;
    }

    if (!mode_ok)
    {
        printf("Failed to set WiFi mode after multiple attempts\n");
        return false;
    }

    // Connect to WiFi
    printf("Connecting to WiFi...\n");
    lcd.cls();
    lcd.locate(0, 0);
    lcd.printf("Connecting to WiFi");
    lcd.locate(0, 1);
    lcd.printf("Please wait...");

    // Try to connect to WiFi (credentials hardcoded)
    sendESP8266Command("AT+CWJAP=\"arvin armand\",\"tehran77\"");

    // Read response with longer timeout for WiFi connection
    bool connection_ok = readESP8266Response(20000, "WIFI GOT IP");

    if (connection_ok)
    {
        printf("WiFi connected successfully!\n");
        wifi_connected = true;

        // Get IP address
        sendESP8266Command("AT+CIFSR");

        // Read response and extract IP address
        char response[1024] = {0};
        int i = 0;
        Timer t;
        t.start();

        while (t.elapsed_time() < chrono::milliseconds(5000))
        {
            if (esp8266.readable())
            {
                if (i < 1023)
                {
                    esp8266.read(&response[i], 1);
                    printf("%c", response[i]);
                    i++;
                }
                else
                {
                    break;
                }
            }
        }
        response[i] = '\0';

        // Extract IP address (simple parsing)
        char *ip_start = strstr(response, "STAIP,\"");
        if (ip_start)
        {
            ip_start += 7; // Move past "STAIP,\""
            char *ip_end = strchr(ip_start, '\"');
            if (ip_end)
            {
                int ip_len = ip_end - ip_start;
                if (ip_len < 16)
                {
                    strncpy(ip_address, ip_start, ip_len);
                    ip_address[ip_len] = '\0';
                    printf("IP address: %s\n", ip_address);
                }
            }
        }

        lcd.cls();
        lcd.locate(0, 0);
        lcd.printf("WiFi Connected!");
        lcd.locate(0, 1);
        lcd.printf("IP: %s", ip_address);
        ThisThread::sleep_for(2000ms);

        return true;
    }
    else
    {
        printf("Failed to connect to WiFi\n");
        lcd.cls();
        lcd.locate(0, 0);
        lcd.printf("WiFi Connection");
        lcd.locate(0, 1);
        lcd.printf("Failed!");
        ThisThread::sleep_for(2000ms);

        return false;
    }
}

// Add this function to your code
void timeout_safe_esp8266_command(const char *cmd, int max_wait_ms = 5000)
{
    // Send the command
    sendESP8266Command(cmd);

    // Set up a timer for the timeout
    Timer t;
    t.start();

    // Wait for response but with strict timeout
    while (t.elapsed_time() < chrono::milliseconds(max_wait_ms))
    {
        // Toggle LED to show the program is still running
        led = !led;
        ThisThread::sleep_for(100ms);

        // Check if there's any response
        if (esp8266.readable())
        {
            char buffer[256] = {0};
            int i = 0;
            while (esp8266.readable() && i < 255)
            {
                esp8266.read(&buffer[i], 1);
                i++;
            }
            buffer[i] = '\0';

            printf("Response fragment: %s\n", buffer);
            break;
        }
    }

    // If we reach here, we either got a response or timed out
    printf("Command completed or timed out\n");
}

// Function to calculate CO2 category
int calculate_co2_category(float co2_ppm)
{
    if (co2_ppm < 600)
        return 0; // Good
    else if (co2_ppm < 800)
        return 1; // Moderate
    else
        return 2; // Poor
}

// Function to calculate PM2.5 category
int calculate_pm2_5_category(float pm2_5_value)
{
    if (pm2_5_value < 12)
        return 0; // Good
    else if (pm2_5_value < 35.4)
        return 1; // Moderate
    else
        return 2; // Poor
}

// Function to calculate PM10 category
int calculate_pm10_category(float pm10_value)
{
    if (pm10_value < 54)
        return 0; // Good
    else if (pm10_value < 154)
        return 1; // Moderate
    else
        return 2; // Poor
}

// Function to get current hour (simplified, returns fixed value)
int get_current_hour()
{
    return 12; // Default to noon
}

// Function to get day of week (simplified, returns fixed value)
int get_day_of_week()
{
    return 3; // Default to Wednesday
}

// Function to check if it's weekend (simplified, returns fixed value)
int is_weekend()
{
    return 0; // Default to weekday
}

// Function to send data to Air Quality API
bool send_air_quality_data()
{
    // Calculate categories
    int co2_category = calculate_co2_category(eco2);
    int pm2_5_category = calculate_pm2_5_category(pm2_5);
    int pm10_category = calculate_pm10_category(pm10);

    // Get time data
    int hour = get_current_hour();
    int day_of_week = get_day_of_week();
    int weekend = is_weekend();

    // Prepare the JSON payload
    char payload[512];
    snprintf(payload, sizeof(payload),
             "{\"device_id\":\"smartenv-monitor\",\"co2\":%.1f,\"pm2_5\":%.1f,\"pm10\":%.1f,"
             "\"temperature\":%.1f,\"humidity\":%.1f,\"co2_category\":%d,"
             "\"pm2_5_category\":%d,\"pm10_category\":%d,\"hour\":%d,"
             "\"day_of_week\":%d,\"is_weekend\":%d}",
             (float)eco2, (float)pm2_5, (float)pm10,
             (float)temp_x10 / 10.0, (float)humidity_x10 / 10.0,
             co2_category, pm2_5_category, pm10_category,
             hour, day_of_week, weekend);

    printf("Sending Air Quality data to API...\n");
    bool success = sendAPIRequest("/api/predict", payload);

    if (success)
    {
        printf("Air Quality API request successful\n");
        // Set default values since we can't parse JSON properly
        air_quality_unsafe = false;
        air_quality_probability = 0.5;
        strcpy(api_message, "Data sent successfully");
    }
    else
    {
        printf("Air Quality API request failed\n");
        air_quality_unsafe = false;
        air_quality_probability = 0.0;
    }

    return success;
}

// Function to send data to Fire Detection API - simplified
bool send_fire_detection_data()
{
    // Use particle counts as number concentration values
    uint16_t nc0_5 = particles_05um;
    uint16_t nc1_0 = particles_10um;
    uint16_t nc2_5 = particles_25um;

    // Raw gas values - if not available, use defaults or approximations
    uint16_t raw_h2 = 12000;      // Default value
    uint16_t raw_ethanol = 15000; // Default value

    // Prepare the JSON payload
    char payload[512];
    snprintf(payload, sizeof(payload),
             "{\"device_id\":\"smartenv-monitor\",\"temperature\":%.1f,\"humidity\":%.1f,"
             "\"tvoc\":%d,\"eco2\":%d,\"raw_h2\":%d,\"raw_ethanol\":%d,"
             "\"pressure\":%.1f,\"pm1_0\":%d,\"pm2_5\":%d,"
             "\"nc0_5\":%d,\"nc1_0\":%d,\"nc2_5\":%d}",
             (float)temp_x10 / 10.0, (float)humidity_x10 / 10.0,
             tvoc, eco2, raw_h2, raw_ethanol,
             (float)pressure_x10 / 10.0, pm1_0, pm2_5,
             nc0_5, nc1_0, nc2_5);

    printf("Sending Fire Detection data to API...\n");
    bool success = sendAPIRequest("/api/predict-fire", payload);

    if (success)
    {
        printf("Fire Detection API request successful\n");
        // Set default values since we can't parse JSON properly
        fire_detected = false;
        fire_probability = 0.3;
        strcpy(api_message, "Data sent successfully");
    }
    else
    {
        printf("Fire Detection API request failed\n");
        fire_detected = false;
        fire_probability = 0.0;
    }

    return success;
}

// Check WiFi connection status
bool checkWiFiStatus()
{
    printf("\nChecking WiFi status...\n");
    sendESP8266Command("AT+CWJAP?");
    bool connected = readESP8266Response(5000, "arvin armand");

    if (connected)
    {
        printf("WiFi is connected, IP: %s\n", ip_address);
    }
    else
    {
        printf("WiFi is disconnected\n");
    }

    return connected;
}

// Button press handler - triggers sensor reading
void on_button_press()
{
    buttonPressed = true;
}

// GENERIC I2C FUNCTIONS

// Function to write a register (generic)
bool writeRegister(int addr, uint8_t reg, uint8_t value)
{
    char data[2];
    data[0] = reg;
    data[1] = value;

    return (i2c.write(addr << 1, data, 2) == 0);
}

// Function to read a byte from a register (generic)
bool readRegister(int addr, uint8_t reg, uint8_t *value)
{
    char cmd = reg;
    char data = 0;

    int ret = i2c.write(addr << 1, &cmd, 1);
    if (ret != 0)
        return false;

    ret = i2c.read(addr << 1, &data, 1);
    if (ret != 0)
        return false;

    *value = (uint8_t)data;
    return true;
}

// Function to read 2 bytes from a register (generic)
bool readRegister16(int addr, uint8_t reg, uint16_t *value)
{
    char cmd = reg;
    char data[2] = {0};

    int ret = i2c.write(addr << 1, &cmd, 1);
    if (ret != 0)
        return false;

    ret = i2c.read(addr << 1, data, 2);
    if (ret != 0)
        return false;

    *value = (uint8_t)data[0] | ((uint8_t)data[1] << 8);
    return true;
}

// Function to read multiple registers (generic)
bool readRegisters(int addr, uint8_t start_reg, uint8_t *buffer, uint8_t len)
{
    char cmd = start_reg;

    int ret = i2c.write(addr << 1, &cmd, 1);
    if (ret != 0)
        return false;

    ret = i2c.read(addr << 1, (char *)buffer, len);
    if (ret != 0)
        return false;

    return true;
}

// BME680 FUNCTIONS

// Initialize BME680 sensor
bool initBME680()
{
    printf("Initializing BME680 sensor...\n");

    // Check device presence
    char cmd = 0;
    if (i2c.write(BME680_ADDR << 1, &cmd, 0) != 0)
    {
        printf("ERROR: No device at address 0x%02X\n", BME680_ADDR);
        return false;
    }

    // Verify chip ID
    uint8_t chip_id;
    if (!readRegister(BME680_ADDR, BME680_REG_CHIP_ID, &chip_id))
    {
        printf("Failed to read BME680 chip ID\n");
        return false;
    }

    printf("BME680 Chip ID: 0x%02X\n", chip_id);

    if (chip_id != 0x61)
    {
        printf("WARNING: Unexpected chip ID (expected 0x61 for BME680)\n");
    }
    else
    {
        printf("Confirmed BME680 sensor\n");
    }

    // Configure the sensor for weather monitoring

    // Set humidity oversampling to 1x
    if (!writeRegister(BME680_ADDR, BME680_REG_CTRL_HUM, 0x01))
    {
        printf("Failed to set humidity oversampling\n");
        return false;
    }

    // Set temperature and pressure oversampling to 1x and set to forced mode
    if (!writeRegister(BME680_ADDR, BME680_REG_CTRL_MEAS, 0x25))
    {
        printf("Failed to set measurement mode\n");
        return false;
    }

    printf("BME680 initialized successfully\n");
    return true;
}

// Read data from BME680 sensor
bool readBME680()
{
    // Trigger a measurement
    if (!writeRegister(BME680_ADDR, BME680_REG_CTRL_MEAS, 0x25))
    {
        printf("Failed to trigger BME680 measurement\n");
        return false;
    }

    // Wait for measurement to complete
    ThisThread::sleep_for(100ms);

    // Read temperature data (3 bytes)
    uint8_t temp_data[3] = {0};
    if (readRegisters(BME680_ADDR, BME680_REG_TEMP_MSB, temp_data, 3))
    {
        // Calculate temperature
        uint32_t temp_adc = ((uint32_t)temp_data[0] << 12) |
                            ((uint32_t)temp_data[1] << 4) |
                            ((uint32_t)temp_data[2] >> 4);

        // Convert to temperature value using fixed-point math (x10 for one decimal place)
        int32_t raw_temp_x10 = (temp_adc * 10) / 5120;
        temp_x10 = raw_temp_x10 + TEMP_CALIB_OFFSET;

        // Print both raw and calibrated values
        printf("Temperature: %d.%d C\n",
               temp_x10 / 10, temp_x10 % 10 >= 0 ? temp_x10 % 10 : -(temp_x10 % 10));
    }
    else
    {
        printf("Failed to read temperature\n");
        return false;
    }

    // Read pressure data (3 bytes)
    uint8_t press_data[3] = {0};
    if (readRegisters(BME680_ADDR, BME680_REG_PRESS_MSB, press_data, 3))
    {
        // Calculate pressure
        uint32_t press_adc = ((uint32_t)press_data[0] << 12) |
                             ((uint32_t)press_data[1] << 4) |
                             ((uint32_t)press_data[2] >> 4);

        // Convert to pressure value (simplified) using fixed-point math
        pressure_x10 = (press_adc * 10) / 16;
        printf("Pressure: %d.%d hPa\n",
               (int)(pressure_x10 / 10), (int)(pressure_x10 % 10));
    }
    else
    {
        printf("Failed to read pressure\n");
        return false;
    }

    // Read humidity data (2 bytes)
    uint8_t hum_data[2] = {0};
    if (readRegisters(BME680_ADDR, BME680_REG_HUM_MSB, hum_data, 2))
    {
        // Calculate humidity
        uint16_t hum_adc = ((uint16_t)hum_data[0] << 8) | hum_data[1];

        // Convert to humidity value (simplified) using fixed-point math
        humidity_x10 = (hum_adc * 10) / 1024;
        printf("Humidity: %d.%d %%\n",
               (int)(humidity_x10 / 10), (int)(humidity_x10 % 10));
    }
    else
    {
        printf("Failed to read humidity\n");
        return false;
    }

    return true;
}

// ENS160 FUNCTIONS

// Function to try reading from ENS160 with an address
bool tryENS160()
{
    printf("Checking ENS160 at address 0x%02X...\n", ENS160_ADDR);

    // Try to read Part ID (register 0x00)
    char cmd = ENS160_REG_PART_ID;
    char data[2] = {0};

    // First write the register address
    int ret = i2c.write(ENS160_ADDR << 1, &cmd, 1);
    if (ret != 0)
    {
        printf("  Failed to write register address: error %d\n", ret);
        return false;
    }

    // Then read the data
    ret = i2c.read(ENS160_ADDR << 1, data, 2);
    if (ret != 0)
    {
        printf("  Failed to read from device: error %d\n", ret);
        return false;
    }

    // Check the Part ID (should be 0x0160)
    uint16_t partID = (uint8_t)data[1] << 8 | (uint8_t)data[0];
    printf("  Read Part ID: 0x%04X\n", partID);

    if (partID == 0x0160)
    {
        printf("  Success! Found ENS160 sensor (Part ID: 0x0160)\n");
        return true;
    }
    else
    {
        printf("  Found device but Part ID doesn't match ENS160\n");
        return false;
    }
}

// Initialize ENS160 sensor
bool initENS160()
{
    printf("Initializing ENS160 sensor...\n");

    // First verify if ENS160 is present
    if (!tryENS160())
    {
        return false;
    }

    // Initialize the sensor - set to standard operation mode
    if (!writeRegister(ENS160_ADDR, ENS160_REG_OP_MODE, ENS160_OPMODE_STD))
    {
        printf("Failed to set operation mode\n");
        return false;
    }

    printf("ENS160 initialized in standard operation mode\n");
    printf("Waiting for sensor to warm up...\n");

    // Wait for sensor to stabilize
    ThisThread::sleep_for(2s);

    return true;
}

// Function to read ENS160 data
bool readENS160Data()
{
    uint8_t status;

    // Read status register
    if (!readRegister(ENS160_ADDR, ENS160_REG_STATUS, &status))
    {
        return false;
    }

    printf("ENS160 Status: 0x%02X\n", status);
    printf("  Data validity: %s\n", (status & 0x01) ? "Valid" : "Invalid");
    printf("  Data ready: %s\n", (status & 0x02) ? "Ready" : "Not ready");
    printf("  Error state: %s\n", (status & 0x04) ? "Error" : "No error");

    // Check if data is valid and ready
    if ((status & 0x03) != 0x03)
    {
        return false; // Data not valid or not ready
    }

    // Read AQI
    if (!readRegister(ENS160_ADDR, ENS160_REG_DATA_AQI, &aqi))
    {
        return false;
    }

    // Read TVOC
    if (!readRegister16(ENS160_ADDR, ENS160_REG_DATA_TVOC, &tvoc))
    {
        return false;
    }

    // Read eCO2
    if (!readRegister16(ENS160_ADDR, ENS160_REG_DATA_ECO2, &eco2))
    {
        return false;
    }

    printf("  Sensor data is valid and ready!\n");
    return true;
}

// Function to interpret AQI value
const char *getAQIDescription(uint8_t aqi)
{
    switch (aqi)
    {
    case 1:
        return "Excellent";
    case 2:
        return "Good";
    case 3:
        return "Moderate";
    case 4:
        return "Poor";
    case 5:
        return "Unhealthy";
    default:
        return "Invalid";
    }
}

// PMS5003 FUNCTIONS

// Forward declarations
void clear_serial_buffer();
void wake_up_pms5003();
void set_pms5003_active_mode();
bool read_pms5003();

// Clear the serial buffer for PMS5003
void clear_serial_buffer()
{
    uint8_t temp;
    int flush_attempts = 5;
    while (flush_attempts--)
    {
        while (pms5003.readable())
        {
            pms5003.read(&temp, 1);
        }
        ThisThread::sleep_for(100ms);
    }
}

// Wake up the PMS5003 sensor
void wake_up_pms5003()
{
    uint8_t wake_command[] = {0x42, 0x4D, 0xE4, 0x00, 0x01, 0x01, 0x74};
    pms5003.write(wake_command, sizeof(wake_command));
    printf("Sent wake-up command to PMS5003\n");
    ThisThread::sleep_for(3000ms); // Reduced from 8000ms to avoid timeout
}

// Set PMS5003 to active mode
void set_pms5003_active_mode()
{
    uint8_t set_active_mode[] = {0x42, 0x4D, 0xE1, 0x00, 0x01, 0x01, 0x71};
    pms5003.write(set_active_mode, sizeof(set_active_mode));
    printf("Sent active mode command to PMS5003\n");
    ThisThread::sleep_for(2000ms); // Reduced from 4000ms to avoid timeout
}

// Initialize PMS5003 sensor
bool initPMS5003()
{
    printf("Initializing PMS5003 sensor...\n");

    // Wake up and set to active mode
    wake_up_pms5003();
    set_pms5003_active_mode();

    printf("PMS5003 initialized successfully\n");
    return true;
}

// Read data from PMS5003
bool read_pms5003()
{
    uint8_t buffer[32] = {0};
    uint16_t checksum = 0;

    printf("\nAttempting to read PMS5003 data...\n");

    // Clear the buffer first
    clear_serial_buffer();
    ThisThread::sleep_for(300ms);

    int timeout = 3000; // Longer timeout for initial read
    bool start_found = false;

    // Try to find the start sequence with more time
    while (timeout > 0 && !start_found)
    {
        if (pms5003.readable())
        {
            pms5003.read(&buffer[0], 1);
            if (buffer[0] == 0x42)
            {
                // First byte matches, now check second byte
                int wait_time = 0;
                while (!pms5003.readable() && wait_time < 100)
                {
                    ThisThread::sleep_for(5ms);
                    wait_time += 5;
                }

                if (pms5003.readable())
                {
                    pms5003.read(&buffer[1], 1);
                    if (buffer[1] == 0x4D)
                    {
                        start_found = true;
                        break;
                    }
                }
            }
        }
        ThisThread::sleep_for(10ms);
        timeout -= 10;
    }

    if (!start_found)
    {
        printf("Error: No valid start bytes received (0x42, 0x4D)\n");
        return false;
    }

    printf("Start bytes found (0x42, 0x4D), reading data...\n");

    // Read remaining data with timeout
    bool read_complete = true;
    for (int i = 2; i < 32; i++)
    {
        timeout = 500;
        bool byte_read = false;

        while (timeout > 0 && !byte_read)
        {
            if (pms5003.readable())
            {
                pms5003.read(&buffer[i], 1);
                byte_read = true;
            }
            else
            {
                ThisThread::sleep_for(5ms);
                timeout -= 5;
            }
        }

        if (!byte_read)
        {
            printf("Error: Timeout reading byte %d\n", i);
            read_complete = false;
            break;
        }
    }

    if (!read_complete)
    {
        return false;
    }

    // Calculate checksum
    for (int i = 0; i < 30; i++)
    {
        checksum += buffer[i];
    }
    uint16_t received_checksum = (buffer[30] << 8) | buffer[31];

    if (checksum != received_checksum)
    {
        printf("Checksum error! Calculated: 0x%04X, Received: 0x%04X\n", checksum, received_checksum);
        return false;
    }

    // Extract data
    pm1_0 = (buffer[4] << 8) | buffer[5];
    pm2_5 = (buffer[6] << 8) | buffer[7];
    pm10 = (buffer[8] << 8) | buffer[9];

    particles_03um = (buffer[16] << 8) | buffer[17];
    particles_05um = (buffer[18] << 8) | buffer[19];
    particles_10um = (buffer[20] << 8) | buffer[21];
    particles_25um = (buffer[22] << 8) | buffer[23];
    particles_50um = (buffer[24] << 8) | buffer[25];
    particles_100um = (buffer[26] << 8) | buffer[27];

    reading_counter++;

    printf("\nPMS5003 Particle Sensor Reading #%d:\n", reading_counter);
    printf("PM1.0: %u µg/m³\n", pm1_0);
    printf("PM2.5: %u µg/m³\n", pm2_5);
    printf("PM10: %u µg/m³\n", pm10);
    printf("Particles >0.3µm: %u per 0.1L air\n", particles_03um);
    printf("Particles >0.5µm: %u per 0.1L air\n", particles_05um);
    printf("Particles >1.0µm: %u per 0.1L air\n", particles_10um);
    printf("Particles >2.5µm: %u per 0.1L air\n", particles_25um);
    printf("Particles >5.0µm: %u per 0.1L air\n", particles_50um);
    printf("Particles >10µm: %u per 0.1L air\n", particles_100um);

    return true;
}

// Function to read all sensors
void readAllSensors()
{
    printf("\n=== Reading All Sensors ===\n");

    // Start by reading BME680
    printf("\n--- Reading BME680 ---\n");
    if (!readBME680())
    {
        printf("Failed to read from BME680\n");
    }

    // Read ENS160 if available
    if (ens160_ok)
    {
        printf("\n--- Reading ENS160 ---\n");
        if (readENS160Data())
        {
            printf("\nAir Quality Measurements:\n");
            printf("----------------------\n");
            printf("Air Quality Index: %d (%s)\n", aqi, getAQIDescription(aqi));
            printf("TVOC: %d ppb\n", tvoc);
            printf("eCO2: %d ppm\n", eco2);
            printf("----------------------\n");
        }
        else
        {
            printf("Failed to read valid data from ENS160\n");
        }
    }

    // Read PMS5003 if available
    if (pms5003_ok)
    {
        printf("\n--- Reading PMS5003 ---\n");
        if (!read_pms5003())
        {
            printf("Failed to read from PMS5003\n");
        }
    }

    // Check WiFi status
    if (esp8266_ok)
    {
        printf("\n--- Checking WiFi Status ---\n");
        if (checkWiFiStatus())
        {
            printf("WiFi Connected: %s\n", ip_address);
            wifi_connected = true;
        }
        else
        {
            printf("WiFi Disconnected\n");
            wifi_connected = false;
            strcpy(ip_address, "Not Connected");
        }
    }

    printf("\n=== Sensor Reading Complete ===\n");
}

// DISPLAY FUNCTIONS

// Update the LCD display based on the current mode
void updateDisplay()
{
    lcd.cls();

    // Display sensor readings based on current mode
    switch (displayMode)
    {
    case 0: // Environmental data (BME680 readings)
        lcd.locate(0, 0);
        lcd.printf("Environment Data");
        lcd.locate(0, 1);
        lcd.printf("Temp: %d.%d C",
                   temp_x10 / 10,
                   temp_x10 % 10 >= 0 ? temp_x10 % 10 : -(temp_x10 % 10));
        lcd.locate(0, 2);
        lcd.printf("Press: %d.%d hPa",
                   (int)(pressure_x10 / 10),
                   (int)(pressure_x10 % 10));
        lcd.locate(0, 3);
        lcd.printf("Humid: %d.%d %%",
                   (int)(humidity_x10 / 10),
                   (int)(humidity_x10 % 10));
        break;

    case 1: // Air Quality (ENS160 readings)
        lcd.locate(0, 0);
        lcd.printf("Air Quality Data");
        lcd.locate(0, 1);
        lcd.printf("AQI: %d (%s)", aqi, getAQIDescription(aqi));
        lcd.locate(0, 2);
        lcd.printf("TVOC: %d ppb", tvoc);
        lcd.locate(0, 3);
        lcd.printf("eCO2: %d ppm", eco2);
        break;

    case 2: // Combined view - key metrics
        lcd.locate(0, 0);
        lcd.printf("Combined View");
        lcd.locate(0, 1);
        lcd.printf("Temp: %d.%d C | AQI: %d",
                   temp_x10 / 10,
                   temp_x10 % 10 >= 0 ? temp_x10 % 10 : -(temp_x10 % 10),
                   aqi);
        lcd.locate(0, 2);
        lcd.printf("Humidity: %d.%d %%",
                   (int)(humidity_x10 / 10),
                   (int)(humidity_x10 % 10));
        lcd.locate(0, 3);
        lcd.printf("CO2: %d ppm", eco2);
        break;

    case 3: // Particle Sensor data (PMS5003)
        lcd.locate(0, 0);
        lcd.printf("Particle Data");
        lcd.locate(0, 1);
        lcd.printf("PM1.0: %d ug/m3", pm1_0);
        lcd.locate(0, 2);
        lcd.printf("PM2.5: %d ug/m3", pm2_5);
        lcd.locate(0, 3);
        lcd.printf("PM10:  %d ug/m3", pm10);
        break;

    case 4: // WiFi Status (new display mode)
        lcd.locate(0, 0);
        lcd.printf("WiFi Status");
        lcd.locate(0, 1);
        lcd.printf("Connected: %s", wifi_connected ? "Yes" : "No");
        if (wifi_connected)
        {
            // Split IP address display if needed
            if (strlen(ip_address) > 18)
            {
                // Show just first part if too long
                char short_ip[19] = {0};
                strncpy(short_ip, ip_address, 18);
                lcd.locate(0, 2);
                lcd.printf("IP: %s", short_ip);
            }
            else
            {
                lcd.locate(0, 2);
                lcd.printf("IP: %s", ip_address);
            }
        }
        else
        {
            lcd.locate(0, 2);
            lcd.printf("Not connected");
        }
        lcd.locate(0, 3);
        lcd.printf("SSID: arvin armand");
        break;

    case 5: // API Results (new display mode)
        lcd.locate(0, 0);
        lcd.printf("API Results");
        lcd.locate(0, 1);
        lcd.printf("AQ: %s (%.0f%%)",
                   air_quality_unsafe ? "UNSAFE" : "SAFE",
                   air_quality_probability * 100);
        lcd.locate(0, 2);
        lcd.printf("Fire: %s (%.0f%%)",
                   fire_detected ? "DETECTED" : "SAFE",
                   fire_probability * 100);
        lcd.locate(0, 3);
        lcd.printf("%.16s", api_message);
        break;
    }
}

// MAIN PROGRAM
int main()
{
    bool skip_esp8266 = true;
    // Start with slower LED blinks to show program starting
    for (int i = 0; i < 3; i++)
    {
        led = 1;
        ThisThread::sleep_for(200ms);
        led = 0;
        ThisThread::sleep_for(200ms);
    }

    printf("\nSmart Environmental Monitor with WiFi - Button Triggered\n");
    printf("=====================================================\n");

    // Set I2C frequency
    i2c.frequency(100000); // 100 kHz
    printf("I2C initialized at 100kHz\n\n");

    // Set up button interrupt
    button.rise(&on_button_press);

    // Wait for LCD to initialize
    ThisThread::sleep_for(500ms);

    // Initialize sensors
    bme680_ok = initBME680();
    if (!bme680_ok)
    {
        printf("Failed to initialize BME680 sensor. Check connections.\n");
        lcd.cls();
        lcd.locate(0, 0);
        lcd.printf("ERROR:");
        lcd.locate(0, 1);
        lcd.printf("BME680 sensor not");
        lcd.locate(0, 2);
        lcd.printf("detected.");

        // Blink LED rapidly to indicate failure
        while (true)
        {
            led = !led;
            ThisThread::sleep_for(100ms);
        }
    }

    // After BME680 is initialized, try ENS160
    printf("Attempting to initialize ENS160 sensor...\n");
    ens160_ok = initENS160();

    // Now initialize PMS5003
    printf("Attempting to initialize PMS5003 sensor...\n");
    pms5003_ok = initPMS5003();

    // Initialize ESP8266 and connect to WiFi
    if (!skip_esp8266)
    {
        // Initialize ESP8266 and connect to WiFi
        printf("Attempting to initialize ESP8266 and connect to WiFi...\n");
        esp8266_ok = initESP8266();
    }
    else
    {
        printf("Skipping ESP8266 initialization for debugging\n");
        esp8266_ok = false;
        wifi_connected = false;
    }

    // Print sensor status to console
    printf("Sensor Status:\n");
    printf("BME680: %s\n", bme680_ok ? "OK" : "FAIL");
    printf("ENS160: %s\n", ens160_ok ? "OK" : "FAIL");
    printf("PMS5003: %s\n", pms5003_ok ? "OK" : "FAIL");
    printf("ESP8266/WiFi: %s\n", esp8266_ok ? "OK" : "FAIL");

    // Show the default welcome screen
    lcd.cls();
    lcd.locate(0, 0);
    lcd.printf("Smart");
    lcd.locate(0, 1);
    lcd.printf("Environmental");
    lcd.locate(0, 2);
    lcd.printf("Monitor");
    lcd.locate(0, 3);
    if (esp8266_ok && wifi_connected)
    {
        lcd.printf("WiFi: Connected");
    }
    else
    {
        lcd.printf("Press the button");
    }

    printf("System ready. Press button to read all sensors.\n");

    // Initialize the timer
    sensorReadTimer.start();
    int64_t lastDisplayChange = 0;
    int64_t lastWiFiCheck = 0;
    bool dataCollected = false;
    bool inDisplayCycle = false;

    // Variables for averaging
    int32_t temp_sum = 0;
    int32_t pressure_sum = 0;
    int32_t humidity_sum = 0;
    uint32_t aqi_sum = 0;
    uint32_t tvoc_sum = 0;
    uint32_t eco2_sum = 0;
    uint32_t pm1_0_sum = 0;
    uint32_t pm2_5_sum = 0;
    uint32_t pm10_sum = 0;

    // Main loop
    while (true)
    {
        // Toggle LED to show the program is running
        led = !led;

        // Get current time in seconds
        int64_t currentTime = sensorReadTimer.elapsed_time().count() / 1000000;

        // Check WiFi status every 30 seconds if ESP8266 is available
        if (esp8266_ok && (currentTime - lastWiFiCheck >= 30))
        {
            printf("\nPeriodic WiFi status check...\n");
            if (checkWiFiStatus())
            {
                if (!wifi_connected)
                {
                    printf("WiFi reconnected\n");
                    wifi_connected = true;
                }
                else
                {
                    printf("WiFi connected\n");
                }
            }
            else
            {
                if (wifi_connected)
                {
                    printf("WiFi connection lost\n");
                    wifi_connected = false;
                    strcpy(ip_address, "Not Connected");
                }
                else
                {
                    printf("WiFi disconnected\n");
                }
            }
            lastWiFiCheck = currentTime;
        }

        // Check if button was pressed
        if (buttonPressed)
        {
            buttonPressed = false;

            // If we were in display cycle, go back to default screen
            if (inDisplayCycle)
            {
                inDisplayCycle = false;

                // Show "Press button" screen again
                lcd.cls();
                lcd.locate(0, 0);
                lcd.printf("Smart");
                lcd.locate(0, 1);
                lcd.printf("Environmental");
                lcd.locate(0, 2);
                lcd.printf("Monitor");
                lcd.locate(0, 3);
                if (esp8266_ok && wifi_connected)
                {
                    lcd.printf("WiFi: Connected");
                }
                else
                {
                    lcd.printf("Press the button");
                }

                printf("Returning to default screen.\n");
            }
            else
            {
                // Not in display cycle, collect new data

                // Show collecting message
                lcd.cls();
                lcd.locate(0, 0);
                lcd.printf("Collecting data...");

                // Reset sums for averaging
                temp_sum = 0;
                pressure_sum = 0;
                humidity_sum = 0;
                aqi_sum = 0;
                tvoc_sum = 0;
                eco2_sum = 0;
                pm1_0_sum = 0;
                pm2_5_sum = 0;
                pm10_sum = 0;

                // Take 4 readings, skip first, average last 3
                for (int reading = 0; reading < 4; reading++)
                {
                    lcd.locate(0, 1);
                    lcd.printf("Reading %d/4...", reading + 1);

                    // Read BME680
                    if (bme680_ok)
                    {
                        if (readBME680())
                        {
                            if (reading > 0)
                            { // Skip the first reading
                                temp_sum += temp_x10;
                                pressure_sum += pressure_x10;
                                humidity_sum += humidity_x10;
                            }
                        }
                    }

                    // Read ENS160
                    if (ens160_ok)
                    {
                        if (readENS160Data())
                        {
                            if (reading > 0)
                            { // Skip the first reading
                                aqi_sum += aqi;
                                tvoc_sum += tvoc;
                                eco2_sum += eco2;
                            }
                        }
                    }

                    // Read PMS5003
                    if (pms5003_ok)
                    {
                        if (read_pms5003())
                        {
                            if (reading > 0)
                            { // Skip the first reading
                                pm1_0_sum += pm1_0;
                                pm2_5_sum += pm2_5;
                                pm10_sum += pm10;
                            }
                        }
                    }

                    // Check WiFi status
                    if (reading == 3 && esp8266_ok)
                    {
                        if (checkWiFiStatus())
                        {
                            wifi_connected = true;
                        }
                        else
                        {
                            wifi_connected = false;
                            strcpy(ip_address, "Not Connected");
                        }
                    }

                    // Short delay between readings
                    ThisThread::sleep_for(500ms);
                }

                // Calculate averages (divide by 3 as we're using 3 readings)
                temp_x10 = temp_sum / 3;
                pressure_x10 = pressure_sum / 3;
                humidity_x10 = humidity_sum / 3;
                aqi = aqi_sum / 3;
                tvoc = tvoc_sum / 3;
                eco2 = eco2_sum / 3;
                pm1_0 = pm1_0_sum / 3;
                pm2_5 = pm2_5_sum / 3;
                pm10 = pm10_sum / 3;

                printf("Averaged data from 3 readings (skipped first reading).\n");

                // Send data to APIs if WiFi is connected
                if (wifi_connected && esp8266_ok)
                {
                    // Update message on LCD
                    lcd.locate(0, 2);
                    lcd.printf("Sending to API...");

                    // Send data to Air Quality API
                    bool aq_success = send_air_quality_data();
                    ThisThread::sleep_for(1000ms); // Wait between requests

                    // Send data to Fire Detection API
                    bool fire_success = send_fire_detection_data();

                    // Show result
                    lcd.locate(0, 3);
                    if (aq_success && fire_success)
                    {
                        lcd.printf("API calls successful");
                    }
                    else
                    {
                        lcd.printf("API error: %s", api_message);
                    }
                    ThisThread::sleep_for(1000ms);
                }
                else
                {
                    strcpy(api_message, "WiFi not connected");
                }

                // Mark that we have valid data now
                dataCollected = true;
                displayMode = 0;                                                      // Reset to first display mode
                lastDisplayChange = sensorReadTimer.elapsed_time().count() / 1000000; // Get current time in seconds
                inDisplayCycle = true;

                // Update display with collected data
                updateDisplay();

                printf("Data collected. Display will cycle through all modes.\n");
            }
        }

        // Only cycle display if we have collected data and are in display cycle mode
        if (dataCollected && inDisplayCycle)
        {
            // Get current time in seconds
            int64_t currentTime = sensorReadTimer.elapsed_time().count() / 1000000;

            // Check if it's time to switch display mode (every 5 seconds)
            if (currentTime - lastDisplayChange >= 5)
            {
                // Move to next display mode
                displayMode = (displayMode + 1) % numDisplayModes;
                lastDisplayChange = currentTime;

                // Update display with new mode
                updateDisplay();
                printf("Display mode changed to %d\n", displayMode + 1);
            }
        }

        // A short sleep to prevent excessive CPU usage
        ThisThread::sleep_for(100ms);
    }
}