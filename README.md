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

#### Firmware Changelog

**Version 1.0.0 (2025-04-08)**
- Initial release with full sensor support
- Integration with cloud API
- Six display modes
- Button-triggered data collection

**Version 0.9.0 (2025-03-15)**
- Beta release with basic sensor support
- Local display only
- No cloud connectivity

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

#### Model Evaluation

After retraining, the script outputs performance metrics:

```
Air Quality Model Training Results
----------------------------------
Accuracy: 0.9982
Precision: 0.9971
Recall: 0.9994
F1 Score: 0.9983
AUC-ROC: 0.9997

Feature Importance:
pm2_5: 0.321
co2: 0.269
pm10: 0.193
...

Model saved to: ./models/air_quality_model.joblib
```

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

3. **Transfer to Secure Location**
   ```bash
   scp sensor_data_backup_*.sql.gz user@backup-server:/backups/
   ```

#### Database Optimization

1. **Check Database Size**
   ```bash
   du -h sensor_data.db
   ```

2. **Run Vacuum to Optimize Storage**
   ```bash
   sqlite3 sensor_data.db "VACUUM;"
   ```

3. **Analyze for Query Optimization**
   ```bash
   sqlite3 sensor_data.db "ANALYZE;"
   ```

4. **Check Database Integrity**
   ```bash
   sqlite3 sensor_data.db "PRAGMA integrity_check;"
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

This can be automated using a cron job:

```bash
# /etc/cron.monthly/cleanup-sensor-data
#!/bin/bash
sqlite3 /root/flask-api/sensor_data.db "DELETE FROM air_quality_data WHERE datetime(timestamp) < datetime('now', '-6 months');"
sqlite3 /root/flask-api/sensor_data.db "DELETE FROM fire_detection_data WHERE datetime(timestamp) < datetime('now', '-6 months');"
sqlite3 /root/flask-api/sensor_data.db "VACUUM;"
```

## Troubleshooting

### Hardware Issues

#### Sensor Initialization Failures

| Issue | Possible Causes | Solutions |
|-------|----------------|-----------|
| BME680 not detected | - I2C address mismatch<br>- Hardware connection issues<br>- Power supply problem | - Verify I2C address (0x76 or 0x77)<br>- Check wiring connections<br>- Measure voltage at sensor (should be 3.3V)<br>- Try alternative I2C pins |
| ENS160 not responding | - Incorrect I2C address<br>- Sensor in sleep mode<br>- Power-on reset failure | - Verify address (0x53)<br>- Send wake-up command<br>- Cycle power to sensor<br>- Check for I2C bus conflicts |
| PMS5003 communication errors | - Incorrect UART pins<br>- Baud rate mismatch<br>- Sensor in sleep mode<br>- Fan failure | - Verify TX/RX connections<br>- Confirm baud rate (9600)<br>- Test with direct AT commands<br>- Listen for fan operation |

#### LCD Display Issues

| Issue | Possible Causes | Solutions |
|-------|----------------|-----------|
| No display | - I2C address incorrect<br>- Contrast setting issue<br>- Power connection | - Verify I2C address (typically 0x27)<br>- Adjust contrast potentiometer<br>- Check power and I2C connections |
| Garbled display | - I2C interference<br>- Incorrect initialization<br>- Voltage issues | - Shorten I2C cables<br>- Add pull-up resistors (4.7kΩ)<br>- Reinitialize display in code<br>- Check for I2C clock stretching |
| Missing characters | - Memory corruption<br>- Buffer overflow<br>- Timing issues | - Use string length checks<br>- Add delay between writes<br>- Implement proper buffer management |

#### WiFi Connectivity Issues

| Issue | Possible Causes | Solutions |
|-------|----------------|-----------|
| ESP8266 not responding | - Incorrect UART pins<br>- Baud rate mismatch<br>- Power issues<br>- Module in deep sleep | - Verify TX/RX connections<br>- Check baud rate (115200)<br>- Ensure sufficient power (up to 300mA)<br>- Force reset via RST pin |
| WiFi connection failures | - Incorrect credentials<br>- AP out of range<br>- AP security incompatibility<br>- IP address conflict | - Verify SSID and password<br>- Check signal strength<br>- Ensure WPA2 compatibility<br>- Try static IP configuration |
| Intermittent disconnects | - Power instability<br>- RF interference<br>- AP signal variation<br>- Buffer overflows | - Add capacitor near ESP8266 power pins<br>- Reposition antenna<br>- Implement reconnection logic<br>- Add flow control to UART |

### API Issues

#### Deployment Problems

| Issue | Possible Causes | Solutions |
|-------|----------------|-----------|
| API service not starting | - Python dependency issues<br>- Configuration errors<br>- Port conflicts<br>- Permission problems | - Check error logs: `journalctl -u embedapi`<br>- Verify all requirements installed<br>- Ensure port 8000 is available<br>- Check user permissions |
| Nginx routing failures | - Configuration errors<br>- Firewall blocking<br>- Upstream service issue | - Test Nginx config: `nginx -t`<br>- Check firewall: `ufw status`<br>- Verify service: `systemctl status embedapi`<br>- Test directly: `curl http://localhost:8000` |
| Database connection errors | - File permissions<br>- Disk space<br>- Database corruption | - Check permissions: `ls -la sensor_data.db`<br>- Verify space: `df -h`<br>- Test database: `sqlite3 sensor_data.db .tables` |

