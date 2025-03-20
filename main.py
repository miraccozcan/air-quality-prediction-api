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

# Define input data models for Air Quality API


class AirQualityData(BaseModel):
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

# For the Air Quality Model, we'll implement a simplified version
# since you already have this working in your original code


@app.get("/")
def read_root():
    api_status = {
        "message": "Air Quality and Fire Detection API",
        "status": "running",
        "endpoints": {
            "air_quality": "/api/predict",
            "fire_detection": "/api/predict-fire"
        },
        "fire_model_loaded": fire_model is not None,
    }
    return api_status


@app.post("/api/predict")
async def predict_air_quality(data: AirQualityData):
    """
    Air Quality prediction endpoint.
    This is your existing endpoint that already works.
    The implementation would go here but we're assuming 
    it's working correctly in your current setup.
    """
    # Implement your working air quality prediction here
    # This is a placeholder response - replace with your actual implementation
    return {
        "status": 0,  # 0 for safe, 1 for unsafe
        "is_unsafe": False,
        "probability": 0.12,
        "message": "Air quality is normal"
    }


@app.post("/api/predict-fire")
async def predict_fire(data: FireDetectionInput):
    """
    Fire detection prediction endpoint.
    This is the endpoint that wasn't working before.
    """
    try:
        # Check if model is available
        if fire_model is None or fire_scaler is None:
            raise HTTPException(
                status_code=500,
                detail="Fire detection model not available. Please check server logs for details."
            )

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

        # Return the prediction result
        return {
            "fire_alarm": int(prediction[0]),
            "is_fire_detected": bool(prediction[0] == 1),
            "probability": float(probability),
            "message": "Fire detected!" if prediction[0] == 1 else "No fire detected"
        }

    except Exception as e:
        # Provide detailed error message
        raise HTTPException(
            status_code=500,
            detail=f"Error making fire prediction: {str(e)}"
        )
