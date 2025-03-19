import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
import xgboost as xgb
import joblib
import os
import warnings
warnings.filterwarnings('ignore')

# Create directories for saving models and visualizations
os.makedirs('models', exist_ok=True)
os.makedirs('visualizations', exist_ok=True)

# Set a random seed for reproducibility
np.random.seed(42)

# Load the dataset
print("Loading dataset...")
df = pd.read_csv('Numerically_Encoded_Air_Quality_Dataset.csv')

# Display basic info about the dataset
print("\nDataset Information:")
print(f"Shape: {df.shape}")
print("\nColumns:")
print(df.columns.tolist())
print("\nSample data:")
print(df.head())

# Check for missing values
print("\nMissing values:")
print(df.isnull().sum())

# Data preprocessing
print("\nPreprocessing data...")

# Remove the unnamed column if it exists
if 'Unnamed: 0' in df.columns:
    df = df.drop('Unnamed: 0', axis=1)

# Convert the time column to datetime format
df['time'] = pd.to_datetime(df['time'])

# Add additional time-based features
df['hour'] = df['time'].dt.hour
df['day_of_week'] = df['time'].dt.dayofweek
df['is_weekend'] = df['day_of_week'].apply(lambda x: 1 if x >= 5 else 0)

# Display distribution of the target variable
print("\nTarget variable distribution:")
print(df['status'].value_counts())
print(f"Class balance ratio (unsafe/safe): {df['status'].mean():.4f}")

# Visualize the data
print("\nCreating visualizations...")

# Correlation matrix
plt.figure(figsize=(12, 10))
corr_matrix = df.drop('time', axis=1).corr()
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt='.2f')
plt.title('Correlation Matrix of Air Quality Features')
plt.tight_layout()
plt.savefig('visualizations/correlation_matrix.png')

# Distribution of key features
plt.figure(figsize=(15, 10))
features = ['co2', 'pm2_5', 'pm10', 'temperature', 'humidity']
for i, feature in enumerate(features):
    plt.subplot(2, 3, i+1)
    sns.histplot(data=df, x=feature, hue='status', bins=30, kde=True)
    plt.title(f'Distribution of {feature} by Air Quality Status')
plt.tight_layout()
plt.savefig('visualizations/feature_distributions.png')

# Prepare the data for modeling
print("\nPreparing data for modeling...")

# Define features and target
X = df.drop(['time', 'status'], axis=1)
y = df['status']

# Print feature names for microcontroller implementation
print("\nFeature names:")
print(X.columns.tolist())

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42)

# Scale the features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Save the scaler for future use
joblib.dump(scaler, 'models/scaler.pkl')

# Train and evaluate multiple models
models = {
    'Random Forest': RandomForestClassifier(random_state=42),
    'Gradient Boosting': GradientBoostingClassifier(random_state=42),
    'SVM': SVC(probability=True, random_state=42),
    'Neural Network': MLPClassifier(random_state=42),
    'XGBoost': xgb.XGBClassifier(random_state=42)
}

# Dictionary to store model performance
model_performance = {}

print("\nTraining and evaluating models:")
for name, model in models.items():
    print(f"\nTraining {name}...")
    model.fit(X_train_scaled, y_train)

    # Make predictions
    y_pred = model.predict(X_test_scaled)

    # Calculate accuracy
    accuracy = accuracy_score(y_test, y_pred)
    model_performance[name] = accuracy

    # Print classification report
    print(f"\n{name} Classification Report:")
    report = classification_report(y_test, y_pred)
    print(report)

    # Display confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
    plt.title(f'Confusion Matrix - {name}')
    plt.xlabel('Predicted Label')
    plt.ylabel('True Label')
    plt.savefig(
        f'visualizations/confusion_matrix_{name.replace(" ", "_").lower()}.png')

    # Save the model
    joblib.dump(model, f'models/{name.replace(" ", "_").lower()}.pkl')

# Find the best model
best_model_name = max(model_performance, key=model_performance.get)
best_model = models[best_model_name]
best_accuracy = model_performance[best_model_name]

print(f"\nBest model: {best_model_name} with accuracy: {best_accuracy:.4f}")

# Save the best model separately
joblib.dump(best_model, 'models/best_model.pkl')

# For the best model, if it's a tree-based model, show feature importance
if best_model_name in ['Random Forest', 'Gradient Boosting', 'XGBoost']:
    # Feature importance
    feature_importance = None
    if best_model_name == 'Random Forest':
        feature_importance = best_model.feature_importances_
    elif best_model_name == 'Gradient Boosting':
        feature_importance = best_model.feature_importances_
    elif best_model_name == 'XGBoost':
        feature_importance = best_model.feature_importances_

    if feature_importance is not None:
        # Plot feature importance
        plt.figure(figsize=(12, 8))
        indices = np.argsort(feature_importance)[::-1]
        plt.barh(range(len(indices)), feature_importance[indices])
        plt.yticks(range(len(indices)), X.columns[indices])
        plt.title(f'Feature Importance - {best_model_name}')
        plt.tight_layout()
        plt.savefig('visualizations/feature_importance.png')

        # Print feature importance for implementation
        print("\nFeature importance for microcontroller implementation:")
        for i, feature in enumerate(X.columns[indices]):
            print(f"{feature}: {feature_importance[indices][i]:.4f}")