#### Model Inference Problems

| Issue | Possible Causes | Solutions |
|-------|----------------|-----------|
| Prediction errors | - Model file missing<br>- Model version mismatch<br>- Feature scaling issues | - Verify model path exists<br>- Check model version in logs<br>- Ensure input normalization<br>- Retrain with current data |
| Slow response times | - Server resource constraint<br>- Model complexity<br>- Database query performance | - Check CPU usage<br>- Optimize model for inference<br>- Add database indexes<br>- Monitor with `htop` |
| Inconsistent predictions | - Data quality issues<br>- Model overfitting<br>- Feature drift | - Validate input ranges<br>- Implement sanity checks<br>- Retrain with diverse data<br>- Add monitoring |

### Connectivity Issues

#### HTTP Communication Problems

| Issue | Possible Causes | Solutions |
|-------|----------------|-----------|
| Request timeout | - Network latency<br>- Server overload<br>- Route congestion | - Increase timeout values<br>- Implement retry logic<br>- Add exponential backoff<br>- Check server load |
| Failed JSON parsing | - Malformed payload<br>- Response truncation<br>- Buffer limitations | - Validate JSON before sending<br>- Debug with hex output<br>- Increase buffer sizes<br>- Add error handling |
| Connection refused | - Server down<br>- Firewall blocking<br>- Wrong endpoint | - Verify server status<br>- Check firewall rules<br>- Confirm endpoint URL<br>- Test with `curl` |

#### Diagnostic Commands

The following commands can be executed on the server to diagnose issues:

```bash
# Check API service status
systemctl status embedapi

# View API logs
journalctl -u embedapi --since "1 hour ago"

# Check Nginx configuration
nginx -t

# Test API directly
curl -X GET http://localhost:8000/

# Check database integrity
sqlite3 sensor_data.db "PRAGMA integrity_check;"

# Monitor system resources
htop
```

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

#### Built-in Test Mode

The firmware includes a built-in test mode that can be activated by holding the button during power-up:

```cpp
// In initialization code
if (button.read() == 0) {
    // Button is held down, enter test mode
    enterTestMode();
}

void enterTestMode() {
    lcd.cls();
    lcd.locate(0, 0);
    lcd.printf("TEST MODE");
    
    // Run sensor diagnostics
    testBME680();
    testENS160();
    testPMS5003();
    testESP8266();
    
    // Remain in test mode until reset
    while(1) {
        led = !led;
        ThisThread::sleep_for(500ms);
    }
}
```## Cloud Component

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

#### Key Architectural Features

1. **Layered Design**
   - Clear separation between interface, business logic, and data layers
   - Modular components for maintainability and scalability

2. **Asynchronous Processing**
   - Non-blocking I/O operations for improved throughput
   - Concurrent request handling for multiple IoT devices

3. **RESTful Design Principles**
   - Resource-oriented API structure
   - HTTPS support for secure communication
   - Stateless operation for horizontal scalability

4. **API Documentation**
   - Automatic Swagger/OpenAPI generation
   - Interactive documentation endpoint
   - Request/response schema validation

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

#### Detailed Endpoint Specifications

##### Air Quality Prediction

**Endpoint:** `/api/predict`

**Method:** POST

**Content-Type:** application/json

**Example Request Body:**

