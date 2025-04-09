# Smart Environmental Monitoring System

A comprehensive IoT-based environmental monitoring solution that combines hardware sensors with cloud-based machine learning for accurate air quality and fire hazard detection.

## System Overview

This project consists of two main components:

1. **Hardware Component**: A Freedom K64F microcontroller-based environmental monitoring device with multiple sensors
2. **Cloud Component**: A RESTful API that serves machine learning models for air quality and fire detection

The system is designed to collect environmental data (temperature, humidity, air quality, particle concentration) from various sensors, process that data locally, and then transmit it to the cloud for advanced analysis using machine learning models.

## Hardware Component

### Components Used

- **Microcontroller**: NXP Freedom K64F (ARM Cortex-M4F)
- **Display**: 20x4 Character LCD with I2C interface
- **Environmental Sensors**:
  - **BME680**: Temperature, humidity, and pressure sensor
  - **ENS160**: VOC, CO2 and air quality sensor
  - **PMS5003**: Particulate matter sensor
- **Connectivity**: ESP8266 WiFi module

### Sensor Features

#### BME680 Environmental Sensor
- Temperature measurement (°C)
- Relative humidity (%)
- Atmospheric pressure (hPa)

#### ENS160 Air Quality Sensor
- Air Quality Index (AQI) on a scale of 1-5
- Total Volatile Organic Compounds (TVOC) in ppb
- Equivalent CO2 (eCO2) in ppm

#### PMS5003 Particulate Matter Sensor
- PM1.0, PM2.5, and PM10 concentration (μg/m³)
- Particle count per 0.1L air for various particle sizes (>0.3μm, >0.5μm, >1.0μm, >2.5μm, >5.0μm, >10μm)

### Hardware Setup

1. Connect the BME680 sensor to the I2C bus (SDA: PTE25, SCL: PTE24)
2. Connect the ENS160 sensor to the same I2C bus
3. Connect the PMS5003 sensor to UART (TX: PTC17, RX: PTC16)
4. Connect the ESP8266 module to UART2 (TX: PTD3, RX: PTD2)
5. Connect the LCD display to the I2C bus
6. Connect a button to PTC3 for user interaction

### Firmware Features

- Multi-sensor data acquisition and processing
- Data averaging to improve accuracy
- Automatic sensor calibration
- WiFi connectivity for data transmission
- Multiple display modes with automatic cycling:
  - Environmental data (temperature, humidity, pressure)
  - Air quality data (AQI, TVOC, eCO2)
  - Combined view with key metrics
  - Particle data (PM1.0, PM2.5, PM10)
  - WiFi status information
  - API results (air quality and fire detection predictions)
- Button-triggered data collection
- Automatic API data transmission

## Cloud Component: Air Quality and Fire Detection API

The API leverages machine learning models to analyze sensor data and provide predictions about air quality conditions and potential fire hazards.

### API Base URL

