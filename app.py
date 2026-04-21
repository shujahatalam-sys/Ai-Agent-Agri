import os
import json
import time
import threading
import joblib
import pandas as pd
import firebase_admin

from flask import Flask
from firebase_admin import credentials, db

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
        # Read soil moisture from Firebase
        soil_moisture = db.reference(
            "/devices/ESP32_CF637C/sensors/current/soilMoisture"
        ).get()

        # Default value if missing
        if soil_moisture is None:
            soil_moisture = 0

        # Dummy values for other model features
        temperature = 25
        humidity = 60
        light_intensity = 500
        air_quality = 300

        # Create input dataframe
        input_df = pd.DataFrame([{
            "Soil_Moisture": soil_moisture,
            "Temperature": temperature,
            "Humidity": humidity,
            "Light_Intensity": light_intensity,
            "Air_Quality": air_quality
        }])

        # Model prediction
        prediction = model.predict(input_df)[0]

        # Convert prediction to boolean
        pump_on = bool(prediction)

        # Safety logic
        # Force ON if too dry
        if soil_moisture < 20:
            pump_on = True

        # Force OFF if wet enough
        if soil_moisture > 30:
            pump_on = False

        # Save AI decision to Firebase
        db.reference(
            "/devices/ESP32_CF637C/commands/pump"
        ).set(pump_on)

        # Save AI prediction info
        db.reference(
            "/devices/ESP32_CF637C/aiStatus"
        ).set({
            "soilMoisture": soil_moisture,
            "prediction": int(prediction),
            "pumpCommand": pump_on,
            "lastUpdated": int(time.time())
        })

        print("====================================")
        print(f"Soil Moisture: {soil_moisture}")
        print(f"AI Prediction: {prediction}")
        print(f"Pump Command: {'ON' if pump_on else 'OFF'}")
        print("====================================")

    except Exception as e:
        print("AI Error:", e)

# ================= BACKGROUND AI LOOP =================
def ai_loop():
    while True:
        try:
            run_ai_logic()
        except Exception as e:
            print("Loop Error:", e)

        time.sleep(10)

# Start AI loop in background
threading.Thread(target=ai_loop, daemon=True).start()

# ================= RUN SERVER =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)