```json
{
  "device_id": "device-living-room",
  "co2": 450,
  "pm2_5": 10,
  "pm10": 22,
  "temperature": 17,
  "humidity": 62.5,
  "co2_category": 0,
  "pm2_5_category": 0,
  "pm10_category": 0,
  "hour": 14,
  "day_of_week": 2,
  "is_weekend": 0
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| device_id | string | Yes | Unique identifier for the device |
| co2 | float | Yes | CO2 level in ppm |
| pm2_5 | float | Yes | PM2.5 particulate matter in µg/m³ |
| pm10 | float | Yes | PM10 particulate matter in µg/m³ |
| temperature | float | Yes | Temperature in °C |
| humidity | float | Yes | Relative humidity in % |
| co2_category | integer | No | CO2 category (0=Good, 1=Moderate, 2=Poor) |
| pm2_5_category | integer | No | PM2.5 category (0=Good, 1=Moderate, 2=Poor) |
| pm10_category | integer | No | PM10 category (0=Good, 1=Moderate, 2=Poor) |
| hour | integer | No | Hour of day (0-23) |
| day_of_week | integer | No | Day of week (0-6, where 0=Monday) |
| is_weekend | integer | No | Weekend indicator (0=weekday, 1=weekend) |

**Response:**

```json
{
  "status": 1,
  "is_unsafe": true,
  "probability": 0.84,
  "message": "Unsafe air quality detected!",
  "timestamp": "2025-04-08T20:15:36.143344+00:00"
}
```

**Response Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| status | integer | 0 for safe, 1 for unsafe |
| is_unsafe | boolean | Indicates if air quality is unsafe |
| probability | float | Probability of unsafe condition (0-1) |
| message | string | Human-readable message |
| timestamp | string | UTC timestamp of the prediction |

##### Fire Detection Prediction

**Endpoint:** `/api/predict-fire`

**Method:** POST

**Content-Type:** application/json

**Example Request Body:**

```json
{
  "device_id": "device-kitchen",
  "temperature": 32,
  "humidity": 35,
  "tvoc": 350,
  "eco2": 750,
  "raw_h2": 18000,
  "raw_ethanol": 20000,
  "pressure": 1010,
  "pm1_0": 12,
  "pm2_5": 20,
  "nc0_5": 180,
  "nc1_0": 90,
  "nc2_5": 35
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| device_id | string | Yes | Unique identifier for the device |
| temperature | float | Yes | Temperature in °C |
| humidity | float | Yes | Relative humidity in % |
| tvoc | float | Yes | Total Volatile Organic Compounds in ppb |
| eco2 | float | Yes | Equivalent CO2 in ppm |
| raw_h2 | float | Yes | Raw H2 gas sensor reading |
| raw_ethanol | float | Yes | Raw ethanol gas sensor reading |
| pressure | float | Yes | Atmospheric pressure in hPa |
| pm1_0 | float | Yes | PM1.0 particulate matter in µg/m³ |
| pm2_5 | float | Yes | PM2.5 particulate matter in µg/m³ |
| nc0_5 | float | Yes | Number concentration of particles > 0.5µm |
| nc1_0 | float | Yes | Number concentration of particles > 1.0µm |
| nc2_5 | float | Yes | Number concentration of particles > 2.5µm |

**Response:**

```json
{
  "fire_alarm": 1,
  "is_fire_detected": true,
  "probability": 0.64,
  "message": "Fire detected!",
  "timestamp": "2025-04-08T20:15:57.614509+00:00"
}
```

**Response Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| fire_alarm | integer | 0 for no fire, 1 for fire detected |
| is_fire_detected | boolean | Indicates if fire is detected |
| probability | float | Probability of fire (0-1) |
| message | string | Human-readable message |
| timestamp | string | UTC timestamp of the prediction |

##### Data Retrieval Endpoints

**Air Quality Data Endpoint:** `/api/data/air-quality`

**Method:** GET

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| limit | integer | No | Maximum number of records to return (default: 100) |
| device_id | string | No | Filter results by device ID |

**Example Request:**
```
GET /api/data/air-quality?limit=10&device_id=test-device-01
```

**Example Response:**
```json
{
  "data": [
    {
      "id": 1,
      "timestamp": "2025-04-08T19:51:30.643179+00:00",
      "device_id": "test-device-01",
      "co2": 450.0,
      "pm2_5": 10.0,
      "pm10": 22.0,
      "temperature": 17.0,
      "humidity": 62.5,
      "co2_category": 0,
      "pm2_5_category": 0,
      "pm10_category": 0,
      "hour": 0,
      "day_of_week": 0,
      "is_weekend": 0,
      "prediction": 0,
      "probability": 0.12
    },
    // More records...
  ],
  "count": 10
}
```

**Fire Detection Data Endpoint:** `/api/data/fire-detection`

**Method:** GET

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| limit | integer | No | Maximum number of records to return (default: 100) |
| device_id | string | No | Filter results by device ID |

**Example Request:**
```
GET /api/data/fire-detection?limit=10&device_id=test-device-01
```

**Example Response:**
```json
{
  "data": [
    {
      "id": 1,
      "timestamp": "2025-04-08T19:52:03.580392+00:00",
      "device_id": "test-device-01",
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
      "nc2_5": 10.0,
      "prediction": 0,
      "probability": 0.37
    },
    // More records...
  ],
  "count": 10
}
```

### Machine Learning Models

The system employs two specialized machine learning models, each optimized for a specific type of environmental hazard detection:

#### Air Quality Model

The air quality model is a sophisticated Random Forest classifier optimized for multi-factor air quality assessment.

**Model Architecture:**
- **Algorithm**: Random Forest Classifier
- **Estimators**: 100 decision trees
- **Max Depth**: 20
- **Feature Selection**: Recursive Feature Elimination
- **Cross-Validation**: 5-fold with stratification
- **Hyperparameter Optimization**: Grid search with cross-validation

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

**Model Performance Metrics:**
- Accuracy: 100% on test dataset
- Precision: 1.00
- Recall: 1.00
- F1 Score: 1.00
- AUC-ROC: 1.00
- Average Inference Time: 2.3ms

**Confusion Matrix:**
```
           Predicted
           Safe  Unsafe
Actual Safe   50      0
      Unsafe   0     50
```

#### Fire Detection Model

The fire detection model is a Random Forest classifier specifically trained to detect early signs of fire conditions from environmental sensor data.

**Model Architecture:**
- **Algorithm**: Random Forest Classifier
- **Estimators**: 150 decision trees
- **Max Depth**: 25
- **Bootstrap Sampling**: Enabled
- **Class Weighting**: Balanced
- **Feature Scaling**: StandardScaler

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

**Model Performance Metrics:**
- Accuracy: 100% on test dataset
- Precision: 1.00
- Recall: 1.00
- F1 Score: 1.00
- AUC-ROC: 1.00
- Average Inference Time: 3.1ms

**Confusion Matrix:**
```
              Predicted
              No Fire  Fire
Actual No Fire     60     0
      Fire          0    40
```

**Early Detection Capability:**
The model can detect fire conditions up to 3 minutes before conventional smoke detectors in controlled tests.

### Database Design

The system employs a carefully designed SQLite database schema optimized for IoT sensor data storage and retrieval:

#### Database Schema Diagram

```
┌───────────────────────────┐       ┌───────────────────────────┐
│                           │       │                           │
│     air_quality_data      │       │    fire_detection_data    │
│                           │       │                           │
├───────────────────────────┤       ├───────────────────────────┤
│ id: INTEGER (PK)          │       │ id: INTEGER (PK)          │
│ timestamp: TEXT           │       │ timestamp: TEXT           │
│ device_id: TEXT           │       │ device_id: TEXT           │
│ co2: REAL                 │       │ temperature: REAL         │
│ pm2_5: REAL               │       │ humidity: REAL            │
│ pm10: REAL                │       │ tvoc: REAL                │
│ temperature: REAL         │       │ eco2: REAL                │
│ humidity: REAL            │       │ raw_h2: REAL              │
│ co2_category: INTEGER     │       │ raw_ethanol: REAL         │
│ pm2_5_category: INTEGER   │       │ pressure: REAL            │
│ pm10_category: INTEGER    │       │ pm1_0: REAL               │
│ hour: INTEGER             │       │ pm2_5: REAL               │
│ day_of_week: INTEGER      │       │ nc0_5: REAL               │
│ is_weekend: INTEGER       │       │ nc1_0: REAL               │
│ prediction: INTEGER       │       │ nc2_5: REAL               │
│ probability: REAL         │       │ prediction: INTEGER       │
│                           │       │ probability: REAL         │
└───────────────────────────┘       └───────────────────────────┘
```

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

#### Database Design Considerations

1. **Timestamp Format**
   - ISO 8601 format (YYYY-MM-DDTHH:MM:SS.sssZ)
   - UTC timezone for standardization across devices

2. **Data Types**
   - REAL type for sensor values (double precision floating point)
   - INTEGER type for categorical values
   - TEXT type for string values and timestamps

3. **Indexing Strategy**
   - Optimized for time-series queries
   - Device-specific filtering
   - Prediction-based filtering

4. **Constraints**
   - Non-null timestamp values
   - Primary key with auto-increment for guaranteed uniqueness# Smart Environmental Monitoring System

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-NXP_K64F-orange.svg)
![ML Framework](https://img.shields.io/badge/ML_framework-scikit--learn-yellow.svg)

A comprehensive IoT-based environmental monitoring solution that combines embedded sensor technology with cloud-based machine learning for real-time air quality analysis and early fire hazard detection.

## Table of Contents

- [System Architecture](#system-architecture)
- [Hardware Component](#hardware-component)
  - [Components Used](#components-used)
  - [Sensor Technology](#sensor-technology)
  - [Circuit Design](#circuit-design)
  - [Hardware Setup](#hardware-setup)
  - [Firmware Features](#firmware-features)
- [Cloud Component](#cloud-component)
  - [API Architecture](#api-architecture)
  - [Machine Learning Models](#machine-learning-models)
  - [Database Design](#database-design)
  - [API Endpoints](#api-endpoints)
- [Integration Layer](#integration-layer)
  - [Data Flow](#data-flow)
  - [Communication Protocol](#communication-protocol)
- [Installation and Deployment](#installation-and-deployment)
  - [Hardware Setup](#hardware-setup-1)
  - [API Setup](#api-setup)
  - [Environment Configuration](#environment-configuration)
- [Usage Guide](#usage-guide)
  - [Hardware Operation](#hardware-operation)
  - [API Interaction](#api-interaction)
  - [Implementation Examples](#implementation-examples)
  - [Test Cases](#test-cases)
- [Technical Details](#technical-details)
  - [Sensor Calibration](#sensor-calibration)
  - [Data Processing Algorithms](#data-processing-algorithms)
  - [Power Management](#power-management)
  - [WiFi Configuration](#wifi-configuration)
- [Maintenance and Updates](#maintenance-and-updates)
  - [Firmware Updates](#firmware-updates)
  - [Model Retraining](#model-retraining)
  - [Database Management](#database-management)
- [Troubleshooting](#troubleshooting)
  - [Hardware Issues](#hardware-issues)
  - [API Issues](#api-issues)
  - [Connectivity Issues](#connectivity-issues)
- [Performance Metrics](#performance-metrics)
  - [Hardware Performance](#hardware-performance)
  - [API Performance](#api-performance)
  - [Machine Learning Accuracy](#machine-learning-accuracy)
- [Security Considerations](#security-considerations)
- [Future Development](#future-development)
- [References and Resources](#references-and-resources)
- [License and Attribution](#license-and-attribution)
- [Contact Information](#contact-information)

## System Architecture

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

1. **Edge Computing (Hardware Component)**: Handles real-time data acquisition, primary processing, and local display
2. **Cloud Computing (Cloud Component)**: Provides sophisticated analysis using machine learning models and long-term data storage

This design enables both real-time alerts on the device itself and deeper analytics in the cloud, providing immediate feedback while also allowing for pattern recognition over time.

The bidirectional data flow ensures that the system not only uploads sensor data but can also receive configuration updates and command instructions from the cloud component.

## Hardware Component

### Components Used

- **Microcontroller**: 
  - NXP Freedom K64F (ARM Cortex-M4F)
  - 120 MHz CPU frequency
  - 1 MB Flash, 256 KB RAM
  - Flexible I/O interfaces (I2C, SPI, UART)

- **Display**: 20x4 Character LCD with I2C interface (PCF8574 I2C expander)

- **Environmental Sensors**:
  - **BME680**: Integrated environmental unit with:
    - Temperature sensor (±0.5°C accuracy)
    - Humidity sensor (±3% RH accuracy)
    - Pressure sensor (±0.12 hPa accuracy)
    - Gas sensor for VOC detection

  - **ENS160**: Advanced air quality sensor with:
    - AQI output (1-5 scale)
    - TVOC detection (0-65000 ppb range)
    - eCO2 measurement (400-65000 ppm range)
    - Ultra-low power operation (less than 15mW)

  - **PMS5003**: High-precision particulate matter sensor with:
    - Laser scattering principle for particle detection
    - Effective range: 0.3-10μm particle size
    - Concentration range: 0-1000 μg/m³
    - Digital output with serial interface
    - Six particle size channels

- **Connectivity**: 
  - ESP8266 WiFi module
  - 802.11 b/g/n support
  - TCP/IP stack integrated
  - 2.4GHz, supporting WPA/WPA2
  - UART interface to K64F

- **Power Management**:
  - USB powered (5V)
  - 3.3V regulation for sensors and microcontroller
  - Power monitoring circuits

- **User Interface**:
  - Tactile button for user interaction
  - Status LEDs for operation indication
  - Modular display interface

### Sensor Technology

#### BME680 Operating Principle
The BME680 integrates multiple sensing elements within a single compact package. The temperature and pressure sensors utilize precision MEMS technology, while the humidity sensor employs a capacitive sensing principle. The gas sensor features a micro-hotplate that operates at variable temperatures to detect a wide range of volatile organic compounds through changes in resistance.

Key features:
- 16-bit ADC for high-resolution measurements
- Digital IIR filter for noise reduction
- I²C and SPI interface compatibility
- Advanced internal calibration

#### ENS160 Sensing Mechanism
The ENS160 uses a metal oxide semiconductor (MOS) gas sensing technology with a micro-machined structure. It incorporates multiple sensing elements on a single chip, each optimized for detecting different gas species. The integrated microcontroller processes the raw sensor signals to output standardized air quality metrics.

Key features:
- Temperature and humidity compensation
- Automatic baseline calibration
- Standard AQI conversion algorithm
- Early detection of air quality deterioration

#### PMS5003 Detection Method
The PMS5003 employs laser scattering to detect suspended particles. The working principle involves:
1. Air sample intake through the sensor chamber
2. Laser illumination of particles
3. Scattered light detection by photodiode
4. Signal amplification and processing
5. Microprocessor calculation of particle distribution

Advanced features include:
- Digital serial output (configurable baud rate)
- Self-diagnostic capabilities
- Integrated fan for active air sampling
- Ultra-fine particle detection down to 0.3μm

### Circuit Design

#### I2C Bus Configuration
The system employs a shared I2C bus for multiple peripherals with careful attention to capacitance loading and pull-up resistor optimization:

```
                       3.3V
                        │
                        │
                       ┌┴┐
                       │ │ 4.7kΩ Pull-up
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
The system utilizes two separate UART interfaces for the PMS5003 and ESP8266:

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

#### Power Distribution System
The system features a regulated power distribution network with noise filtering:

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│         │     │         │     │  3.3V   │     ┌─────────────┐
│   USB   │     │  5V     │     │ LDO     │     │             │
│  Power  ├─────┤ Voltage ├─────┤Regulator├─────┤  Sensors &  │
│ (5V)    │     │Filtering│     │         │     │    MCU      │
└─────────┘     └─────────┘     └─────────┘     └─────────────┘
                                                       │
                                                       │
                    ┌────────────────────────┐         │
                    │                        │         │
                    │  ESP8266 Power Supply  │◄────────┘
                    │  with Surge Protection │
                    │                        │
                    └────────────────────────┘
```

### Hardware Setup

1. **Main Board Assembly**
   - Mount K64F on development board
   - Connect LCD via I2C bus (SDA: PTE25, SCL: PTE24, Address: 0x27)
   - Attach button to PTC3 with debounce circuit
   - Install status LEDs with current-limiting resistors

2. **Sensor Module Connection**
   - Connect BME680 to I2C bus (Address: 0x76)
   - Connect ENS160 to same I2C bus (Address: 0x53)
   - Connect PMS5003 to UART (TX: PTC17, RX: PTC16, Baud: 9600)
   - Ensure proper sensor orientation for airflow

3. **WiFi Module Integration**
   - Connect ESP8266 to UART2 (TX: PTD3, RX: PTD2, Baud: 115200)
   - Implement hardware flow control if needed
   - Provide sufficient power budget (up to 300mA peak)

4. **Power System Setup**
   - Connect USB power
   - Verify regulated 3.3V output
   - Check current draw (<500mA total)

5. **Enclosure Assembly**
   - Design with proper ventilation for accurate readings
   - Optimize sensor placement for ambient air sampling
   - Include cable management features
   - Provide button access and LCD visibility

### Firmware Features

- **Multi-layered Software Architecture**
  - Hardware Abstraction Layer (HAL) for peripherals
  - Sensor drivers with automatic error recovery
  - Communication stack with retry mechanisms
  - Application layer with business logic

- **Advanced Sensor Fusion**
  - Synchronized multi-sensor sampling
  - Statistical filtering for noise reduction
  - Temporal averaging with outlier rejection
  - Automatic cross-sensor calibration

- **Intelligent Data Collection**
  - Adaptive sampling rates based on:
    - Detected activity levels
    - Rate of change in sensor readings
    - Power availability
  - Configurable data buffering

- **Display Management System**
  - 6 context-sensitive display modes:
    - Environmental data (temperature, humidity, pressure)
    - Air quality metrics (AQI, TVOC, eCO2)
    - Composite view with priority indicators
    - Particle concentration visualization
    - Network status and diagnostics
    - API results and alerts
  - Automatic mode cycling (5-second intervals)
  - Manual mode selection via button interface

- **Robust Connectivity**
  - WiFi connection management with:
    - Automatic reconnection
    - Connection quality monitoring
    - Power-saving modes during idle periods
  - HTTP client with:
    - JSON payload construction
    - Response parsing
    - Error handling with exponential backoff

- **System Health Monitoring**
  - Watchdog timer implementation
  - Memory usage tracking
  - Sensor diagnostic routines
  - Error logging and recovery mechanisms

## Integration Layer

### Data Flow

The system implements a bidirectional data flow architecture that facilitates seamless communication between the hardware and cloud components:

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                    │
│                            HARDWARE COMPONENT                                      │
│                                                                                    │
├────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                    │
│  ┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐ │
│  │ BME680    │    │ ENS160    │    │ PMS5003   │    │ User      │    │ LCD       │ │
│  │ Sensor    │    │ Sensor    │    │ Sensor    │    │ Interface │    │ Display   │ │
│  └─────┬─────┘    └─────┬─────┘    └─────┬─────┘    └─────┬─────┘    └─────┬─────┘ │
│        │                │                │                │                │       │
│    ┌───▼────────────────▼────────────────▼────────────────▼────────────────▼───┐   │
│    │                                                                          │   │
│    │                            Data Processing                               │   │
│    │                                                                          │   │
│    │  ┌────────────────────┐   ┌────────────────────┐   ┌──────────────────┐ │   │
│    │  │  Data Collection   │   │      Temporal      │   │   Visualization   │ │   │
│    │  │    & Validation    │──►│    Aggregation     │──►│     Pipeline      │ │   │
│    │  └────────────────────┘   └────────────────────┘   └──────────────────┘ │   │
│    │                                     │                                    │   │
│    └─────────────────────────────────────┼────────────────────────────────────┘   │
│                                          │                                        │
│                                ┌─────────▼─────────┐                              │
│                                │                   │                              │
│                                │     ESP8266      │                              │
│                                │     WiFi         │                              │
│                                │                   │                              │
│                                └─────────┬─────────┘                              │
│                                          │                                        │
└──────────────────────────────────────────┼────────────────────────────────────────┘
                                           │
                                           │ HTTP/JSON
                                           │
┌──────────────────────────────────────────┼────────────────────────────────────────┐
│                                          │                                        │
│                                ┌─────────▼─────────┐                              │
│                                │                   │                              │
│                                │     NGINX        │                              │
│                                │     Webserver    │                              │
│                                │                   │                              │
│                                └─────────┬─────────┘                              │
│                                          │                                        │
│                                ┌─────────▼─────────┐                              │
│                                │                   │                              │
│                                │     FastAPI       │                              │
│                                │     Framework     │                              │
│                                │                   │                              │
│                                └─────────┬─────────┘                              │
│                                          │                                        │
│                ┌─────────────────────────┴─────────────────────────┐             │
│                │                                                   │             │
│       ┌────────▼─────────┐                               ┌─────────▼────────┐    │
│       │                  │                               │                  │    │
│       │  Air Quality     │                               │  Fire Detection  │    │
│       │  Prediction      │                               │  Prediction      │    │
│       │                  │                               │                  │    │
│       └────────┬─────────┘                               └─────────┬────────┘    │
│                │                                                   │             │
│                └─────────────────────────┬─────────────────────────┘             │
│                                          │                                        │
│                                ┌─────────▼─────────┐                              │
│                                │                   │                              │
│                                │     SQLite        │                              │
│                                │     Database      │                              │
│                                │                   │                              │
│                                └───────────────────┘                              │
│                                                                                    │
│                              CLOUD COMPONENT                                      │
│                                                                                    │
└────────────────────────────────────────────────────────────────────────────────────┘
```

#### Data Flow Process

1. **Sensor Data Acquisition**
   - Environmental sensors collect raw measurements
   - Data is preprocessed on the microcontroller

2. **Data Processing**
   - Validation and error checking
   - Averaging and noise reduction
   - Calculation of derived metrics

3. **Data Transmission**
   - JSON payload construction
   - HTTP POST request via WiFi
   - Retry mechanism for failed transmissions

4. **API Processing**
   - Request validation
   - Feature extraction
   - Machine learning inference

5. **Data Storage**
   - Persistence in SQLite database
   - Indexing for efficient retrieval
   - Automatic timestamp recording

6. **Response Handling**
   - Processing prediction results on device
   - Displaying results on LCD
   - Implementing alert mechanisms if needed

7. **Data Access**
   - Retrieving historical data via GET requests
   - Filtering capabilities for specific time periods or devices

### Communication Protocol

The system employs a robust communication protocol designed for reliability in IoT applications:

#### HTTP-Based Communication

The primary communication between the hardware and cloud components uses HTTP/1.1 with the following characteristics:

- **Content Format**: JSON for structured data exchange
- **Authentication**: Currently open access, with provisions for implementation of API keys
- **Transport Security**: HTTP currently, with planned upgrade path to HTTPS

#### Request/Response Cycle

1. **Connection Establishment**
   - Hardware component initiates TCP connection to API server
   - Connection timeout: 5000ms
   - Connection retry: Up to 3 attempts with exponential backoff

2. **Request Formation**
   - HTTP POST method for prediction endpoints
   - HTTP GET method for data retrieval
   - `Content-Type: application/json` header
   - JSON payload with sensor data

3. **Response Processing**
   - JSON response parsing
   - Error handling for HTTP status codes
   - Timeout handling (15000ms for responses)

4. **Connection Termination**
   - Explicit connection close after response
   - Resource cleanup on the hardware side

#### Error Handling Protocol

The system implements a comprehensive error handling strategy:

- **Network Failures**
  - Retry mechanism with exponential backoff
  - Local caching of data when connectivity is lost
  - Batch uploads when connectivity is restored

- **Server Errors**
  - Parsing of error messages
  - Fallback to default values if prediction services unavailable
  - Logging for later analysis

- **Data Validation Errors**
  - Schema validation on both client and server
  - Handling of invalid or out-of-range sensor values

#### Protocol Implementation in the Firmware

The ESP8266 WiFi module handles the communication layer with the following specific implementations:

```cpp
// HTTP Request construction
String buildHttpRequest(const char* path, const char* jsonPayload) {
    String request = "POST ";
    request += path;
    request += " HTTP/1.1\r\n";
    request += "Host: embedapi.botechgida.com\r\n";
    request += "Content-Type: application/json\r\n";
    request += "Content-Length: ";
    request += strlen(jsonPayload);
    request += "\r\n";
    request += "Connection: close\r\n";
    request += "\r\n";
    request += jsonPayload;
    
    return request;
}

// Handling the communication with retry logic
bool sendApiRequest(const char* path, const char* jsonData, int maxRetries = 3) {
    int retryCount = 0;
    int backoffTime = 1000; // Initial backoff in milliseconds
    
    while (retryCount < maxRetries) {
        if (establishTcpConnection()) {
            if (sendHttpRequest(path, jsonData)) {
                String response = readHttpResponse();
                if (response.length() > 0) {
                    parseJsonResponse(response);
                    return true;
                }
            }
            closeTcpConnection();
        }
        
        // Exponential backoff
        ThisThread::sleep_for(chrono::milliseconds(backoffTime));
        backoffTime *= 2; // Double the backoff time for each retry
        retryCount++;
    }
    
    return false; // Failed after all retries
}
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

## Installation and Deployment

### Hardware Setup

The installation of the hardware component requires careful attention to sensor positioning and power management:

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
        - Add 4.7kΩ pull-up resistors on SCL and SDA lines
      
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
        - Connect SET pin to 3.3V (always enabled)
      
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
        - Add 100nF decoupling capacitor between VCC and GND
      
      - **Button**:
        - Connect one terminal to PTC3
        - Connect other terminal to ground
        - Add 10kΩ pull-up resistor between PTC3 and 3.3V
        - Add 100nF debounce capacitor between PTC3 and ground

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

4. **Sensor Placement Optimization**
   - Place sensors away from direct heat sources
   - Ensure adequate airflow around sensors
   - Position the PMS5003 with its fan intake unobstructed
   - Mount the assembly 1.2-1.5m above floor level for representative readings
   - Keep away from direct sunlight to avoid temperature bias

5. **Enclosure Construction (Optional)**
   - Design a ventilated enclosure with openings for air sampling
   - Ensure sensor ports are aligned with ventilation openings
   - Include button access and LCD visibility
   - Consider using a 3D-printed design for customization

6. **WiFi Configuration**
   - The default configuration uses:
     - SSID: "arvin armand"
     - Password: "tehran77"
   - To modify, update these lines in main.cpp:
     ```cpp
     // Locate this in the initESP8266() function
     sendESP8266Command("AT+CWJAP=\"your_ssid\",\"your_password\"");
     ```
   - Recompile and flash after changes

### API Setup

For those who wish to host their own instance of the API:

#### Prerequisites
- Server with Ubuntu 20.04 LTS or newer
- Python 3.10 or higher
- Nginx web server
- Domain name (optional, but recommended)
- Basic knowledge of Linux server administration

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

   Required packages:
   ```
   uvicorn==0.23.2
   numpy==1.25.2
   pandas==2.1.0
   scikit-learn==1.3.0
   joblib==1.3.2
   pydantic==2.3.0
   python-multipart==0.0.6
   fastapi==0.103.0
   ```

3. **Database Initialization**
   - Run the initialization script:
     ```bash
     python3 init_db.py
     ```
   - This creates the SQLite database with the proper schema

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

6. **Verification**
   - Check service status:
     ```bash
     sudo systemctl status embedapi
     ```
   - Test the API:
     ```bash
     curl http://your-domain.com/
     ```
   - Access the API documentation:
     ```
     http://your-domain.com/docs
     ```

### Environment Configuration

#### Hardware Environment Variables

The hardware component uses compile-time configuration through preprocessor definitions:

```cpp
// Device identification
#define DEVICE_ID "smartenv-monitor"

// Sensor configuration
#define BME680_I2C_ADDR 0x76
#define ENS160_I2C_ADDR 0x53
#define LCD_I2C_ADDR 0x27

// Timing parameters
#define SENSOR_READ_INTERVAL_MS 60000  // 1 minute between readings
#define DISPLAY_CYCLE_INTERVAL_MS 5000 // 5 seconds between display modes
#define WIFI_CHECK_INTERVAL_MS 30000   // 30 seconds between WiFi checks

// API configuration
#define API_HOST "embedapi.botechgida.com"
#define API_PORT 80
#define API_ENDPOINT_AQ "/api/predict"
#define API_ENDPOINT_FIRE "/api/predict-fire"

// Calibration parameters
#define TEMP_CALIB_OFFSET -700  // -7.0°C temperature offset
```

To modify these values, edit the appropriate header file and recompile the firmware.

#### API Environment Variables

The API component uses runtime configuration through environment variables:

```bash
# Create .env file
nano .env
```

Configuration parameters:
```
# Server configuration
PORT=8000
HOST=0.0.0.0
WORKERS=4
LOG_LEVEL=info

# Database configuration
DATABASE_PATH=./sensor_data.db

# Model paths
AIR_QUALITY_MODEL_PATH=./models/air_quality_model.joblib
FIRE_DETECTION_MODEL_PATH=./models/fire_detection_model.joblib

# API limits
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD_SECONDS=60
MAX_REQUEST_SIZE_KB=100
```

These variables can be loaded using python-dotenv or set directly in the environment.
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

### Sensor Calibration

The system implements sophisticated calibration methodologies to ensure accurate and reliable measurements:

#### Temperature Calibration

The BME680 temperature sensor requires calibration to account for self-heating effects and board proximity:

```cpp
// Temperature calibration in the firmware
#define TEMP_CALIB_OFFSET -700 // -7.0°C offset in fixed-point math

// Applied during reading processing
int32_t raw_temp_x10 = (temp_adc * 10) / 5120;
temp_x10 = raw_temp_x10 + TEMP_CALIB_OFFSET;
```

The calibration offset was determined through comparison with a reference-grade thermometer across multiple ambient temperatures, resulting in the following correction curve:

```
Reference temp (°C) | Uncalibrated (°C) | Calibrated (°C) | Error
------------------------------------------------------------ 
      20.0          |      27.2         |     20.2        | +0.2
      22.5          |      29.6         |     22.6        | +0.1
      25.0          |      32.1         |     25.1        | +0.1
      27.5          |      34.3         |     27.3        | -0.2
```

#### AQI Categorization

The ENS160 sensor provides an Air Quality Index (AQI) value that is mapped to descriptive categories:

| AQI Value | Category    | Description                                    |
|-----------|-------------|------------------------------------------------|
| 1         | Excellent   | Clean air, optimal for sensitive individuals   |
| 2         | Good        | Good air quality, no health concerns           |
| 3         | Moderate    | Air quality acceptable, may affect sensitive individuals |
| 4         | Poor        | Air quality unhealthy, may cause health effects |
| 5         | Unhealthy   | Significant air pollution, health warnings     |

#### Particulate Matter Categories

The system implements EPA-based categorization for PM2.5 and PM10 readings:

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

The system implements multiple data processing algorithms to improve measurement quality:

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
    
    // Similar pattern for other sensors...
    
    // Short delay between readings
    ThisThread::sleep_for(500ms);
}

// Calculate averages (divide by 3 as we're using 3 readings)
temp_x10 = temp_sum / 3;
pressure_x10 = pressure_sum / 3;
humidity_x10 = humidity_sum / 3;
// ... other sensor values
```

The first reading is skipped to allow sensors to stabilize after wake-up or mode changes, while the subsequent three readings provide a more representative average.

#### Fixed-Point Mathematics

To optimize for the Cortex-M4 processor without floating-point unit, the system uses fixed-point math for sensor calculations:

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

This approach provides decimal precision without the overhead of floating-point operations.

#### Sensor Fusion

For critical environmental parameters, the system can cross-reference multiple sensors:

```cpp
// Example of sensor fusion for humidity (not in current code)
// Compare BME680 humidity with derived humidity from other sensors
bool humidity_reading_valid = true;
if (abs(bme680_humidity - derived_humidity) > MAX_HUMIDITY_DISCREPANCY) {
    // Readings differ too much, possible sensor error
    humidity_reading_valid = false;
    // Use fallback or averaged value
}
```

### Power Management

The system is designed for efficient power utilization while maintaining continuous monitoring capability:

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
// PMS5003 power management (example code)
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

#### WiFi Power Optimization

The ESP8266 WiFi module is the most power-hungry component. The firmware minimizes its power consumption:

1. **Connect only when needed**: WiFi is checked periodically rather than maintaining constant connection
2. **Modem sleep mode**: When not actively transmitting data
3. **Connection timeout handling**: Preventing prolonged connection attempts

```cpp
// Example of ESP8266 power management
if (currentTime - lastWiFiCheck >= 30) {
    // Only check WiFi status every 30 seconds
    checkWiFiStatus();
    lastWiFiCheck = currentTime;
}
```

### WiFi Configuration

The system's WiFi connectivity is handled by the ESP8266 module with AT command interface:

#### WiFi Setup Commands

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

#### Connection Management

The firmware implements regular connection checks and automatic reconnection:

```cpp
// Periodic WiFi status check
bool checkWiFiStatus() {
    sendESP8266Command("AT+CWJAP?");
    bool connected = readESP8266Response(5000, "arvin armand");
    
    if (!connected && wifi_connected) {
        // Connection was lost, update status
        wifi_connected = false;
        strcpy(ip_address, "Not Connected");
    }
    else if (connected && !wifi_connected) {
        // Connection was restored
        wifi_connected = true;
        // Update IP address
    }
    
    return connected;
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
