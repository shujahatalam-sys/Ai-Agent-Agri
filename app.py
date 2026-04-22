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

        # Default if missing
        if soil_moisture is None:
            soil_moisture = 0

        soil_moisture = int(soil_moisture)

        # Get previous pump state
        pump_ref = db.reference("/devices/ESP32_CF637C/commands/pump")
        current_pump_state = pump_ref.get()

        if current_pump_state is None:
            current_pump_state = False

        # Dummy values for remaining model inputs
        temperature = 25
        humidity = 60
        light_intensity = 500
        air_quality = 300

        # Create dataframe for prediction
        input_df = pd.DataFrame([{
            "Soil_Moisture": soil_moisture,
            "Temperature": temperature,
            "Humidity": humidity,
            "Light_Intensity": light_intensity,
            "Air_Quality": air_quality
        }])

        # Model prediction
        prediction = model.predict(input_df)[0]

        # Convert prediction safely
        if str(prediction).lower() in ["1", "true", "on", "yes"]:
            pump_on = True
        else:
            pump_on = False

        # Threshold Logic
        if soil_moisture < 20:
            pump_on = True
        elif soil_moisture > 30:
            pump_on = False
        else:
            # Between 20 and 30 keep previous state
            pump_on = current_pump_state

        # Save final pump command
        pump_ref.set(pump_on)

        # Save AI status
        db.reference(
            "/devices/ESP32_CF637C/aiStatus"
        ).set({
            "soilMoisture": soil_moisture,
            "prediction": str(prediction),
            "pumpCommand": pump_on,
            "currentPumpState": current_pump_state,
            "lastUpdated": int(time.time())
        })

        # Logs
        print("====================================")
        print("Soil Moisture:", soil_moisture)
        print("Previous Pump State:", current_pump_state)
        print("Raw Prediction:", prediction)
        print("Final Pump Command:", "ON" if pump_on else "OFF")
        print("====================================")

    except Exception as e:
        print("AI Error:", e)

# ================= BACKGROUND LOOP =================
def ai_loop():
    while True:
        run_ai_logic()
        time.sleep(10)

# Start AI loop in background
threading.Thread(target=ai_loop, daemon=True).start()

# ================= RUN SERVER =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)