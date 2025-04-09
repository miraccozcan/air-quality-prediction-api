from fastapi.middleware.cors import CORSMiddleware
import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
import joblib
import sqlite3
from datetime import datetime
import pytz
from contextlib import contextmanager

app = FastAPI()

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create models directory if it doesn't exist
os.makedirs('models', exist_ok=True)

# Database connection helper


@contextmanager
def get_db_connection():
    conn = sqlite3.connect('sensor_data.db')
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# Database setup function


def setup_database():
    conn = sqlite3.connect('sensor_data.db')
    cursor = conn.cursor()

    # Air Quality Data table
    cursor.execute('''
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
    )
    ''')

    # Fire Detection Data table
    cursor.execute('''
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
    )
    ''')

    conn.commit()
    conn.close()
    print("✅ Database setup complete")

# Define input data models for Air Quality API


class AirQualityData(BaseModel):
    device_id: str = "unknown"
    co2: float
    pm2_5: float
    pm10: float
    temperature: float
    humidity: float
    co2_category: int = 0
    pm2_5_category: int = 0
    pm10_category: int = 0
    hour: int = 0
    day_of_week: int = 0
    is_weekend: int = 0

# Define input data model for Fire Detection API


class FireDetectionInput(BaseModel):
    device_id: str = "unknown"
    temperature: float
    humidity: float
    tvoc: float
    eco2: float
    raw_h2: float
    raw_ethanol: float
    pressure: float
    pm1_0: float
    pm2_5: float
    nc0_5: float
    nc1_0: float
    nc2_5: float

# Function to train or load the fire detection model


def setup_fire_detection_model():
    # First try to load pre-trained models if they exist
    model_path = 'models/fire_detection_model.pkl'
    scaler_path = 'models/fire_detection_scaler.pkl'

    if os.path.exists(model_path) and os.path.exists(scaler_path):
        try:
            print("Loading pre-trained fire detection model and scaler...")
            model = joblib.load(model_path)
            scaler = joblib.load(scaler_path)
            print("✅ Fire detection model loaded successfully!")
            return model, scaler
        except Exception as e:
            print(f"Error loading pre-trained model: {e}")

    # If loading failed or models don't exist, try to train a new model
    try:
        print("Training new fire detection model...")

        # Load the dataset
        csv_path = "smoke_detection_iot.csv"
        if not os.path.exists(csv_path):
            print(f"❌ Dataset not found at {csv_path}")
            return None, None

        df = pd.read_csv(csv_path)

        # Clean the dataset
        columns_to_drop = ['Unnamed: 0', 'UTC', 'CNT']
        df = df.drop(
            columns=[col for col in columns_to_drop if col in df.columns])

        # Define features and target
        X = df.drop(columns=['Fire Alarm'])
        y = df['Fire Alarm']

        # Split the dataset
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42)

        # Scale the features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Train the model
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train_scaled, y_train)

        # Evaluate the model
        y_pred = model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"Model accuracy: {accuracy:.4f}")

        # Save the trained model and scaler
        joblib.dump(model, model_path)
        joblib.dump(scaler, scaler_path)

        print("✅ Fire detection model trained and saved successfully!")
        return model, scaler

    except Exception as e:
        print(f"❌ Error training fire detection model: {e}")
        return None, None


# Load or train the fire detection model
fire_model, fire_scaler = setup_fire_detection_model()

# Load air quality model and scaler
try:
    air_quality_model = joblib.load('models/best_model.pkl')
    air_quality_scaler = joblib.load('models/scaler.pkl')
    print("✅ Air quality model and scaler loaded successfully!")
except Exception as e:
    print(f"❌ Error loading air quality model: {e}")
    air_quality_model = None
    air_quality_scaler = None


@app.get("/")
def read_root():
    api_status = {
        "message": "Air Quality and Fire Detection API",
        "status": "running",
        "endpoints": {
            "air_quality": "/api/predict",
            "fire_detection": "/api/predict-fire",
            "air_quality_data": "/api/data/air-quality",
            "fire_detection_data": "/api/data/fire-detection"
        },
        "models": {
            "fire_model_loaded": fire_model is not None,
            "air_quality_model_loaded": air_quality_model is not None
        }
    }
    return api_status


