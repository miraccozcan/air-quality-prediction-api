#include "mbed.h"
#include "LCDi2c.h"
#include <stdio.h>
#include <cstring>

namespace FireModelNamespace {
    #include "fire_model.h"
}
namespace ZoneModelNamespace {
    #include "zone_model.h"
}
using FireModel = FireModelNamespace::Eloquent::ML::Port::RandomForest;
using ZoneModel = ZoneModelNamespace::Eloquent::ML::Port::RandomForest;

I2C i2c(PTE25, PTE24);
LCDi2c lcd(PTE25, PTE24, LCD20x4, 0x27);
DigitalOut led(LED1);
DigitalOut buzzer(PTB9);
InterruptIn button(PTC3);
BufferedSerial pms5003(D1, D0, 9600);
BufferedSerial esp(PTD3, PTD2, 115200);

volatile bool buttonPressed = false;
bool systemStarted = false;
int displayMode = 0;
int numDisplayModes = 6;
Timer sensorReadTimer;
Timer buzzerTimer;
int buzzerPattern = 0;
int buzzerState = 0;
int64_t lastBuzzerUpdate = 0;

bool wifi_connected = false;
int64_t last_api_update = 0;
const int api_update_interval = 60;
bool api_air_success = false;
bool api_fire_success = false;

#define BME680_ADDR 0x76
#define ENS160_ADDR 0x53
#define BME680_REG_CHIP_ID   0xD0
#define BME680_REG_RESET     0xE0
#define BME680_REG_CTRL_HUM  0x72
#define BME680_REG_CTRL_MEAS 0x74
#define BME680_REG_CONFIG    0x75
#define BME680_REG_STATUS    0x73
#define BME680_REG_TEMP_MSB  0x22
#define BME680_REG_TEMP_LSB  0x23
#define BME680_REG_TEMP_XLSB 0x24
#define BME680_REG_PRESS_MSB 0x1F
#define BME680_REG_PRESS_LSB 0x20
#define BME680_REG_PRESS_XLSB 0x21
#define BME680_REG_HUM_MSB   0x25
#define BME680_REG_HUM_LSB   0x26
#define ENS160_REG_PART_ID     0x00
#define ENS160_REG_OP_MODE     0x10
#define ENS160_REG_STATUS      0x20
#define ENS160_REG_DATA_AQI    0x21
#define ENS160_REG_DATA_TVOC   0x22
#define ENS160_REG_DATA_ECO2   0x24
#define ENS160_REG_TEMP_IN     0x30
#define ENS160_REG_RH_IN       0x32
#define ENS160_OPMODE_IDLE     0x01
#define ENS160_OPMODE_STD      0x02
#define TEMP_CALIB_OFFSET -700

int32_t temp_x10 = 0;
int32_t pressure_x10 = 0;
int32_t humidity_x10 = 0;
uint8_t aqi = 1;
uint16_t tvoc = 0;
uint16_t eco2 = 400;
uint16_t pm1_0 = 0;
uint16_t pm2_5 = 0;
uint16_t pm10 = 0;
uint16_t particles_03um = 0;
uint16_t particles_05um = 0;
uint16_t particles_10um = 0;
uint16_t particles_25um = 0;
uint16_t particles_50um = 0;
uint16_t particles_100um = 0;
int reading_counter = 0;

bool bme680_ok = false;
bool ens160_ok = false;
bool pms5003_ok = false;

char fireStatus[20] = "";
char zoneStatus[20] = "";
int currentFirePrediction = 0;
int currentZonePrediction = 0;

char apiAirMessage[64] = "Not available";
char apiFireMessage[64] = "Not available";
float apiAirProbability = 0.0;
float apiFireProbability = 0.0;
bool apiAirIsUnsafe = false;
bool apiFireDetected = false;

void on_button_press() {
    if (!systemStarted) {
        buttonPressed = true;
    } else {
        displayMode = (displayMode + 1) % numDisplayModes;
    }
}