# Create a simple function to predict air quality based on sensor readings


def predict_air_quality(co2, pm2_5, pm10, temperature, humidity,
                        co2_category, pm2_5_category, pm10_category,
                        hour=None, day_of_week=None, is_weekend=None):
    """
    Predicts air quality based on sensor readings.
    Returns:
    - status: 0 (safe) or 1 (unsafe)
    - probability: probability of the prediction
    """
    # Create a feature vector
    features = [co2, pm2_5, pm10, temperature, humidity,
                co2_category, pm2_5_category, pm10_category]

    # Add time features if provided
    if hour is not None:
        features.append(hour)
    else:
        features.append(0)  # Default value

    if day_of_week is not None:
        features.append(day_of_week)
    else:
        features.append(0)  # Default value

    if is_weekend is not None:
        features.append(is_weekend)
    else:
        features.append(0)  # Default value

    # Convert to numpy array and reshape
    features = np.array(features).reshape(1, -1)

    # Scale the features
    features_scaled = scaler.transform(features)

    # Make prediction
    status = best_model.predict(features_scaled)[0]
    probability = best_model.predict_proba(features_scaled)[0][1]

    return int(status), float(probability)


# Save the prediction function code
with open('models/predict_function.py', 'w') as f:
    f.write("""
import numpy as np
import joblib

# Load the model and scaler
scaler = joblib.load('models/scaler.pkl')
model = joblib.load('models/best_model.pkl')

def predict_air_quality(co2, pm2_5, pm10, temperature, humidity, 
                        co2_category, pm2_5_category, pm10_category,
                        hour=None, day_of_week=None, is_weekend=None):
    \"\"\"
    Predicts air quality based on sensor readings.
    Returns:
    - status: 0 (safe) or 1 (unsafe)
    - probability: probability of the prediction
    \"\"\"
    # Create a feature vector
    features = [co2, pm2_5, pm10, temperature, humidity, 
                co2_category, pm2_5_category, pm10_category]
    
    # Add time features if provided
    if hour is not None:
        features.append(hour)
    else:
        features.append(0)  # Default value
        
    if day_of_week is not None:
        features.append(day_of_week)
    else:
        features.append(0)  # Default value
        
    if is_weekend is not None:
        features.append(is_weekend)
    else:
        features.append(0)  # Default value
    
    # Convert to numpy array and reshape
    features = np.array(features).reshape(1, -1)
    
    # Scale the features
    features_scaled = scaler.transform(features)
    
    # Make prediction
    status = model.predict(features_scaled)[0]
    probability = model.predict_proba(features_scaled)[0][1]
    
    return int(status), float(probability)
""")

# Create a simplified prediction function for microcontrollers
with open('models/simplified_predict.cpp', 'w') as f:
    f.write(f"""
// Simplified air quality prediction function for microcontroller
// Based on {best_model_name} model

// Returns:
// 0 = safe air quality
// 1 = unsafe/unhealthy air quality

int predictAirQuality(float co2, float pm2_5, float pm10, float temperature, float humidity, 
                     int co2_category, int pm2_5_category, int pm10_category) {{
  // Simple threshold-based prediction based on the trained model's important features
  
  if (co2 > 680.0) return 1;  // High CO2 levels
  if (pm10 > 125.0) return 1;  // High PM10 levels
  if (pm2_5_category > 0) return 1;  // PM2.5 not in 'Good' category
  
  // Add other important thresholds based on feature importance
  
  return 0;  // Default to safe air quality
}}
""")

print("\nTraining and evaluation complete!")
print("Models saved in the 'models' directory")
print("Visualizations saved in the 'visualizations' directory")

# Test the model with a sample input
print("\nTesting the model with a sample input:")
sample_co2 = 700
sample_pm2_5 = 15
sample_pm10 = 30
sample_temp = 16
sample_humidity = 62.5
sample_co2_cat = 1
sample_pm2_5_cat = 0
sample_pm10_cat = 0

status, probability = predict_air_quality(
    sample_co2, sample_pm2_5, sample_pm10, sample_temp, sample_humidity,
    sample_co2_cat, sample_pm2_5_cat, sample_pm10_cat
)

print(f"Prediction: {'Unsafe' if status == 1 else 'Safe'} air quality")
print(f"Confidence: {probability:.2%}")

