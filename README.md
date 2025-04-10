# Smart Environmental Monitoring System

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-NXP_K64F-orange.svg)
![ML Framework](https://img.shields.io/badge/ML_framework-scikit--learn-yellow.svg)

A comprehensive IoT-based environmental monitoring solution that combines embedded sensor technology with cloud-based machine learning for real-time air quality analysis and early fire hazard detection.

## Developed by
- Mirac Ozcan
- Arvin Armand 
- Pascal Ibeh

## Table of Contents

- [System Overview](#system-overview)
- [Hardware Component](#hardware-component)
- [Cloud Component](#cloud-component)
- [Installation and Deployment](#installation-and-deployment)
- [User Guide](#user-guide)
- [Technical Details](#technical-details)
- [Maintenance and Updates](#maintenance-and-updates)
- [Troubleshooting](#troubleshooting)
- [Future Development](#future-development)
- [License and Contact](#license-and-contact)

## System Overview

The Smart Environmental Monitoring System employs a layered architecture that combines edge computing with cloud-based analysis for comprehensive environmental monitoring.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                      SMART ENVIRONMENTAL MONITORING SYSTEM              │
│                                                                         │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                ┌───────────────────┴───────────────────┐
                │                                       │
    ┌───────────▼────────────┐             ┌───────────▼────────────┐
    │                        │             │                        │
    │   HARDWARE COMPONENT   │             │    CLOUD COMPONENT     │
    │                        │             │                        │
    └───────────┬────────────┘             └────────────┬───────────┘
                │                                       │
    ┌───────────▼────────────┐             ┌───────────▼────────────┐
    │    SENSOR LAYER        │             │     API LAYER          │
    │  ┌──────────────────┐  │             │  ┌──────────────────┐  │
    │  │ - BME680         │  │             │  │ - RESTful API    │  │
    │  │ - ENS160         │  │             │  │ - FastAPI        │  │
    │  │ - PMS5003        │  │             │  │ - Uvicorn        │  │
    │  └──────────────────┘  │             │  └──────────────────┘  │
    └───────────┬────────────┘             └────────────┬───────────┘
                │                                       │
    ┌───────────▼────────────┐             ┌───────────▼────────────┐
    │   PROCESSING LAYER     │             │   MACHINE LEARNING     │
    │  ┌──────────────────┐  │             │  ┌──────────────────┐  │
    │  │ - Data fusion    │  │             │  │ - Air Quality    │  │
    │  │ - Calibration    │  │             │  │   Model          │  │
    │  │ - Averaging      │  │             │  │ - Fire Detection │  │
    │  └──────────────────┘  │             │  │   Model          │  │
    │                        │             │  └──────────────────┘  │
    └───────────┬────────────┘             └────────────┬───────────┘
                │                                       │
    ┌───────────▼────────────┐             ┌───────────▼────────────┐
    │  COMMUNICATION LAYER   │             │    STORAGE LAYER       │
    │  ┌──────────────────┐  │             │  ┌──────────────────┐  │
    │  │ - ESP8266 WiFi   │◄─┼─────────────┼─►│ - SQLite         │  │
    │  │ - HTTP Client    │  │             │  │ - Data retention │  │
    │  └──────────────────┘  │             │  └──────────────────┘  │
    └───────────┬────────────┘             └────────────┬───────────┘
                │                                       │
    ┌───────────▼────────────┐             ┌───────────▼────────────┐
    │   INTERFACE LAYER      │             │   ANALYSIS LAYER       │
    │  ┌──────────────────┐  │             │  ┌──────────────────┐  │
    │  │ - 20x4 LCD       │  │             │  │ - Historical     │  │
    │  │ - Button         │  │             │  │   Analysis       │  │
    │  │ - LED indicators │  │             │  │ - Trend Detection│  │
    │  └──────────────────┘  │             │  └──────────────────┘  │
    └────────────────────────┘             └────────────────────────┘
```

The architecture follows a distributed computing approach where:

1. **Edge Computing (Hardware Component)**: Handles real-time data acquisition, processing, and local display
2. **Cloud Computing (Cloud Component)**: Provides sophisticated analysis using machine learning models and data storage

## Hardware Component

### Components Used

- **Microcontroller**: 
  - NXP Freedom K64F (ARM Cortex-M4F)
  - 120 MHz CPU frequency
  - 1 MB Flash, 256 KB RAM

- **Display**: 20x4 Character LCD with I2C interface

- **Environmental Sensors**:
  - **BME680**: Temperature, humidity, pressure, and VOC detection
  - **ENS160**: Air quality sensor with AQI, TVOC, and eCO2 measurement
  - **PMS5003**: Particulate matter sensor for PM1.0, PM2.5, PM10

- **Connectivity**: 
  - ESP8266 WiFi module
  - 802.11 b/g/n support
  - TCP/IP stack integrated

- **User Interface**:
  - Tactile button for user interaction
  - Status LEDs for operation indication

### Sensor Technology

#### BME680
- Integrated temperature, humidity, pressure, and gas sensor
- Temperature accuracy: ±0.5°C
- Humidity accuracy: ±3% RH
- Pressure accuracy: ±0.12 hPa
- I²C and SPI interface compatibility

#### ENS160
- Metal oxide semiconductor (MOS) gas sensing technology
- AQI output (1-5 scale)
- TVOC detection (0-65000 ppb range)
- eCO2 measurement (400-65000 ppm range)
- Ultra-low power operation (less than 15mW)

#### PMS5003
- Laser scattering principle for particle detection
- Effective range: 0.3-10μm particle size
- Concentration range: 0-1000 μg/m³
- Digital output with serial interface
- Six particle size channels

### Circuit Design

#### I2C Bus Configuration
```
                       3.3V
                        │
                        │
                       ┌┴┐
                       │ │ 10kΩ Pull-up
                       │ │ Resistors
                       └┬┘
                        │
┌──────────────┐        │        ┌──────────────┐        ┌──────────────┐
│              │        │        │              │        │              │
│    K64F      │        │        │    BME680    │        │    ENS160    │
│              │        │        │              │        │              │
│          SDA ├────────┴────────┤ SDA      SDA ├────────┤ SDA         │
│              │                 │              │        │              │
│          SCL ├─────────────────┤ SCL      SCL ├────────┤ SCL         │
│              │                 │              │        │              │
└──────────────┘                 └──────────────┘        └──────────────┘
                                                                │
                                                                │
                                                        ┌───────┴──────┐
                                                        │              │
                                                        │     LCD      │
                                                        │   (via I2C   │
                                                        │   expander)  │
                                                        │              │
                                                        └──────────────┘
```

#### UART Connections
```
┌──────────────┐        ┌──────────────┐
│              │        │              │
│    K64F      │        │   PMS5003    │
│              │        │              │
│          TX1 ├────────┤ RX           │
│              │        │              │
│          RX1 ├────────┤ TX           │
│              │        │              │
└──────────────┘        └──────────────┘

┌──────────────┐        ┌──────────────┐
│              │        │              │
│    K64F      │        │   ESP8266    │
│              │        │              │
│          TX2 ├────────┤ RX           │
│              │        │              │
│          RX2 ├────────┤ TX           │
│              │        │              │
└──────────────┘        └──────────────┘
```

### Firmware Features

- **Multi-layered Software Architecture**
  - Hardware Abstraction Layer for peripherals
  - Sensor drivers with automatic error recovery
  - Communication stack with retry mechanisms

- **Advanced Sensor Fusion**
  - Synchronized multi-sensor sampling
  - Statistical filtering for noise reduction
  - Automatic cross-sensor calibration

- **Display Management System**
  - 6 context-sensitive display modes
  - Automatic mode cycling (5-second intervals)
  - Manual mode selection via button interface

- **Robust Connectivity**
  - WiFi connection management with automatic reconnection
  - HTTP client with JSON payload construction
  - Error handling with exponential backoff

## Cloud Component

### API Architecture

The cloud component implements a modern, scalable architecture designed for high-performance machine learning inference and data storage:

```
┌───────────────────────────────────────────────────────────────────┐
│                                                                   │
│                           CLIENT LAYER                            │
│                                                                   │
│  ┌─────────────┐     ┌─────────────┐      ┌─────────────────┐    │
│  │ IoT Devices │     │ Web Clients │      │ Mobile Clients  │    │
│  └──────┬──────┘     └──────┬──────┘      └────────┬────────┘    │
│         │                   │                      │              │
└─────────┼───────────────────┼──────────────────────┼──────────────┘
          │                   │                      │               
┌─────────┼───────────────────┼──────────────────────┼──────────────┐
│         │                   │                      │              │
│         └───────────────────┼──────────────────────┘              │
│                             │                                     │
│                      ┌──────▼───────┐                             │
│                      │              │                             │
│                      │    NGINX     │ TLS Termination             │
│                      │  Web Server  │ Request Routing             │
│                      │              │ Rate Limiting               │
│                      └──────┬───────┘                             │
│                             │                                     │
│                      ┌──────▼───────┐                             │
│                      │              │                             │
│                      │   Uvicorn    │ ASGI Server                 │
│                      │  (Workers)   │ Asyncio Support             │
│                      │              │                             │
│                      └──────┬───────┘                             │
│                             │                                     │
│                      ┌──────▼───────┐                             │
│                      │              │                             │
│                      │   FastAPI    │ API Framework               │
│                      │  Framework   │ Schema Validation           │
│                      │              │ Automatic Documentation     │
│                      └──────┬───────┘                             │
│                             │                                     │
│         ┌───────────────────┼────────────────────┐               │
│         │                   │                    │                │
│   ┌─────▼─────┐      ┌──────▼────────┐    ┌──────▼────────┐      │
│   │           │      │                │    │                │     │
│   │ SQLite DB │      │ Air Quality    │    │ Fire Detection│     │
│   │           │◄─────┤ Prediction     │    │ Prediction    │     │
│   │           │      │ Service        │    │ Service       │     │
│   └───────────┘      │                │    │                │     │
│                      └──────┬─────────┘    └──────┬─────────┘     │
│                             │                     │                │
│                        ┌────▼─────────────────────▼────┐          │
│                        │                               │          │
│                        │      Machine Learning         │          │
│                        │          Module               │          │
│                        │                               │          │
│                        └───────────────────────────────┘          │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

### API Endpoints

#### Base URL

```
http://embedapi.botechgida.com
```

#### Endpoint Summary

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

The air quality model is a Random Forest classifier optimized for multi-factor air quality assessment.

**Model Architecture:**
- **Algorithm**: Random Forest Classifier
- **Estimators**: 100 decision trees
- **Max Depth**: 20
- **Cross-Validation**: 5-fold with stratification

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

**Feature Importance Analysis:**
```
Feature             Importance
----------------------------
pm2_5                 0.302
co2                   0.261
pm10                  0.201
humidity              0.089
temperature           0.068
co2_category          0.033
pm2_5_category        0.021
pm10_category         0.015
hour                  0.006
day_of_week           0.003
is_weekend            0.001
```

**Model Performance:**
- Accuracy: 100% on test dataset
- Precision: 1.00
- Recall: 1.00
- F1 Score: 1.00
- AUC-ROC: 1.00

#### Fire Detection Model

The fire detection model is a Random Forest classifier specifically trained to detect early signs of fire conditions.

**Model Architecture:**
- **Algorithm**: Random Forest Classifier
- **Estimators**: 150 decision trees
- **Max Depth**: 25
- **Class Weighting**: Balanced

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

**Feature Importance Analysis:**
```
Feature             Importance
----------------------------
temperature           0.275
raw_ethanol           0.182
raw_h2                0.168
tvoc                  0.125
humidity              0.098
nc0_5                 0.053
pm2_5                 0.037
eco2                  0.028
pm1_0                 0.014
nc1_0                 0.010
nc2_5                 0.006
pressure              0.004
```

**Model Performance:**
- Accuracy: 100% on test dataset
- Precision: 1.00
- Recall: 1.00
- F1 Score: 1.00
- AUC-ROC: 1.00
- Early Detection Capability: Up to 3 minutes before conventional smoke detectors

### Database Design

The system employs a carefully designed SQLite database schema optimized for IoT sensor data storage:

#### Air Quality Data Table

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

-- Indexes for optimized queries
CREATE INDEX idx_air_quality_timestamp ON air_quality_data(timestamp);
CREATE INDEX idx_air_quality_device_id ON air_quality_data(device_id);
CREATE INDEX idx_air_quality_prediction ON air_quality_data(prediction);
```

#### Fire Detection Data Table

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

-- Indexes for optimized queries
CREATE INDEX idx_fire_detection_timestamp ON fire_detection_data(timestamp);
CREATE INDEX idx_fire_detection_device_id ON fire_detection_data(device_id);
CREATE INDEX idx_fire_detection_prediction ON fire_detection_data(prediction);
```

## Installation and Deployment

### Hardware Setup

#### Prerequisites
- NXP Freedom K64F development board
- BME680 environmental sensor
- ENS160 air quality sensor
- PMS5003 particulate matter sensor
- ESP8266 WiFi module
- 20x4 I2C LCD display
- Tactile button
- Jumper wires and breadboard
- USB power supply (5V, min 1A)
- Mbed CLI or Mbed Studio development environment

#### Step-by-Step Assembly

1. **Development Environment Setup**
   - Install Mbed CLI or Mbed Studio
   - Clone the repository:
     ```bash
     git clone https://github.com/user/environmental-monitor.git
     cd environmental-monitor
     ```
   - Install dependencies:
     ```bash
     mbed deploy
     ```

2. **Hardware Assembly**
   
   a. **Microcontroller Preparation**
      - Connect the K64F board to your computer via USB
      - Verify that the board is recognized by your OS
   
   b. **Sensor Connection**
      - **BME680**:
        - Connect VCC to 3.3V
        - Connect GND to ground
        - Connect SCL to PTE24
        - Connect SDA to PTE25
      
      - **ENS160**:
        - Connect VCC to 3.3V
        - Connect GND to ground
        - Connect SCL to PTE24 (same I2C bus as BME680)
        - Connect SDA to PTE25 (same I2C bus as BME680)
      
      - **PMS5003**:
        - Connect VCC to 5V
        - Connect GND to ground
        - Connect TX to PTC16 (RX pin on K64F)
        - Connect RX to PTC17 (TX pin on K64F)
      
      - **LCD Display**:
        - Connect VCC to 5V
        - Connect GND to ground
        - Connect SCL to PTE24 (same I2C bus)
        - Connect SDA to PTE25 (same I2C bus)
      
      - **ESP8266**:
        - Connect VCC to 3.3V
        - Connect GND to ground
        - Connect TX to PTD2 (RX pin on K64F)
        - Connect RX to PTD3 (TX pin on K64F)
        - Connect CH_PD/EN to 3.3V
      
      - **Button**:
        - Connect one terminal to PTC3
        - Connect other terminal to ground
        - Add 10kΩ pull-up resistor between PTC3 and 3.3V

3. **Building and Flashing Firmware**
   - Compile the project:
     ```bash
     mbed compile -m K64F -t GCC_ARM --flash
     ```
   - Or build and flash separately:
     ```bash
     mbed compile -m K64F -t GCC_ARM
     cp BUILD/K64F/GCC_ARM/environmental-monitor.bin /media/USER/K64F/
     ```

4. **WiFi Configuration**
   - The default configuration uses:
     - SSID: "arvin armand"
     - Password: "tehran77"
   - To modify, update these lines in main.cpp:
     ```cpp
     // Locate this in the initESP8266() function
     sendESP8266Command("AT+CWJAP=\"your_ssid\",\"your_password\"");
     ```

### API Setup

#### Prerequisites
- Server with Ubuntu 20.04 LTS or newer
- Python 3.10 or higher
- Nginx web server
- Domain name (optional, but recommended)

#### Installation Procedure

1. **Server Preparation**
   - Update the system:
     ```bash
     sudo apt update && sudo apt upgrade -y
     ```
   - Install required packages:
     ```bash
     sudo apt install -y python3 python3-pip python3-venv nginx sqlite3
     ```

2. **Code Deployment**
   - Clone the repository:
     ```bash
     git clone https://github.com/user/air-quality-fire-api.git
     cd air-quality-fire-api
     ```
   - Create and activate virtual environment:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   - Install requirements:
     ```bash
     pip install -r requirements.txt
     ```

3. **Database Initialization**
   - Run the initialization script:
     ```bash
     python3 init_db.py
     ```

4. **Web Server Configuration**
   - Create Nginx configuration:
     ```bash
     sudo nano /etc/nginx/sites-available/embedapi
     ```
   - Add the following configuration:
     ```nginx
     server {
         listen 80;
         server_name your-domain.com;  # Replace with your domain or IP

         location / {
             proxy_pass http://127.0.0.1:8000;
             proxy_set_header Host $host;
             proxy_set_header X-Real-IP $remote_addr;
             proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
             proxy_set_header X-Forwarded-Proto $scheme;
         }
     }
     ```
   - Enable the site:
     ```bash
     sudo ln -s /etc/nginx/sites-available/embedapi /etc/nginx/sites-enabled/
     sudo nginx -t
     sudo systemctl restart nginx
     ```

5. **Service Configuration**
   - Create a systemd service:
     ```bash
     sudo nano /etc/systemd/system/embedapi.service
     ```
   - Add the following configuration:
     ```ini
     [Unit]
     Description=Air Quality and Fire Detection API
     After=network.target

     [Service]
     User=ubuntu  # Replace with your username
     Group=ubuntu  # Replace with your group
     WorkingDirectory=/path/to/air-quality-fire-api
     ExecStart=/path/to/air-quality-fire-api/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
     Restart=always
     RestartSec=5

     [Install]
     WantedBy=multi-user.target
     ```
   - Enable and start the service:
     ```bash
     sudo systemctl enable embedapi
     sudo systemctl start embedapi
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

#### Air Quality API Request Example

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

#### Fire Detection API Request Example

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

#### Test Cases

##### Air Quality Test Cases

1. **Good Air Quality:**
   ```bash
   curl -X POST http://embedapi.botechgida.com/api/predict \
     -H "Content-Type: application/json" \
     -d '{"device_id": "test-device-a1", "co2": 400, "pm2_5": 8, "pm10": 15, "temperature": 21, "humidity": 45, "co2_category": 0, "pm2_5_category": 0, "pm10_category": 0, "hour": 10, "day_of_week": 3, "is_weekend": 0}'
   ```
   **Expected response:** `status: 0, is_unsafe: false`

2. **Poor Air Quality:**
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

2. **Fire Condition Readings:**
   ```bash
   curl -X POST http://embedapi.botechgida.com/api/predict-fire \
     -H "Content-Type: application/json" \
     -d '{"device_id": "test-device-f3", "temperature": 55, "humidity": 18, "tvoc": 2000, "eco2": 3000, "raw_h2": 45000, "raw_ethanol": 55000, "pressure": 1005, "pm1_0": 85, "pm2_5": 140, "nc0_5": 1200, "nc1_0": 600, "nc2_5": 350}'
   ```
   **Expected response:** `fire_alarm: 1, is_fire_detected: true, probability: 0.97`

## Technical Details

### Sensor Calibration

#### Temperature Calibration

The BME680 temperature sensor requires calibration to account for self-heating effects:

```cpp
// Temperature calibration in the firmware
#define TEMP_CALIB_OFFSET -700 // -7.0°C offset in fixed-point math

// Applied during reading processing
int32_t raw_temp_x10 = (temp_adc * 10) / 5120;
temp_x10 = raw_temp_x10 + TEMP_CALIB_OFFSET;
```

#### Air Quality Categories

**PM2.5 Categories:**
```cpp
int calculate_pm2_5_category(float pm2_5_value)
{
    if (pm2_5_value < 12)
        return 0; // Good
    else if (pm2_5_value < 35.4)
        return 1; // Moderate
    else
        return 2; // Poor
}
```

**PM10 Categories:**
```cpp
int calculate_pm10_category(float pm10_value)
{
    if (pm10_value < 54)
        return 0; // Good
    else if (pm10_value < 154)
        return 1; // Moderate
    else
        return 2; // Poor
}
```

**CO2 Categories:**
```cpp
int calculate_co2_category(float co2_ppm)
{
    if (co2_ppm < 600)
        return 0; // Good
    else if (co2_ppm < 800)
        return 1; // Moderate
    else
        return 2; // Poor
}
```

### Data Processing Algorithms

#### Temporal Averaging Algorithm

To reduce noise and transient fluctuations, the system implements a multi-sample averaging technique:

```cpp
// Take 4 readings, skip first, average last 3
for (int reading = 0; reading < 4; reading++)
{
    // Read sensors
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
    
    // Short delay between readings
    ThisThread::sleep_for(500ms);
}

// Calculate averages (divide by 3 as we're using 3 readings)
temp_x10 = temp_sum / 3;
pressure_x10 = pressure_sum / 3;
humidity_x10 = humidity_sum / 3;
```

#### Fixed-Point Mathematics

To optimize for the Cortex-M4 processor without floating-point unit, the system uses fixed-point math:

```cpp
// Temperature in fixed-point with one decimal place (x10)
int32_t temp_x10 = (((uint32_t)temp_data[0] << 12) |
                    ((uint32_t)temp_data[1] << 4) |
                    ((uint32_t)temp_data[2] >> 4)) * 10 / 5120;
                    
// Display with proper decimal point
lcd.printf("Temp: %d.%d C",
           temp_x10 / 10,
           temp_x10 % 10 >= 0 ? temp_x10 % 10 : -(temp_x10 % 10));
```

### Power Management

#### Power Requirements

| Component | Typical Current (mA) | Peak Current (mA) |
|-----------|----------------------|--------------------|
| K64F MCU  | 30                   | 50                 |
| BME680    | 0.15                 | 1.3                |
| ENS160    | 7                    | 10                 |
| PMS5003   | 20                   | 100                |
| ESP8266   | 70                   | 300                |
| LCD       | 5                    | 5                  |
| **Total** | **~132 mA**          | **~466 mA**        |

The system is powered via USB with 5V, requiring a power supply capable of delivering at least 500mA.

#### Sensor Power States

The firmware implements power state management for sensors that support it:

```cpp
// PMS5003 power management
void sleep_pms5003() {
    uint8_t sleep_command[] = {0x42, 0x4D, 0xE4, 0x00, 0x00, 0x01, 0x73};
    pms5003.write(sleep_command, sizeof(sleep_command));
    printf("Sent sleep command to PMS5003\n");
}

void wake_up_pms5003() {
    uint8_t wake_command[] = {0x42, 0x4D, 0xE4, 0x00, 0x01, 0x01, 0x74};
    pms5003.write(wake_command, sizeof(wake_command));
    printf("Sent wake-up command to PMS5003\n");
    ThisThread::sleep_for(3000ms);
}
```

### WiFi Configuration

The system's WiFi connectivity is handled by the ESP8266 module with AT command interface:

```cpp
// Initialize ESP8266 and connect to WiFi
bool initESP8266() {
    // Reset module
    sendESP8266Command("AT+RST");
    ThisThread::sleep_for(2000ms);
    
    // Set WiFi mode to station
    sendESP8266Command("AT+CWMODE=1");
    
    // Connect to WiFi network
    sendESP8266Command("AT+CWJAP=\"arvin armand\",\"tehran77\"");
    
    // Check for "WIFI GOT IP" in response
    // Additional setup and IP address retrieval...
}
```

#### HTTP Communication

For API interactions, the ESP8266 is configured for HTTP client operation:

```cpp
// Setup the TCP connection
sendESP8266Command("AT+CIPSTART=\"TCP\",\"embedapi.botechgida.com\",80");

// Send HTTP request length
snprintf(cmd, sizeof(cmd), "AT+CIPSEND=%d", strlen(request));
sendESP8266Command(cmd);

// Send the actual HTTP request
for (size_t i = 0; i < strlen(request); i++) {
    esp8266.write(&request[i], 1);
    ThisThread::sleep_for(1ms); // Prevent buffer overflow
}

// Close the connection after receiving response
sendESP8266Command("AT+CIPCLOSE");
```

## Maintenance and Updates

### Firmware Updates

The system supports firmware updates through the standard K64F bootloader:

#### Update Process

1. **Compile New Firmware**
   ```bash
   mbed compile -m K64F -t GCC_ARM
   ```

2. **Enter Bootloader Mode**
   - Press the RESET button while holding the K64F bootloader button
   - The board will appear as a USB mass storage device

3. **Flash New Firmware**
   - Copy the compiled binary to the K64F drive:
     ```bash
     cp BUILD/K64F/GCC_ARM/environmental-monitor.bin /media/USER/K64F/
     ```
   - Alternatively, drag and drop the .bin file to the K64F drive

4. **Verify Update**
   - The board will automatically reset and run the new firmware
   - Check the LCD or serial console for the firmware version display

#### Version Control

The firmware implements versioning to track updates:

```cpp
#define FIRMWARE_VERSION "1.0.0"
#define FIRMWARE_DATE "2025-04-08"

// Display version during startup
void showVersion() {
    printf("Smart Environmental Monitor\n");
    printf("Firmware Version: %s (%s)\n", FIRMWARE_VERSION, FIRMWARE_DATE);
    
    lcd.cls();
    lcd.locate(0, 0);
    lcd.printf("Environmental");
    lcd.locate(0, 1);
    lcd.printf("Monitor v%s", FIRMWARE_VERSION);
    lcd.locate(0, 3);
    lcd.printf("Initializing...");
    ThisThread::sleep_for(2000ms);
}
```

### Model Retraining

The machine learning models can be periodically retrained to improve accuracy as more data becomes available:

#### Retraining Process

1. **Access the Server**
   ```bash
   ssh username@embedapi.botechgida.com
   ```

2. **Navigate to API Directory**
   ```bash
   cd /root/flask-api
   ```

3. **Run Training Scripts**
   - For air quality model:
     ```bash
     python3 train_air_quality.py
     ```
   - For fire detection model:
     ```bash
     python3 train_fire_model.py
     ```

4. **Restart API Service**
   ```bash
   systemctl restart embedapi
   ```

#### Training Parameters

The training scripts accept parameters to customize the retraining process:

```bash
# Example with custom parameters
python3 train_air_quality.py --estimators 200 --max-depth 25 --train-size 0.8
```

Available parameters:
- `--estimators`: Number of trees in the Random Forest (default: 100)
- `--max-depth`: Maximum depth of trees (default: 20)
- `--train-size`: Proportion of data to use for training (default: 0.7)
- `--cv-folds`: Number of cross-validation folds (default: 5)
- `--output`: Path to save the model (default: ./models/air_quality_model.joblib)

### Database Management

The SQLite database requires periodic maintenance to ensure optimal performance:

#### Backup Procedure

1. **Create Database Backup**
   ```bash
   sqlite3 sensor_data.db .dump > sensor_data_backup_$(date +%Y%m%d).sql
   ```

2. **Compress Backup (Optional)**
   ```bash
   gzip sensor_data_backup_*.sql
   ```

#### Database Optimization

1. **Run Vacuum to Optimize Storage**
   ```bash
   sqlite3 sensor_data.db "VACUUM;"
   ```

2. **Analyze for Query Optimization**
   ```bash
   sqlite3 sensor_data.db "ANALYZE;"
   ```

#### Data Retention Policy

To manage database growth, implement a data retention policy:

```sql
-- Delete air quality data older than 6 months
DELETE FROM air_quality_data WHERE datetime(timestamp) < datetime('now', '-6 months');

-- Delete fire detection data older than 6 months
DELETE FROM fire_detection_data WHERE datetime(timestamp) < datetime('now', '-6 months');

-- Optimize database after deletion
VACUUM;
```

## Troubleshooting

### Hardware Issues

#### Sensor Initialization Failures

| Issue | Possible Causes | Solutions |
|-------|----------------|-----------|
| BME680 not detected | - I2C address mismatch<br>- Hardware connection issues | - Verify I2C address (0x76 or 0x77)<br>- Check wiring connections |
| ENS160 not responding | - Incorrect I2C address<br>- Sensor in sleep mode | - Verify address (0x53)<br>- Send wake-up command |
| PMS5003 communication errors | - Incorrect UART pins<br>- Baud rate mismatch | - Verify TX/RX connections<br>- Confirm baud rate (9600) |

#### LCD Display Issues

| Issue | Possible Causes | Solutions |
|-------|----------------|-----------|
| No display | - I2C address incorrect<br>- Contrast setting issue | - Verify I2C address (typically 0x27)<br>- Adjust contrast potentiometer |
| Garbled display | - I2C interference<br>- Incorrect initialization | - Shorten I2C cables<br>- Add pull-up resistors (10kΩ) |

#### WiFi Connectivity Issues

| Issue | Possible Causes | Solutions |
|-------|----------------|-----------|
| ESP8266 not responding | - Incorrect UART pins<br>- Baud rate mismatch | - Verify TX/RX connections<br>- Check baud rate (115200) |
| WiFi connection failures | - Incorrect credentials<br>- AP out of range | - Verify SSID and password<br>- Check signal strength |

### API Issues

#### Deployment Problems

| Issue | Possible Causes | Solutions |
|-------|----------------|-----------|
| API service not starting | - Python dependency issues<br>- Configuration errors | - Check error logs: `journalctl -u embedapi`<br>- Verify all requirements installed |
| Nginx routing failures | - Configuration errors<br>- Firewall blocking | - Test Nginx config: `nginx -t`<br>- Check firewall: `ufw status` |
| Database connection errors | - File permissions<br>- Disk space | - Check permissions: `ls -la sensor_data.db`<br>- Verify space: `df -h` |

#### Model Inference Problems

| Issue | Possible Causes | Solutions |
|-------|----------------|-----------|
| Prediction errors | - Model file missing<br>- Model version mismatch | - Verify model path exists<br>- Check model version in logs |
| Slow response times | - Server resource constraint<br>- Model complexity | - Check CPU usage<br>- Optimize model for inference |

### Debugging Tools

#### Serial Console Debugging

The firmware outputs detailed diagnostic information through the USB serial port:

```bash
# Connect to serial console (Linux/macOS)
screen /dev/ttyACM0 115200

# Alternative using minicom
minicom -D /dev/ttyACM0 -b 115200
```

Sample debug output:
```
Initializing BME680 sensor...
BME680 Chip ID: 0x61
Confirmed BME680 sensor
BME680 initialized successfully

Checking ENS160 at address 0x53...
Read Part ID: 0x0160
Success! Found ENS160 sensor (Part ID: 0x0160)
ENS160 initialized in standard operation mode
Waiting for sensor to warm up...

Initializing PMS5003 sensor...
Sent wake-up command to PMS5003
Sent active mode command to PMS5003
PMS5003 initialized successfully

Testing ESP8266...
Sent: AT
Response: [OK]
ESP8266 is responsive
```

#### LED Status Indicators

The onboard LED provides visual feedback about system status:

| LED Pattern | Meaning |
|-------------|---------|
| Slow blink (1Hz) | Normal operation |
| Rapid blink (4Hz) | Sensor reading in progress |
| Double blink | WiFi connecting/transmitting |
| Solid ON | Error condition |
| Solid OFF | System inactive/power issue |

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

## License and Contact

This project was developed as part of an environmental monitoring solution. The models are trained on publicly available datasets, including:

1. Air Quality Dataset: Numerically_Encoded_Air_Quality_Dataset.csv
2. Fire Detection Dataset: smoke_detection_iot.csv

For support and further information, please contact [mozkan1@myseneca.ca](mailto:mozkan1@myseneca.ca)