bool writeRegister(int addr, uint8_t reg, uint8_t value) {
    char data[2];
    data[0] = reg;
    data[1] = value;
    return (i2c.write(addr << 1, data, 2) == 0);
}
bool readRegister(int addr, uint8_t reg, uint8_t* value) {
    char cmd = reg;
    char data = 0;
    int ret = i2c.write(addr << 1, &cmd, 1);
    if (ret != 0) return false;
    ret = i2c.read(addr << 1, &data, 1);
    if (ret != 0) return false;
    *value = (uint8_t)data;
    return true;
}
bool readRegister16(int addr, uint8_t reg, uint16_t* value) {
    char cmd = reg;
    char data[2] = {0};
    int ret = i2c.write(addr << 1, &cmd, 1);
    if (ret != 0) return false;
    ret = i2c.read(addr << 1, data, 2);
    if (ret != 0) return false;
    *value = (uint8_t)data[0] | ((uint8_t)data[1] << 8);
    return true;
}
bool readRegisters(int addr, uint8_t start_reg, uint8_t* buffer, uint8_t len) {
    char cmd = start_reg;
    int ret = i2c.write(addr << 1, &cmd, 1);
    if (ret != 0) return false;
    ret = i2c.read(addr << 1, (char*)buffer, len);
    if (ret != 0) return false;
    return true;
}

