from fastapi.middleware.cors import CORSMiddleware
import os
import numpy as np
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


# Try to load the fire detection model and scaler
fire_model = None
fire_scaler = None

# Check for pre-trained models
model_path = 'models/fire_detection_model.pkl'
scaler_path = 'models/fire_detection_scaler.pkl'

if os.path.exists(model_path) and os.path.exists(scaler_path):
    try:
        fire_model = joblib.load(model_path)
        fire_scaler = joblib.load(scaler_path)
        print("✅ Fire detection model loaded successfully!")
    except Exception as e:
        print(f"❌ Error loading fire detection model: {e}")
else:
    print("❌ Fire detection model files not found")


@app.get("/")
def read_root():
    api_status = {
        "message": "Air Quality and Fire Detection API",
        "status": "running",
        "endpoints": {
            "air_quality": "/api/predict",
            "fire_detection": "/api/predict-fire"
        },
        "fire_model_loaded": fire_model is not None
    }
    return api_status


@app.post("/api/predict")
async def predict_air_quality(data: AirQualityData):
    """
    Air Quality prediction endpoint that properly processes the input data.
    """
    try:
        # Create a feature array from the input data
        features = np.array([[
            data.co2, data.pm2_5, data.pm10, data.temperature, data.humidity,
            data.co2_category, data.pm2_5_category, data.pm10_category,
            data.hour, data.day_of_week, data.is_weekend
        ]])
        
        # Simple rule-based prediction
        is_unsafe = False
        probability = 0.05  # Default low probability
        
        # Check conditions that would indicate unsafe air quality
        if data.co2 > 600:
            is_unsafe = True
            probability = max(probability, 0.7)
        
        if data.pm10 > 100:
            is_unsafe = True
            probability = max(probability, 0.8)
            
        if data.pm2_5 > 25:
            is_unsafe = True
            probability = max(probability, 0.75)
            
        if data.pm2_5_category > 0 or data.pm10_category > 0 or data.co2_category > 0:
            is_unsafe = True
            probability = max(probability, 0.65)
        
        # Create the response
        return {
            "status": 1 if is_unsafe else 0,
            "is_unsafe": is_unsafe,
            "probability": probability,
            "message": "Unsafe air quality detected!" if is_unsafe else "Air quality is normal"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/predict-fire")
async def predict_fire(data: FireDetectionInput):
    """
    Fire detection prediction endpoint.
    """
    try:
        # Check if model is available
        if fire_model is None or fire_scaler is None:
            return {
                "fire_alarm": 0,
                "is_fire_detected": False,
                "probability": 0.0,
                "message": "Fire detection model is not available."
            }
        
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
        # Return a response even if an error occurs
        return {
            "fire_alarm": 0,
            "is_fire_detected": False,
            "probability": 0.0,
            "message": f"Error: {str(e)}"
        }