```
http://embedapi.botechgida.com
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API status and information |
| `/api/predict` | POST | Air quality prediction |
| `/api/predict-fire` | POST | Fire detection prediction |
| `/api/data/air-quality` | GET | Retrieve air quality data |
| `/api/data/fire-detection` | GET | Retrieve fire detection data |
| `/docs` | GET | API documentation (Swagger UI) |

### Machine Learning Models

#### Air Quality Model
The air quality model is a RandomForest classifier trained on a dataset of air quality measurements. It predicts whether the air quality is safe or unsafe based on the input features.

**Input Features:**
- CO2 level (ppm)
- PM2.5 particulate matter (µg/m³)
- PM10 particulate matter (µg/m³)
- Temperature (°C)
- Humidity (%)
- CO2 category (0-2)
- PM2.5 category (0-2)
- PM10 category (0-2)
- Hour of day (0-23)
- Day of week (0-6)
- Is weekend (0-1)

**Output:**
- Binary classification (0 = safe, 1 = unsafe)
- Probability of unsafe condition

**Performance:**
- Model accuracy: 100% on test dataset

#### Fire Detection Model
The fire detection model is a RandomForest classifier trained on the smoke detection IoT dataset. It predicts whether there is a fire hazard based on environmental and air quality sensor readings.

**Input Features:**
- Temperature (°C)
- Humidity (%)
- TVOC (ppb)
- eCO2 (ppm)
- Raw H2 gas sensor reading
- Raw ethanol gas sensor reading
- Atmospheric pressure (hPa)
- PM1.0 particulate matter (µg/m³)
- PM2.5 particulate matter (µg/m³)
- Number concentration of particles > 0.5µm
- Number concentration of particles > 1.0µm
- Number concentration of particles > 2.5µm

**Output:**
- Binary classification (0 = no fire, 1 = fire detected)
- Probability of fire

**Performance:**
- Model accuracy: 100% on test dataset

### API Authentication

API access is currently open without authentication requirements.

## Integration Between Hardware and Cloud

### Data Flow

1. **Sensor Data Collection**: The K64F microcontroller collects data from BME680, ENS160, and PMS5003 sensors
2. **Local Processing**: Data is averaged and processed locally
3. **Data Transmission**: Processed data is sent to the cloud API via WiFi (ESP8266)
4. **Cloud Analysis**: Machine learning models analyze the data and provide predictions
5. **Display Results**: Predictions are displayed on the LCD screen

### Air Quality API Request Example

The microcontroller sends data in the following format:

```json
{
  "device_id": "smartenv-monitor",
  "co2": 450.0,
  "pm2_5": 10.0,
  "pm10": 22.0,
  "temperature": 17.0,
  "humidity": 62.5,
  "co2_category": 0,
  "pm2_5_category": 0,
  "pm10_category": 0,
  "hour": 14,
  "day_of_week": 3,
  "is_weekend": 0
}
```

### Fire Detection API Request Example

```json
{
  "device_id": "smartenv-monitor",
  "temperature": 25.0,
  "humidity": 50.0,
  "tvoc": 100.0,
  "eco2": 450.0,
  "raw_h2": 12000.0,
  "raw_ethanol": 15000.0,
  "pressure": 1013.0,
  "pm1_0": 5.0,
  "pm2_5": 8.0,
  "nc0_5": 100.0,
  "nc1_0": 50.0,
  "nc2_5": 10.0
}
```

## Installation and Setup

### Hardware Setup

1. Clone the repository or download the source code
2. Build the project using Mbed CLI or Mbed Studio:
   ```
   mbed compile -m K64F -t GCC_ARM
   ```
3. Flash the compiled binary to the Freedom K64F board
4. Connect the sensors and ESP8266 module as specified in the Hardware Setup section

### API Setup (for self-hosting)

1. Clone the API repository
2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
   Required packages:
   ```
   uvicorn==0.23.2
   numpy==1.25.2
   pandas==2.1.0
   scikit-learn==1.3.0
   joblib==1.3.2
   pydantic==2.3.0
   python-multipart==0.0.6
   ```
3. Configure database connection in `config.py`
4. Run the server:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 80
   ```

## Database Schema

The system uses SQLite to store all predictions and sensor data.

### Air Quality Data Table

```sql
CREATE TABLE IF NOT EXISTS air_quality_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    device_id TEXT,
    co2 REAL,
    pm2_5 REAL,
    pm10 REAL,
    temperature REAL,
    humidity REAL,
    co2_category INTEGER,
    pm2_5_category INTEGER,
    pm10_category INTEGER,
    hour INTEGER,
    day_of_week INTEGER,
    is_weekend INTEGER,
    prediction INTEGER,
    probability REAL
);
```

### Fire Detection Data Table

```sql
CREATE TABLE IF NOT EXISTS fire_detection_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    device_id TEXT,
    temperature REAL,
    humidity REAL,
    tvoc REAL,
    eco2 REAL,
    raw_h2 REAL,
    raw_ethanol REAL,
    pressure REAL,
    pm1_0 REAL,
    pm2_5 REAL,
    nc0_5 REAL,
    nc1_0 REAL,
    nc2_5 REAL,
    prediction INTEGER,
    probability REAL
);
```

## User Guide

### Hardware Operation

1. **Initial Setup**:
   - Power on the device
   - The device will initialize sensors and attempt to connect to WiFi
   - The LCD will display the welcome screen

2. **Data Collection**:
   - Press the button to start data collection
   - The device will take multiple readings and average them
   - If WiFi is connected, data will be sent to the cloud API
   - The display will cycle through different data views

3. **Display Modes**:
   - The display will automatically cycle through different modes every 5 seconds
   - Press the button again to return to the welcome screen

### API Usage

#### Implementation Examples

##### Air Quality API Request (C++)

```cpp
bool sendAirQualityData(String deviceId, float co2, float pm2_5, float pm10, 
                       float temperature, float humidity, int co2_category, 
                       int pm2_5_category, int pm10_category) {
  
  WiFiClient client;
  HTTPClient http;
  
  // Configure HTTP client
  http.begin(client, "http://embedapi.botechgida.com/api/predict");
  http.addHeader("Content-Type", "application/json");
  
  // Create JSON payload
  StaticJsonDocument<256> doc;
  doc["device_id"] = deviceId;
  doc["co2"] = co2;
  doc["pm2_5"] = pm2_5;
  doc["pm10"] = pm10;
  doc["temperature"] = temperature;
  doc["humidity"] = humidity;
  doc["co2_category"] = co2_category;
  doc["pm2_5_category"] = pm2_5_category;
  doc["pm10_category"] = pm10_category;
  doc["hour"] = 12;  // Replace with actual hour
  doc["day_of_week"] = 3;  // Replace with actual day
  doc["is_weekend"] = 0;  // Replace with actual weekend status
  
  // Serialize JSON to string
  String jsonPayload;
  serializeJson(doc, jsonPayload);
  
  // Send POST request
  int httpResponseCode = http.POST(jsonPayload);
  
  // Process response
  if (httpResponseCode > 0) {
    String response = http.getString();
    
    // Parse response
    StaticJsonDocument<256> responseDoc;
    DeserializationError error = deserializeJson(responseDoc, response);
    
    if (!error) {
      bool isUnsafe = responseDoc["is_unsafe"];
      float probability = responseDoc["probability"];
      
      // Handle the result
      http.end();
      return true;
    }
  }
  
  http.end();
  return false;
}
```