bool initBME680() {
    char cmd = 0;
    if (i2c.write(BME680_ADDR << 1, &cmd, 0) != 0) return false;
    uint8_t chip_id;
    if (!readRegister(BME680_ADDR, BME680_REG_CHIP_ID, &chip_id)) return false;
    if (!writeRegister(BME680_ADDR, BME680_REG_CTRL_HUM, 0x01)) return false;
    if (!writeRegister(BME680_ADDR, BME680_REG_CTRL_MEAS, 0x25)) return false;
    return true;
}
bool readBME680() {
    if (!writeRegister(BME680_ADDR, BME680_REG_CTRL_MEAS, 0x25)) return false;
    ThisThread::sleep_for(100ms);
    uint8_t temp_data[3] = {0};
    if (readRegisters(BME680_ADDR, BME680_REG_TEMP_MSB, temp_data, 3)) {
        uint32_t temp_adc = ((uint32_t)temp_data[0] << 12) | ((uint32_t)temp_data[1] << 4) | ((uint32_t)temp_data[2] >> 4);
        int32_t raw_temp_x10 = (temp_adc * 10) / 5120;
        temp_x10 = raw_temp_x10 + TEMP_CALIB_OFFSET;
    } else {
        return false;
    }
    uint8_t press_data[3] = {0};
    if (readRegisters(BME680_ADDR, BME680_REG_PRESS_MSB, press_data, 3)) {
        uint32_t press_adc = ((uint32_t)press_data[0] << 12) | ((uint32_t)press_data[1] << 4) | ((uint32_t)press_data[2] >> 4);
        pressure_x10 = (press_adc * 10) / 16;
    } else {
        return false;
    }
    uint8_t hum_data[2] = {0};
    if (readRegisters(BME680_ADDR, BME680_REG_HUM_MSB, hum_data, 2)) {
        uint16_t hum_adc = ((uint16_t)hum_data[0] << 8) | hum_data[1];
        humidity_x10 = (hum_adc * 10) / 1024;
    } else {
        return false;
    }
    return true;
}
bool tryENS160() {
    char cmd = ENS160_REG_PART_ID;
    char data[2] = {0};
    int ret = i2c.write(ENS160_ADDR << 1, &cmd, 1);
    if (ret != 0) return false;
    ret = i2c.read(ENS160_ADDR << 1, data, 2);
    if (ret != 0) return false;
    uint16_t partID = (uint8_t)data[1] << 8 | (uint8_t)data[0];
    return (partID == 0x0160);
}
bool initENS160() {
    if (!tryENS160()) return false;
    if (!writeRegister(ENS160_ADDR, ENS160_REG_OP_MODE, ENS160_OPMODE_STD)) return false;
    ThisThread::sleep_for(2000ms);
    return true;
}
bool readENS160Data() {
    uint8_t status;
    if (!readRegister(ENS160_ADDR, ENS160_REG_STATUS, &status)) return false;
    if ((status & 0x03) != 0x03) return false;
    if (!readRegister(ENS160_ADDR, ENS160_REG_DATA_AQI, &aqi)) return false;
    if (!readRegister16(ENS160_ADDR, ENS160_REG_DATA_TVOC, &tvoc)) return false;
    if (!readRegister16(ENS160_ADDR, ENS160_REG_DATA_ECO2, &eco2)) return false;
    return true;
}
const char* getAQIDescription(uint8_t aqi) {
    switch(aqi) {
        case 1: return "Excellent";
        case 2: return "Good";
        case 3: return "Moderate";
        case 4: return "Poor";
        case 5: return "Unhealthy";
        default: return "Invalid";
    }
}
void clear_serial_buffer() {
    uint8_t temp;
    int flush_attempts = 5;
    while (flush_attempts--) {
        while (pms5003.readable()) {
            pms5003.read(&temp, 1);
        }
        ThisThread::sleep_for(100ms);
    }
}
void wake_up_pms5003() {
    uint8_t wake_command[] = {0x42, 0x4D, 0xE4, 0x00, 0x01, 0x01, 0x74};
    pms5003.write(wake_command, sizeof(wake_command));
    ThisThread::sleep_for(3000ms);
}
void set_pms5003_active_mode() {
    uint8_t set_active_mode[] = {0x42, 0x4D, 0xE1, 0x00, 0x01, 0x01, 0x71};
    pms5003.write(set_active_mode, sizeof(set_active_mode));
    ThisThread::sleep_for(2000ms);
}
bool initPMS5003() {
    wake_up_pms5003();
    set_pms5003_active_mode();
    return true;
}
bool read_pms5003() {
    uint8_t buffer[32] = {0};
    uint16_t checksum = 0;
    clear_serial_buffer();
    ThisThread::sleep_for(300ms);
    int timeout = 3000;
    bool start_found = false;
    while (timeout > 0 && !start_found) {
        if (pms5003.readable()) {
            pms5003.read(&buffer[0], 1);
            if (buffer[0] == 0x42) {
                int wait_time = 0;
                while (!pms5003.readable() && wait_time < 100) {
                    ThisThread::sleep_for(5ms);
                    wait_time += 5;
                }
                if (pms5003.readable()) {
                    pms5003.read(&buffer[1], 1);
                    if (buffer[1] == 0x4D) {
                        start_found = true;
                        break;
                    }
                }
            }
        }
        ThisThread::sleep_for(10ms);
        timeout -= 10;
    }
    if (!start_found) return false;
    bool read_complete = true;
    for (int i = 2; i < 32; i++) {
        timeout = 500;
        bool byte_read = false;
        while (timeout > 0 && !byte_read) {
            if (pms5003.readable()) {
                pms5003.read(&buffer[i], 1);
                byte_read = true;
            } else {
                ThisThread::sleep_for(5ms);
                timeout -= 5;
            }
        }
        if (!byte_read) {
            read_complete = false;
            break;
        }
    }
    if (!read_complete) return false;
    for (int i = 0; i < 30; i++) {
        checksum += buffer[i];
    }
    uint16_t received_checksum = (buffer[30] << 8) | buffer[31];
    if (checksum != received_checksum) return false;
    pm1_0 = (buffer[4] << 8) | buffer[5];
    pm2_5 = (buffer[6] << 8) | buffer[7];
    pm10  = (buffer[8] << 8) | buffer[9];
    particles_03um = (buffer[16] << 8) | buffer[17];
    particles_05um = (buffer[18] << 8) | buffer[19];
    particles_10um = (buffer[20] << 8) | buffer[21];
    particles_25um = (buffer[22] << 8) | buffer[23];
    particles_50um = (buffer[24] << 8) | buffer[25];
    particles_100um = (buffer[26] << 8) | buffer[27];
    reading_counter++;
    return true;
}
void makePredictions() {
    float sensorInput[6] = {
        ((float)temp_x10)/10.0f, 
        ((float)humidity_x10)/10.0f, 
        (float)tvoc, 
        (float)eco2, 
        (float)pm2_5, 
        (float)pm10
    };
    FireModel localFireModel;
    ZoneModel localZoneModel;
    int firePrediction = localFireModel.predict(sensorInput);
    int zonePrediction = localZoneModel.predict(sensorInput);
    currentFirePrediction = firePrediction;
    currentZonePrediction = zonePrediction;
    switch(firePrediction) {
        case 0: strcpy(fireStatus, "No fire"); break;
        case 1: strcpy(fireStatus, "Possible"); break;
        case 2: strcpy(fireStatus, "Fire!"); break;
        default: strcpy(fireStatus, "Unknown"); break;
    }
    switch(zonePrediction) {
        case 0: strcpy(zoneStatus, "Safe"); break;
        case 1: strcpy(zoneStatus, "Warning"); break;
        case 2: strcpy(zoneStatus, "Hazardous"); break;
        default: strcpy(zoneStatus, "Unknown"); break;
    }
    if (firePrediction >= 1 || zonePrediction >= 2) {
        buzzerPattern = 2;
    } else if (firePrediction == 0 && zonePrediction == 1) {
        buzzerPattern = 1;
    } else {
        buzzerPattern = 0;
    }
    printf("Fire prediction: %d (%s)\n", firePrediction, fireStatus);
    printf("Zone prediction: %d (%s)\n", zonePrediction, zoneStatus);
    printf("Buzzer pattern: %d\n", buzzerPattern);
}
void updateBuzzer() {
    int64_t currentTime = buzzerTimer.elapsed_time().count() / 1000;
    if (buzzerPattern == 0) {
        buzzer = 0;
        return;
    }
    if (buzzerPattern == 1) {
        if (currentTime - lastBuzzerUpdate >= (buzzerState ? 500 : 1500)) {
            buzzerState = !buzzerState;
            buzzer = buzzerState;
            lastBuzzerUpdate = currentTime;
        }
    } else if (buzzerPattern == 2) {
        if (currentTime - lastBuzzerUpdate >= 200) {
            buzzerState = !buzzerState;
            buzzer = buzzerState;
            lastBuzzerUpdate = currentTime;
        }
    }
}
void readAllSensors() {
    if (bme680_ok) readBME680();
    if (ens160_ok) readENS160Data();
    if (pms5003_ok) read_pms5003();
}
void send_esp(const char* cmd) {
    esp.write(cmd, strlen(cmd));
    esp.write("\r\n", 2);
    ThisThread::sleep_for(300ms);
}
bool read_esp(int timeout = 3000, const char* success_text = "OK") {
    Timer t;
    t.start();
    char c;
    char buffer[512] = {0};
    int pos = 0;
    while (t.elapsed_time() < chrono::milliseconds(timeout)) {
        if (esp.readable()) {
            esp.read(&c, 1);
            if (pos < 511) {
                buffer[pos++] = c;
            }
        }
    }
    buffer[pos] = '\0';
    printf("ESP response: %.100s...\n", buffer);
    return (strstr(buffer, success_text) != NULL);
}
bool init_wifi(const char* ssid, const char* password) {
    printf("Initializing WiFi...\n");
    send_esp("AT+RST");
    ThisThread::sleep_for(2000ms);
    read_esp(5000);
    send_esp("AT");
    if (!read_esp(2000, "OK")) {
        printf("ESP8266 not responding\n");
        return false;
    }
    send_esp("AT+CWMODE=1");
    if (!read_esp()) {
        printf("Failed to set mode\n");
        return false;
    }
    char cmd[128];
    sprintf(cmd, "AT+CWJAP=\"%s\",\"%s\"", ssid, password);
    send_esp(cmd);
    if (!read_esp(15000, "WIFI GOT IP")) {
        printf("Failed to connect to WiFi\n");
        return false;
    }
    printf("WiFi connected successfully\n");
    return true;
}
void check_wifi_connection() {
    send_esp("AT");
    if (!read_esp(2000, "OK")) {
        send_esp("AT+CIPCLOSE");
        ThisThread::sleep_for(1000ms);
        send_esp("AT");
        wifi_connected = read_esp(2000, "OK");
    } else {
        wifi_connected = true;
    }
}
bool sendPost(const char* host, const char* path, const char* body) {
    char cmd[128];
    sprintf(cmd, "AT+CIPSTART=\"TCP\",\"%s\",80", host);
    send_esp(cmd);
    read_esp(5000, "CONNECT");
    char req[1024];
    sprintf(req,
        "POST %s HTTP/1.1\r\n"
        "Host: %s\r\n"
        "Content-Type: application/json\r\n"
        "Content-Length: %d\r\n\r\n"
        "%s", path, host, strlen(body), body);
    sprintf(cmd, "AT+CIPSEND=%d", strlen(req));
    send_esp(cmd);
    read_esp(3000, ">");
    esp.write(req, strlen(req));
    printf("Sent POST to %s%s\n", host, path);
    read_esp(10000);
    send_esp("AT+CIPCLOSE");
    read_esp(3000, "OK");
    return true;
}
bool send_air_quality_data() {
    if (!wifi_connected) return false;
    char body[512];
    snprintf(body, sizeof(body), 
        "{\"device_id\":\"k64f-monitor\","
        "\"co2\":%d,"
        "\"pm2_5\":%d,"
        "\"pm10\":%d,"
        "\"temperature\":%.1f,"
        "\"humidity\":%.1f,"
        "\"co2_category\":%d,"
        "\"pm2_5_category\":%d,"
        "\"pm10_category\":%d,"
        "\"hour\":%d,"
        "\"day_of_week\":%d,"
        "\"is_weekend\":%d}",
        eco2,
        pm2_5,
        pm10,
        (float)temp_x10 / 10.0f,
        (float)humidity_x10 / 10.0f,
        (eco2 > 1000) ? 2 : ((eco2 > 800) ? 1 : 0),
        (pm2_5 > 25) ? 2 : ((pm2_5 > 12) ? 1 : 0),
        (pm10 > 50) ? 2 : ((pm10 > 25) ? 1 : 0),
        12,
        3,
        0
    );
    printf("Sending Air Quality API data: %s\n", body);
    return sendPost("embedapi.botechgida.com", "/api/predict", body);
}
bool send_fire_detection_data() {
    if (!wifi_connected) return false;
    char body[512];
    snprintf(body, sizeof(body), 
        "{\"device_id\":\"k64f-monitor\","
        "\"temperature\":%.1f,"
        "\"humidity\":%.1f,"
        "\"tvoc\":%d,"
        "\"eco2\":%d,"
        "\"raw_h2\":150,"
        "\"raw_ethanol\":90,"
        "\"pressure\":%.1f,"
        "\"pm1_0\":%d,"
        "\"pm2_5\":%d,"
        "\"nc0_5\":%d,"
        "\"nc1_0\":%d,"
        "\"nc2_5\":%d}",
        (float)temp_x10 / 10.0f,
        (float)humidity_x10 / 10.0f,
        tvoc,
        eco2,
        (float)pressure_x10 / 10.0f,
        pm1_0,
        pm2_5,
        particles_03um,
        particles_10um,
        particles_25um
    );
    printf("Sending Fire API data: %s\n", body);
    return sendPost("embedapi.botechgida.com", "/api/predict-fire", body);
}
void updateDisplay() {
    lcd.cls();
    switch (displayMode) {
        case 0:
            lcd.locate(0, 0);
            lcd.printf("Environment Data");
            lcd.locate(0, 1);
            lcd.printf("Temp: %d.%d C", temp_x10 / 10, temp_x10 % 10 >= 0 ? temp_x10 % 10 : -(temp_x10 % 10));
            lcd.locate(0, 2);
            lcd.printf("Press: %d.%d hPa", (int)(pressure_x10 / 10), (int)(pressure_x10 % 10));
            lcd.locate(0, 3);
            lcd.printf("Humid: %d.%d %%", (int)(humidity_x10 / 10), (int)(humidity_x10 % 10));
            break;
        case 1:
            lcd.locate(0, 0);
            lcd.printf("Air Quality Data");
            lcd.locate(0, 1);
            lcd.printf("AQI: %d (%s)", aqi, getAQIDescription(aqi));
            lcd.locate(0, 2);
            lcd.printf("TVOC: %d ppb", tvoc);
            lcd.locate(0, 3);
            lcd.printf("eCO2: %d ppm", eco2);
            break;
        case 2:
            lcd.locate(0, 0);
            lcd.printf("Combined View");
            lcd.locate(0, 1);
            lcd.printf("Temp: %d.%d C | AQI: %d", temp_x10 / 10, temp_x10 % 10 >= 0 ? temp_x10 % 10 : -(temp_x10 % 10), aqi);
            lcd.locate(0, 2);
            lcd.printf("Humid: %d.%d %%", (int)(humidity_x10 / 10), (int)(humidity_x10 % 10));
            lcd.locate(0, 3);
            lcd.printf("CO2: %d ppm", eco2);
            break;
        case 3:
            lcd.locate(0, 0);
            lcd.printf("P>0.3:%d P>0.5:%d", particles_03um, particles_05um);
            lcd.locate(0, 1);
            lcd.printf("P>1.0:%d P>2.5:%d", particles_10um, particles_25um);
            lcd.locate(0, 2);
            lcd.printf("P>5.0:%d P>10:%d", particles_50um, particles_100um);
            lcd.locate(0, 3);
            lcd.printf("Press btn to change");
            break;
        case 4:
            lcd.locate(0, 0);
            lcd.printf("Safety Status");
            lcd.locate(0, 1);
            if (currentFirePrediction >= 1) {
                lcd.printf("Fire: !%s!", fireStatus);
            } else {
                lcd.printf("Fire: %s", fireStatus);
            }
            lcd.locate(0, 2);
            if (currentZonePrediction >= 1) {
                lcd.printf("Zone: !%s!", zoneStatus);
            } else {
                lcd.printf("Zone: %s", zoneStatus);
            }
            lcd.locate(0, 3);
            if (buzzerPattern > 0) {
                lcd.printf("ALERT ACTIVE");
            } else {
                lcd.printf("All conditions normal");
            }
            break;
        case 5:
            lcd.locate(0, 0);
            lcd.printf("Cloud Status");
            lcd.locate(0, 1);
            lcd.printf("WiFi: %s", wifi_connected ? "Connected" : "OFFLINE");
            lcd.locate(0, 2);
            lcd.printf("AQ: %s", api_air_success ? (apiAirIsUnsafe ? "UNSAFE" : "Safe") : "N/A");
            lcd.locate(0, 3);
            lcd.printf("Fire: %s", api_fire_success ? (apiFireDetected ? "DETECTED" : "Clear") : "N/A");
            break;
    }
}
int main() {
    buzzer = 0;
    for (int i = 0; i < 3; i++) {
        led = 1;
        ThisThread::sleep_for(200ms);
        led = 0;
        ThisThread::sleep_for(200ms);
    }
    printf("\nSmart Environmental Monitor with Cloud Connection\n");
    i2c.frequency(100000);
    button.rise(&on_button_press);
    ThisThread::sleep_for(500ms);
    buzzerTimer.start();
    bme680_ok = initBME680();
    if (!bme680_ok) {
        lcd.cls();
        lcd.locate(0, 0);
        lcd.printf("ERROR:");
        lcd.locate(0, 1);
        lcd.printf("BME680 not found");
        while (true) { led = !led; ThisThread::sleep_for(100ms); }
    }
    ens160_ok = initENS160();
    pms5003_ok = initPMS5003();
    printf("BME680: %s\n", bme680_ok ? "OK" : "FAIL");
    printf("ENS160: %s\n", ens160_ok ? "OK" : "FAIL");
    printf("PMS5003: %s\n", pms5003_ok ? "OK" : "FAIL");
    wifi_connected = init_wifi("arvin armand", "tehran77");
    printf("WiFi status: %s\n", wifi_connected ? "Connected" : "Offline");
    lcd.cls();
    lcd.locate(0, 0);
    lcd.printf("Smart");
    lcd.locate(0, 1);
    lcd.printf("Environmental");
    lcd.locate(0, 2);
    lcd.printf("Monitor");
    lcd.locate(0, 3);
    lcd.printf("Press btn to start");
    sensorReadTimer.start();
    int64_t lastDisplayChange = 0;
    int64_t lastSensorUpdate = 0;
    last_api_update = 0;
    int32_t temp_sum = 0;
    int32_t pressure_sum = 0;
    int32_t humidity_sum = 0;
    uint32_t aqi_sum = 0;
    uint32_t tvoc_sum = 0;
    uint32_t eco2_sum = 0;
    uint32_t pm1_0_sum = 0;
    uint32_t pm2_5_sum = 0;
    uint32_t pm10_sum = 0;
    while (true) {
        led = !led;
        if (!systemStarted && buttonPressed) {
            buttonPressed = false;
            systemStarted = true;
            lcd.cls();
            lcd.locate(0, 0);
            lcd.printf("Collecting data...");
            temp_sum = pressure_sum = humidity_sum = 0;
            aqi_sum = tvoc_sum = eco2_sum = 0;
            pm1_0_sum = pm2_5_sum = pm10_sum = 0;
            for (int reading = 0; reading < 4; reading++) {
                lcd.locate(0, 1);
                lcd.printf("Reading %d/4...", reading + 1);
                if (bme680_ok && readBME680()) {
                    if (reading > 0) {
                        temp_sum += temp_x10;
                        pressure_sum += pressure_x10;
                        humidity_sum += humidity_x10;
                    }
                }
                if (ens160_ok && readENS160Data()) {
                    if (reading > 0) {
                        aqi_sum += aqi;
                        tvoc_sum += tvoc;
                        eco2_sum += eco2;
                    }
                }
                if (pms5003_ok && read_pms5003()) {
                    if (reading > 0) {
                        pm1_0_sum += pm1_0;
                        pm2_5_sum += pm2_5;
                        pm10_sum += pm10;
                    }
                }
                ThisThread::sleep_for(4000ms);
            }
            temp_x10 = temp_sum / 3;
            pressure_x10 = pressure_sum / 3;
            humidity_x10 = humidity_sum / 3;
            aqi = aqi_sum / 3;
            tvoc = tvoc_sum / 3;
            eco2 = eco2_sum / 3;
            pm1_0 = pm1_0_sum / 3;
            pm2_5 = pm2_5_sum / 3;
            pm10 = pm10_sum / 3;
            printf("Averaged data from initial readings.\n");
            makePredictions();
            if (wifi_connected) {
                lcd.cls();
                lcd.locate(0, 0);
                lcd.printf("Sending to cloud");
                api_air_success = send_air_quality_data();
                ThisThread::sleep_for(3000ms);
                api_fire_success = send_fire_detection_data();
                lcd.locate(0, 2);
                lcd.printf("Air API: %s", api_air_success ? "OK" : "Failed");
                lcd.locate(0, 3);
                lcd.printf("Fire API: %s", api_fire_success ? "OK" : "Failed");
                ThisThread::sleep_for(2000ms);
            }
            lastSensorUpdate = sensorReadTimer.elapsed_time().count() / 1000000;
            lastDisplayChange = lastSensorUpdate;
            last_api_update = lastSensorUpdate;
            lastBuzzerUpdate = buzzerTimer.elapsed_time().count() / 1000;
            updateDisplay();
            printf("Data collected. Display cycling started.\n");
        }
        if (systemStarted) {
            int64_t currentTime = sensorReadTimer.elapsed_time().count() / 1000000;
            if (currentTime - lastSensorUpdate >= 30) {
                readAllSensors();
                makePredictions();
                if (currentTime - last_api_update >= api_update_interval) {
                    check_wifi_connection();
                    if (wifi_connected) {
                        api_air_success = send_air_quality_data();
                        ThisThread::sleep_for(3000ms);
                        api_fire_success = send_fire_detection_data();
                        printf("API update: Air %s, Fire %s\n", api_air_success ? "OK" : "Failed", api_fire_success ? "OK" : "Failed");
                    } else {
                        api_air_success = false;
                        api_fire_success = false;
                        printf("API update skipped: WiFi offline\n");
                    }
                    last_api_update = currentTime;
                }
                lastSensorUpdate = currentTime;
                updateDisplay();
                printf("Auto-update complete.\n");
            }
            if (currentTime - lastDisplayChange >= 5) {
                displayMode = (displayMode + 1) % numDisplayModes;
                lastDisplayChange = currentTime;
                updateDisplay();
                printf("Display mode changed to %d\n", displayMode + 1);
            }
            updateBuzzer();
        }
        ThisThread::sleep_for(100ms);
    }
}