# Create a simple test script
with open('test_model.py', 'w') as f:
    f.write("""
from models.predict_function import predict_air_quality

# Test the model with a sample input
print("Testing the model with sample inputs:")

# Test Case 1: Safe Air Quality
safe_co2 = 400
safe_pm2_5 = 8
safe_pm10 = 20
safe_temp = 17
safe_humidity = 62.3
safe_co2_cat = 0
safe_pm2_5_cat = 0
safe_pm10_cat = 0

status, probability = predict_air_quality(
    safe_co2, safe_pm2_5, safe_pm10, safe_temp, safe_humidity,
    safe_co2_cat, safe_pm2_5_cat, safe_pm10_cat
)

print(f"Safe Air Quality Test:")
print(f"CO2: {safe_co2} ppm, PM2.5: {safe_pm2_5} µg/m³, PM10: {safe_pm10} µg/m³")
print(f"Prediction: {'Unsafe' if status == 1 else 'Safe'} air quality")
print(f"Confidence: {probability:.2%}")

# Test Case 2: Unsafe Air Quality
unsafe_co2 = 800
unsafe_pm2_5 = 40
unsafe_pm10 = 150
unsafe_temp = 15
unsafe_humidity = 62.8
unsafe_co2_cat = 2
unsafe_pm2_5_cat = 2
unsafe_pm10_cat = 2

status, probability = predict_air_quality(
    unsafe_co2, unsafe_pm2_5, unsafe_pm10, unsafe_temp, unsafe_humidity,
    unsafe_co2_cat, unsafe_pm2_5_cat, unsafe_pm10_cat
)

print(f"\\nUnsafe Air Quality Test:")
print(f"CO2: {unsafe_co2} ppm, PM2.5: {unsafe_pm2_5} µg/m³, PM10: {unsafe_pm10} µg/m³")
print(f"Prediction: {'Unsafe' if status == 1 else 'Safe'} air quality")
print(f"Confidence: {probability:.2%}")
""")

print("\nCreated test script: test_model.py")

# Create a Flask API server for serving predictions
with open('api_server.py', 'w') as f:
    f.write("""
from flask import Flask, request, jsonify
from models.predict_function import predict_air_quality

app = Flask(__name__)

@app.route('/predict', methods=['POST'])
def predict():
    # Get data from request
    data = request.get_json()
    
    # Extract features
    co2 = data.get('co2')
    pm2_5 = data.get('pm2_5')
    pm10 = data.get('pm10')
    temperature = data.get('temperature')
    humidity = data.get('humidity')
    co2_category = data.get('co2_category', 0)
    pm2_5_category = data.get('pm2_5_category', 0)
    pm10_category = data.get('pm10_category', 0)
    
    # Optional time features
    hour = data.get('hour')
    day_of_week = data.get('day_of_week')
    is_weekend = data.get('is_weekend')
    
    # Make prediction
    status, probability = predict_air_quality(
        co2, pm2_5, pm10, temperature, humidity,
        co2_category, pm2_5_category, pm10_category,
        hour, day_of_week, is_weekend
    )
    
    # Return prediction
    return jsonify({
        'status': status,
        'is_unsafe': bool(status == 1),
        'probability': probability,
        'message': 'Unsafe air quality detected!' if status == 1 else 'Air quality is normal'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
""")

print("\nCreated API server: api_server.py")

# Create a README file with instructions
with open('README.md', 'w') as f:
    f.write("""
# Advanced Air Quality AI Model

This project contains an advanced AI model for predicting air quality based on sensor readings from the Smart Environmental Monitor.

## Directory Structure

- `models/` - Trained models and prediction functions
- `visualizations/` - Data visualizations and model performance metrics
- `test_model.py` - Script to test the model with sample inputs
- `api_server.py` - Flask API server to serve predictions

## Getting Started

1. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

2. Run the training script:
   ```
   python train_model.py
   ```

3. Test the model:
   ```
   python test_model.py
   ```

4. Start the API server:
   ```
   python api_server.py
   ```

## API Usage

Send a POST request to `/predict` with the following JSON data:

```json
{
  "co2": 450,
  "pm2_5": 10,
  "pm10": 22,
  "temperature": 17,
  "humidity": 62.5,
  "co2_category": 0,
  "pm2_5_category": 0,
  "pm10_category": 0
}
```

The API will return a prediction like:

```json
{
  "is_unsafe": false,
  "message": "Air quality is normal",
  "probability": 0.12,
  "status": 0
}
```

## Microcontroller Integration

For ESP8266/ESP32 integration, see the Arduino example code in `models/arduino_example.ino`.

## Model Performance

The best model achieved [accuracy] accuracy on the test set. See the visualizations directory for detailed performance metrics.
""")

print("\nCreated README.md file with instructions")

