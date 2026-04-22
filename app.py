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
        # Read current soil moisture from Firebase
        soil_moisture = db.reference(
            "/devices/ESP32_CF637C/sensors/current/soilMoisture"
        ).get()

        # Default value if missing
        if soil_moisture is None:
            soil_moisture = 0

        soil_moisture = int(soil_moisture)

        # Dummy values for other model features
        temperature = 25
        humidity = 60
        light_intensity = 500
        air_quality = 300

        # Create dataframe for model
        input_df = pd.DataFrame([{
            "Soil_Moisture": soil_moisture,
            "Temperature": temperature,
            "Humidity": humidity,
            "Light_Intensity": light_intensity,
            "Air_Quality": air_quality
        }])

        # AI model prediction
        prediction = model.predict(input_df)[0]

        # Safe conversion of prediction
        if str(prediction).lower() in ["1", "true", "on", "yes"]:
            ai_prediction = True
        else:
            ai_prediction = False

        # Final threshold logic
        if soil_moisture < 20:
            pump_on = True
        elif soil_moisture > 21:
            pump_on = False
        else:
            pump_on = ai_prediction

        # Save final pump command
        db.reference(
            "/devices/ESP32_CF637C/commands/pump"
        ).set(pump_on)

        # Save AI status info
        db.reference(
            "/devices/ESP32_CF637C/aiStatus"
        ).set({
            "soilMoisture": soil_moisture,
            "rawPrediction": str(prediction),
            "aiPrediction": ai_prediction,
            "pumpCommand": pump_on,
            "lastUpdated": int(time.time())
        })

        # Logs
        print("====================================")
        print("Soil Moisture:", soil_moisture)
        print("Raw Prediction:", prediction)
        print("AI Prediction:", "ON" if ai_prediction else "OFF")
        print("Final Pump Command:", "ON" if pump_on else "OFF")
        print("====================================")

    except Exception as e:
        print("AI Error:", e)

# ================= BACKGROUND LOOP =================
def ai_loop():
    while True:
        run_ai_logic()
        time.sleep(10)

# Start AI loop
threading.Thread(target=ai_loop, daemon=True).start()

# ================= RUN SERVER =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)