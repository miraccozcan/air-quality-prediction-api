from fastapi.middleware.cors import CORSMiddleware
import os
import numpy as np
import joblib
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
i  # main.py (this is the file Vercel will use as entry point)

app = FastAPI()

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define input data model


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


# Load models
model_path = os.path.join(os.path.dirname(__file__), "models/best_model.pkl")
scaler_path = os.path.join(os.path.dirname(__file__), "models/scaler.pkl")

try:
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
except Exception as e:
    # For simplicity, we'll use a fallback function if model loading fails
    print(f"Error loading model: {e}")
    model = None
    scaler = None

# Fallback prediction function


def fallback_predict(data):
    # Simple threshold-based prediction
    if data.co2 > 680 or data.pm10 > 125 or data.pm2_5_category > 0:
        return 1, 0.9  # Unsafe with 90% confidence
    return 0, 0.1  # Safe with 10% confidence of being unsafe


@app.get("/")
def read_root():
    return {"message": "Air Quality Prediction API is running"}


@app.post("/api/predict")
async def predict(data: AirQualityData):
    try:
        # Use fallback if model couldn't be loaded
        if model is None or scaler is None:
            status, probability = fallback_predict(data)
        else:
            # Prepare features
            features = np.array([
                data.co2, data.pm2_5, data.pm10,
                data.temperature, data.humidity,
                data.co2_category, data.pm2_5_category, data.pm10_category,
                data.hour, data.day_of_week, data.is_weekend
            ]).reshape(1, -1)

            # Scale features and predict
            features_scaled = scaler.transform(features)
            status = int(model.predict(features_scaled)[0])
            probability = float(model.predict_proba(features_scaled)[0][1])

        # Return prediction
        return {
            "status": status,
            "is_unsafe": bool(status == 1),
            "probability": probability,
            "message": "Unsafe air quality detected!" if status == 1 else "Air quality is normal"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