@app.post("/api/predict")
async def predict_air_quality(data: AirQualityData):
    """
    Air Quality prediction endpoint with data logging.
    """
    try:
        # Get current time with timezone
        timestamp = datetime.now(pytz.UTC).isoformat()

        # Make prediction if model is available
        if air_quality_model is not None and air_quality_scaler is not None:
            # Create feature array
            features = np.array([
                data.co2, data.pm2_5, data.pm10, data.temperature, data.humidity,
                data.co2_category, data.pm2_5_category, data.pm10_category,
                data.hour, data.day_of_week, data.is_weekend
            ]).reshape(1, -1)

            # Scale features
            scaled_features = air_quality_scaler.transform(features)

            # Make prediction
            status = int(air_quality_model.predict(scaled_features)[0])
            probability = float(
                air_quality_model.predict_proba(scaled_features)[0][1])
        else:
            # Fallback to placeholder values if model not available
            print("Warning: Air quality model not available, using fallback values")
            status = 0  # 0 for safe, 1 for unsafe
            probability = 0.12

        # Save to database
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO air_quality_data 
            (timestamp, device_id, co2, pm2_5, pm10, temperature, humidity, 
             co2_category, pm2_5_category, pm10_category, hour, day_of_week, is_weekend,
             prediction, probability) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                timestamp, data.device_id, data.co2, data.pm2_5, data.pm10,
                data.temperature, data.humidity, data.co2_category,
                data.pm2_5_category, data.pm10_category, data.hour, data.day_of_week,
                data.is_weekend, status, probability
            ))
            conn.commit()

        # Return prediction result
        return {
            "status": status,
            "is_unsafe": bool(status == 1),
            "probability": probability,
            "message": "Unsafe air quality detected!" if status == 1 else "Air quality is normal",
            "timestamp": timestamp
        }
    except Exception as e:
        # Provide detailed error message
        raise HTTPException(
            status_code=500,
            detail=f"Error processing air quality prediction: {str(e)}"
        )


@app.post("/api/predict-fire")
async def predict_fire(data: FireDetectionInput):
    """
    Fire detection prediction endpoint with data logging.
    """
    try:
        # Check if model is available
        if fire_model is None or fire_scaler is None:
            raise HTTPException(
                status_code=500,
                detail="Fire detection model not available. Please check server logs for details."
            )

        # Get current time with timezone
        timestamp = datetime.now(pytz.UTC).isoformat()

        # Prepare the input data for prediction
        input_data = np.array([[
            data.temperature, data.humidity, data.tvoc, data.eco2,
            data.raw_h2, data.raw_ethanol, data.pressure, data.pm1_0,
            data.pm2_5, data.nc0_5, data.nc1_0, data.nc2_5
        ]])

        # Scale the input data
        scaled_data = fire_scaler.transform(input_data)

        # Make prediction
        prediction = fire_model.predict(scaled_data)

        # Get prediction probability
        probability = fire_model.predict_proba(scaled_data)[0][1]

        # Save to database
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO fire_detection_data 
            (timestamp, device_id, temperature, humidity, tvoc, eco2, raw_h2, raw_ethanol, 
             pressure, pm1_0, pm2_5, nc0_5, nc1_0, nc2_5, prediction, probability) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                timestamp, data.device_id, data.temperature, data.humidity, data.tvoc,
                data.eco2, data.raw_h2, data.raw_ethanol, data.pressure, data.pm1_0,
                data.pm2_5, data.nc0_5, data.nc1_0, data.nc2_5, int(
                    prediction[0]), float(probability)
            ))
            conn.commit()

        # Return the prediction result
        return {
            "fire_alarm": int(prediction[0]),
            "is_fire_detected": bool(prediction[0] == 1),
            "probability": float(probability),
            "message": "Fire detected!" if prediction[0] == 1 else "No fire detected",
            "timestamp": timestamp
        }

    except Exception as e:
        # Provide detailed error message
        raise HTTPException(
            status_code=500,
            detail=f"Error making fire prediction: {str(e)}"
        )


@app.get("/api/data/air-quality")
async def get_air_quality_data(limit: int = 100, device_id: str = None):
    """
    Retrieve stored air quality data
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            if device_id:
                cursor.execute(
                    "SELECT * FROM air_quality_data WHERE device_id = ? ORDER BY timestamp DESC LIMIT ?",
                    (device_id, limit)
                )
            else:
                cursor.execute(
                    "SELECT * FROM air_quality_data ORDER BY timestamp DESC LIMIT ?",
                    (limit,)
                )

            rows = cursor.fetchall()

        # Convert to list of dicts
        data = [dict(row) for row in rows]
        return {"data": data, "count": len(data)}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving air quality data: {str(e)}"
        )


@app.get("/api/data/fire-detection")
async def get_fire_detection_data(limit: int = 100, device_id: str = None):
    """
    Retrieve stored fire detection data
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            if device_id:
                cursor.execute(
                    "SELECT * FROM fire_detection_data WHERE device_id = ? ORDER BY timestamp DESC LIMIT ?",
                    (device_id, limit)
                )
            else:
                cursor.execute(
                    "SELECT * FROM fire_detection_data ORDER BY timestamp DESC LIMIT ?",
                    (limit,)
                )

            rows = cursor.fetchall()

        # Convert to list of dicts
        data = [dict(row) for row in rows]
        return {"data": data, "count": len(data)}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving fire detection data: {str(e)}"
        )

# Initialize the database on startup


@app.on_event("startup")
async def startup_event():
    setup_database()
    print("API started and database initialized")