##### Fire Detection API Request (C++)

```cpp
bool checkForFire(String deviceId, float temperature, float humidity, 
                 float tvoc, float eco2, float raw_h2, float raw_ethanol,
                 float pressure, float pm1_0, float pm2_5, float nc0_5,
                 float nc1_0, float nc2_5) {
  
  WiFiClient client;
  HTTPClient http;
  
  // Configure HTTP client
  http.begin(client, "http://embedapi.botechgida.com/api/predict-fire");
  http.addHeader("Content-Type", "application/json");
  
  // Create JSON payload
  StaticJsonDocument<384> doc;
  doc["device_id"] = deviceId;
  doc["temperature"] = temperature;
  doc["humidity"] = humidity;
  doc["tvoc"] = tvoc;
  doc["eco2"] = eco2;
  doc["raw_h2"] = raw_h2;
  doc["raw_ethanol"] = raw_ethanol;
  doc["pressure"] = pressure;
  doc["pm1_0"] = pm1_0;
  doc["pm2_5"] = pm2_5;
  doc["nc0_5"] = nc0_5;
  doc["nc1_0"] = nc1_0;
  doc["nc2_5"] = nc2_5;
  
  // Serialize JSON to string
  String jsonPayload;
  serializeJson(doc, jsonPayload);
  
  // Send POST request
  int httpResponseCode = http.POST(jsonPayload);
  
  // Process response
  if (httpResponseCode > 0) {
    String response = http.getString();
    
    // Parse response
    StaticJsonDocument<256> responseDoc;
    DeserializationError error = deserializeJson(responseDoc, response);
    
    if (!error) {
      bool isFireDetected = responseDoc["is_fire_detected"];
      float probability = responseDoc["probability"];
      
      // Return fire detection result
      http.end();
      return isFireDetected;
    }
  }
  
  http.end();
  return false;
}
```

#### Test Cases

##### Air Quality Test Cases

1. **Good Air Quality:**
   ```bash
   curl -X POST http://embedapi.botechgida.com/api/predict \
     -H "Content-Type: application/json" \
     -d '{"device_id": "test-device-a1", "co2": 400, "pm2_5": 8, "pm10": 15, "temperature": 21, "humidity": 45, "co2_category": 0, "pm2_5_category": 0, "pm10_category": 0, "hour": 10, "day_of_week": 3, "is_weekend": 0}'
   ```
   **Expected response:** `status: 0, is_unsafe: false`

2. **Moderate Air Quality:**
   ```bash
   curl -X POST http://embedapi.botechgida.com/api/predict \
     -H "Content-Type: application/json" \
     -d '{"device_id": "test-device-a2", "co2": 650, "pm2_5": 25, "pm10": 85, "temperature": 24, "humidity": 62, "co2_category": 1, "pm2_5_category": 1, "pm10_category": 1, "hour": 14, "day_of_week": 5, "is_weekend": 1}'
   ```
   **Expected response:** `status: 1, is_unsafe: true, probability: 0.84`

3. **Poor Air Quality:**
   ```bash
   curl -X POST http://embedapi.botechgida.com/api/predict \
     -H "Content-Type: application/json" \
     -d '{"device_id": "test-device-a3", "co2": 950, "pm2_5": 55, "pm10": 200, "temperature": 30, "humidity": 75, "co2_category": 2, "pm2_5_category": 2, "pm10_category": 2, "hour": 20, "day_of_week": 6, "is_weekend": 1}'
   ```
   **Expected response:** `status: 1, is_unsafe: true, probability: 0.98`

##### Fire Detection Test Cases

1. **Normal Conditions:**
   ```bash
   curl -X POST http://embedapi.botechgida.com/api/predict-fire \
     -H "Content-Type: application/json" \
     -d '{"device_id": "test-device-f1", "temperature": 22, "humidity": 60, "tvoc": 80, "eco2": 400, "raw_h2": 10000, "raw_ethanol": 12000, "pressure": 1015, "pm1_0": 3, "pm2_5": 5, "nc0_5": 50, "nc1_0": 25, "nc2_5": 5}'
   ```
   **Expected response:** `fire_alarm: 0, is_fire_detected: false`

