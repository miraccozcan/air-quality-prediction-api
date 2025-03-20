from fastapi.middleware.cors import CORSMiddleware
import os
import numpy as np
import joblib
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException

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


# Load models
model_path = os.path.join(os.path.dirname(__file__), "models/best_model.pkl")
scaler_path = os.path.join(os.path.dirname(__file__), "models/scaler.pkl")
fire_model_path = os.path.join(os.path.dirname(
    __file__), "models/fire_detection_model.pkl")
fire_scaler_path = os.path.join(os.path.dirname(
    __file__), "models/fire_detection_scaler.pkl")

try:
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    fire_model = joblib.load(fire_model_path)
    fire_scaler = joblib.load(fire_scaler_path)
except Exception as e:
    print(f"Error loading model: {e}")
    model = None
    scaler = None
    fire_model = None
    fire_scaler = None

# Fallback prediction function


def fallback_predict(data):
    if data.co2 > 680 or data.pm10 > 125 or data.pm2_5_category > 0:
        return 1, 0.9
    return 0, 0.1


@app.get("/")
def read_root():
    return {"message": "Air Quality and Fire Detection API is running"}


@app.post("/api/predict")
async def predict(data: AirQualityData):
    try:
        if model is None or scaler is None:
            status, probability = fallback_predict(data)
        else:
            features = np.array([
                data.co2, data.pm2_5, data.pm10,
                data.temperature, data.humidity,
                data.co2_category, data.pm2_5_category, data.pm10_category,
                data.hour, data.day_of_week, data.is_weekend
            ]).reshape(1, -1)

            features_scaled = scaler.transform(features)
            status = int(model.predict(features_scaled)[0])
            probability = float(model.predict_proba(features_scaled)[0][1])

        return {
            "status": status,
            "is_unsafe": bool(status == 1),
            "probability": probability,
            "message": "Unsafe air quality detected!" if status == 1 else "Air quality is normal"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/predict-fire")
async def predict_fire(data: FireDetectionInput):
    try:
        if fire_model is None or fire_scaler is None:
            raise HTTPException(
                status_code=500, detail="Fire detection model is not available.")

        input_data = np.array([[
            data.temperature, data.humidity, data.tvoc, data.eco2, data.raw_h2,
            data.raw_ethanol, data.pressure, data.pm1_0, data.pm2_5, data.nc0_5,
            data.nc1_0, data.nc2_5
        ]])
        scaled_data = fire_scaler.transform(input_data)
        prediction = fire_model.predict(scaled_data)
        return {"fire_alarm": int(prediction[0])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
