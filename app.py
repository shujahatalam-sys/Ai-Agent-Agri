import os
import json
import time
import joblib
import pandas as pd
import firebase_admin

from firebase_admin import credentials, db
from flask import Flask

# ================= FLASK APP =================
app = Flask(__name__)

@app.route("/")
def home():
    return "AI Irrigation System Running"

# ================= FIREBASE SETUP =================
firebase_creds = json.loads(os.environ["FIREBASE_CREDENTIALS"])

cred = credentials.Certificate(firebase_creds)

firebase_admin.initialize_app(cred, {
    "databaseURL": "https://fieldsync-edcd7-default-rtdb.firebaseio.com"
})

# ================= LOAD MODEL =================
model = joblib.load("irrigation_model.pkl")

# ================= AI LOGIC =================
def run_ai_logic():
    try:
        # Read sensor values from Firebase
        soil_moisture = db.reference(
            "/devices/ESP32_CF637C/sensors/current/soilMoisture"
        ).get()

        # Default value if missing
        if soil_moisture is None:
            soil_moisture = 0

        # Dummy values for missing model inputs
        temperature = 25
        humidity = 60
        light_intensity = 500
        air_quality = 300

        # Create DataFrame for model
        input_df = pd.DataFrame([{
            "Soil_Moisture": soil_moisture,
            "Temperature": temperature,
            "Humidity": humidity,
            "Light_Intensity": light_intensity,
            "Air_Quality": air_quality
        }])

        # Prediction
        prediction = model.predict(input_df)[0]

        # Safety rule
        pump_on = bool(prediction)

        # Never run pump if soil already wet
        if soil_moisture > 70:
            pump_on = False

        # Force ON if soil too dry
        if soil_moisture < 20:
            pump_on = True

        # Save AI decision to Firebase
        db.reference(
            "/devices/ESP32_CF637C/commands/pump"
        ).set(pump_on)

        print("=================================")
        print(f"Soil Moisture: {soil_moisture}")
        print(f"AI Prediction: {prediction}")
        print(f"Pump Command: {'ON' if pump_on else 'OFF'}")
        print("=================================")

    except Exception as e:
        print("AI Error:", e)

# ================= BACKGROUND LOOP =================
while True:
    run_ai_logic()
    time.sleep(10)

# ================= RUN SERVER =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)