2. **Elevated Readings:**
   ```bash
   curl -X POST http://embedapi.botechgida.com/api/predict-fire \
     -H "Content-Type: application/json" \
     -d '{"device_id": "test-device-f2", "temperature": 32, "humidity": 35, "tvoc": 350, "eco2": 750, "raw_h2": 18000, "raw_ethanol": 20000, "pressure": 1010, "pm1_0": 12, "pm2_5": 20, "nc0_5": 180, "nc1_0": 90, "nc2_5": 35}'
   ```
   **Expected response:** `fire_alarm: 1, is_fire_detected: true, probability: 0.64`

3. **Fire Condition Readings:**
   ```bash
   curl -X POST http://embedapi.botechgida.com/api/predict-fire \
     -H "Content-Type: application/json" \
     -d '{"device_id": "test-device-f3", "temperature": 55, "humidity": 18, "tvoc": 2000, "eco2": 3000, "raw_h2": 45000, "raw_ethanol": 55000, "pressure": 1005, "pm1_0": 85, "pm2_5": 140, "nc0_5": 1200, "nc1_0": 600, "nc2_5": 350}'
   ```
   **Expected response:** `fire_alarm: 1, is_fire_detected: true, probability: 0.67`

## Technical Details

### K64F Microcontroller Specifications
- ARM Cortex-M4 core at 120 MHz
- 1 MB flash, 256 KB RAM
- Multiple I2C, SPI, and UART interfaces
- Integrated sensors and peripherals

### WiFi Configuration
The device is configured to connect to the following WiFi network:
- SSID: "arvin armand"
- Password: "tehran77"

To change the WiFi settings, modify the `initESP8266()` function in the code.

### Error Handling
The system includes robust error handling for:
- Sensor initialization failures
- Sensor reading errors
- WiFi connection issues
- API communication problems

### Data Processing
- **Sensor Reading Frequency**: On demand (button press)
- **Averaging Method**: 4 readings taken, first reading discarded, average of 3 remaining readings
- **Calibration**: Temperature is calibrated with a -7.0°C offset for accuracy

## Troubleshooting

### Common Hardware Issues

1. **LCD not displaying**:
   - Check I2C connections
   - Verify correct I2C address (0x27)
   - Check power supply

2. **WiFi not connecting**:
   - Verify ESP8266 connections
   - Check network availability
   - Ensure correct credentials

3. **Sensor readings inaccurate**:
   - Allow warm-up time (especially for ENS160)
   - Check for air flow around sensors
   - Verify sensor connections

### Common API Issues

1. **API Not Responding**:
   - Check if the service is running: `systemctl status embedapi`
   - Check Nginx status: `systemctl status nginx`
   - Check logs: `journalctl -u embedapi`

2. **Model Prediction Errors**:
   - Verify input data formats match the required specifications
   - Check if models are properly loaded
   - Review server logs for detailed error messages

3. **Database Issues**:
   - Check database file permissions
   - Verify disk space is available
   - Use SQLite commands to check database integrity

## Maintenance and Updates

### Retraining Models

To retrain the models with new data:

1. Access the server via SSH
2. Navigate to the API directory: `cd /root/flask-api`
3. Run the training scripts:
   - For air quality model: `python3 train_air_quality.py`
   - For fire detection model: `python3 train_fire_model.py`
4. Restart the API service: `systemctl restart embedapi`

### Viewing the Database

To view the stored data in the SQLite database:

1. SSH into the server
2. Navigate to the API directory: `cd /root/flask-api`
3. Open the SQLite shell: `sqlite3 sensor_data.db`
4. List tables: `.tables`
5. View table schema: `.schema air_quality_data`
6. Query data: `SELECT * FROM air_quality_data LIMIT 10;`
7. Exit SQLite: `.exit`

## Future Development

Planned improvements for the system include:

1. **Hardware Enhancements**:
   - Battery-powered operation with low-power mode
   - Enclosure design for indoor/outdoor use
   - Additional sensors (e.g., CO, NO2, O3)

2. **Software Enhancements**:
   - Local data storage on SD card
   - Firmware updates over WiFi
   - User configuration interface

3. **API Enhancements**:
   - HTTPS support for secure communication
   - User authentication
   - Time-series analysis and anomaly detection
   - Mobile app integration

## License and Attribution

This project was developed as part of an environmental monitoring solution. The models are trained on publicly available datasets, including:

1. Air Quality Dataset: Numerically_Encoded_Air_Quality_Dataset.csv
2. Fire Detection Dataset: smoke_detection_iot.csv

## Contact Information

For support and further information, please contact [mozkan1@myseneca.ca](mailto:mozkan1@myseneca.ca)
