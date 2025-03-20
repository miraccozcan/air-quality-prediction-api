# Save this as train_fire_model_fixed.py
import pandas as pd
import numpy as np
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# Ensure the models directory exists
os.makedirs('models', exist_ok=True)

# Load the dataset
print("Loading dataset...")
df = pd.read_csv('smoke_detection_iot.csv')

# Drop unnecessary columns
df = df.drop(columns=['Unnamed: 0', 'UTC', 'CNT'], errors='ignore')

# Define features and target variable
print("Preparing data...")
X = df.drop(columns=['Fire Alarm'])
y = df['Fire Alarm']

# Split the data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42)

# Normalize numerical features
print("Scaling features...")
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# Train the model
print("Training model...")
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate the model
y_pred = model.predict(X_test)
print("Accuracy:", accuracy_score(y_test, y_pred))

# Save the model and scaler
print("Saving model files...")
joblib.dump(model, 'models/fire_detection_model.pkl')
joblib.dump(scaler, 'models/fire_detection_scaler.pkl')

print("Model training complete. Model saved as 'models/fire_detection_model.pkl'")
print("Scaler saved as 'models/fire_detection_scaler.pkl'")
