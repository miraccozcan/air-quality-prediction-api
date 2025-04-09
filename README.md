# Air Quality and Fire Detection API

This document provides comprehensive documentation for the Air Quality and Fire Detection API system. The API serves predictions from machine learning models trained to detect unsafe air quality conditions and potential fire hazards based on sensor data.

## Overview

The system consists of:

1. **Air Quality Model**: A RandomForest classifier trained to detect unsafe air quality conditions
2. **Fire Detection Model**: A RandomForest classifier trained to detect potential fire conditions
3. **REST API**: FastAPI endpoints to serve predictions and store sensor data
4. **Database**: SQLite database that stores all sensor readings and predictions

The API is designed to be used by IoT devices and microcontrollers that collect environmental sensor data, allowing them to leverage sophisticated machine learning models without requiring significant on-device computing power.

## API Endpoints

### Base URL

```
http://embedapi.botechgida.com
```

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API status and information |
| `/api/predict` | POST | Air quality prediction |
| `/api/predict-fire` | POST | Fire detection prediction |
| `/api/data/air-quality` | GET | Retrieve air quality data |
| `/api/data/fire-detection` | GET | Retrieve fire detection data |
| `/docs` | GET | API documentation (Swagger UI) |

## Air Quality Prediction

### Request

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

### Response

**Example Response:**

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

## Fire Detection Prediction

### Request

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

### Response

**Example Response:**

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

## Data Retrieval

### Air Quality Data

**Endpoint:** `/api/data/air-quality`

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

### Fire Detection Data

**Endpoint:** `/api/data/fire-detection`

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

## Machine Learning Models

### Air Quality Model

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

### Fire Detection Model

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

## Implementation Examples

### Air Quality API Request (Arduino/ESP8266)

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

### Fire Detection API Request (Arduino/ESP8266)

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

## Test Cases

### Air Quality Test Cases

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

### Fire Detection Test Cases

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

## Deployment Information

The API is deployed on a VPS with the following configuration:

- Server: Ubuntu Linux
- Web Server: Nginx
- Application Server: Uvicorn
- Python Version: 3.10
- Domain: embedapi.botechgida.com
- Port: 80 (HTTP)

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

## Troubleshooting

### Common Issues

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

## License and Attribution

This API system was developed as part of an environmental monitoring solution. The models are trained on publicly available datasets, including:

1. Air Quality Dataset: Numerically_Encoded_Air_Quality_Dataset.csv
2. Fire Detection Dataset: smoke_detection_iot.csv

For support and further information, please contact the system administrator.