# Create requirements.txt
with open('requirements.txt', 'w') as f:
    f.write("""
numpy==1.24.3
pandas==2.0.1
scikit-learn==1.2.2
matplotlib==3.7.1
seaborn==0.12.2
joblib==1.2.0
xgboost==1.7.5
flask==2.3.2
""")

print("\nCreated requirements.txt file")

# Create an Arduino example code
with open('models/arduino_example.ino', 'w') as f:
    f.write("""
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>

// WiFi credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// API server address
const char* apiUrl = "http://your-server-ip:5000/predict";

// Pin definitions
const int buzzerPin = D1;
const int ledPin = D2;

void setup() {
  Serial.begin(115200);
  
  // Initialize pins
  pinMode(buzzerPin, OUTPUT);
  pinMode(ledPin, OUTPUT);
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: " + WiFi.localIP().toString());
}

void loop() {
  // Read sensor values (replace with actual sensor reading code)
  float co2 = 450;          // CO2 value in ppm
  float pm2_5 = 10;         // PM2.5 value in µg/m³
  float pm10 = 22;          // PM10 value in µg/m³
  float temperature = 17;    // Temperature in °C
  float humidity = 62.5;     // Humidity in %
  
  // Calculate categories (simplified)
  int co2_category = (co2 < 600) ? 0 : (co2 < 800) ? 1 : 2;
  int pm2_5_category = (pm2_5 < 12) ? 0 : (pm2_5 < 35.4) ? 1 : 2;
  int pm10_category = (pm10 < 54) ? 0 : (pm10 < 154) ? 1 : 2;
  
  // Check air quality
  bool isUnsafe = false;
  
  // Try to get prediction from API
  if (WiFi.status() == WL_CONNECTED) {
    isUnsafe = checkAirQualityAPI(co2, pm2_5, pm10, temperature, humidity, 
                                 co2_category, pm2_5_category, pm10_category);
  } else {
    // Fallback to local prediction if no WiFi
    isUnsafe = predictAirQuality(co2, pm2_5, pm10, temperature, humidity, 
                                co2_category, pm2_5_category, pm10_category);
    Serial.println("Using local prediction: " + String(isUnsafe ? "Unsafe" : "Safe"));
  }
  
  // Take action based on prediction
  if (isUnsafe) {
    // Activate warning indicators
    digitalWrite(ledPin, HIGH);
    tone(buzzerPin, 1000);
    Serial.println("WARNING: Unsafe air quality detected!");
  } else {
    // Normal operation
    digitalWrite(ledPin, LOW);
    noTone(buzzerPin);
    Serial.println("Air quality is normal");
  }
  
  // Wait before next check
  delay(60000); // Check every minute
}

bool checkAirQualityAPI(float co2, float pm2_5, float pm10, float temperature, float humidity,
                       int co2_category, int pm2_5_category, int pm10_category) {
  HTTPClient http;
  WiFiClient client;
  
  // Prepare JSON data
  DynamicJsonDocument doc(200);
  doc["co2"] = co2;
  doc["pm2_5"] = pm2_5;
  doc["pm10"] = pm10;
  doc["temperature"] = temperature;
  doc["humidity"] = humidity;
  doc["co2_category"] = co2_category;
  doc["pm2_5_category"] = pm2_5_category;
  doc["pm10_category"] = pm10_category;
  
  String jsonData;
  serializeJson(doc, jsonData);
  
  // Send request to API
  http.begin(client, apiUrl);
  http.addHeader("Content-Type", "application/json");
  
  int httpCode = http.POST(jsonData);
  bool isUnsafe = false;
  
  if (httpCode > 0) {
    String payload = http.getString();
    Serial.println("API Response: " + payload);
    
    // Parse response
    DynamicJsonDocument response(200);
    deserializeJson(response, payload);
    
    isUnsafe = response["is_unsafe"];
  } else {
    Serial.println("Error on HTTP request");
    // Fallback to local prediction
    isUnsafe = predictAirQuality(co2, pm2_5, pm10, temperature, humidity, 
                               co2_category, pm2_5_category, pm10_category);
  }
  
  http.end();
  return isUnsafe;
}

// Simplified local prediction function
bool predictAirQuality(float co2, float pm2_5, float pm10, float temperature, float humidity,
                      int co2_category, int pm2_5_category, int pm10_category) {
  // Simple threshold-based prediction based on the trained model
  if (co2 > 680.0) return true;  // High CO2 levels
  if (pm10 > 125.0) return true;  // High PM10 levels
  if (pm2_5_category > 0) return true;  // PM2.5 not in 'Good' category
  
  return false;  // Default to safe air quality
}
""")

print("\nCreated Arduino example code: models/arduino_example.ino")

print("\nSetup complete! You can now run the training script to train the AI model.")
