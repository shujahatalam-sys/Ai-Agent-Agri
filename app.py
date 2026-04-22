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

        # Default if missing
        if soil_moisture is None:
            soil_moisture = 0

        soil_moisture = int(soil_moisture)

        # Read thresholds from Firebase
        min_threshold = db.reference(
            "/devices/ESP32_CF637C/thresholds/settings/soilMoistureMin"
        ).get()

        max_threshold = db.reference(
            "/devices/ESP32_CF637C/thresholds/settings/soilMoistureMax"
        ).get()

        # Default threshold values if missing
        if min_threshold is None:
            min_threshold = 20

        if max_threshold is None:
            max_threshold = 21

        min_threshold = int(min_threshold)
        max_threshold = int(max_threshold)

        # Read current pump state from Firebase
        pump_ref = db.reference("/devices/ESP32_CF637C/commands/pump")
        current_pump_state = pump_ref.get()

        if current_pump_state is None:
            current_pump_state = False

        # Dummy values for remaining model inputs
        temperature = 25
        humidity = 60
        light_intensity = 500
        air_quality = 300

        # Create dataframe for model prediction
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
        if str(prediction).lower() in ["1", "true", "on", "yes"]:
            ai_prediction = True
        else:
            ai_prediction = False

        # ================= FINAL PUMP LOGIC =================
        # Below minimum threshold → Pump ON
        if soil_moisture < min_threshold:
            pump_on = True

        # Above maximum threshold → Pump OFF
        elif soil_moisture > max_threshold:
            pump_on = False

        # Between thresholds → Keep previous pump state
        else:
            pump_on = current_pump_state

        # Save final pump command to Firebase
        pump_ref.set(pump_on)

        # Save AI status to Firebase
        db.reference(
            "/devices/ESP32_CF637C/aiStatus"
        ).set({
            "soilMoisture": soil_moisture,
            "minThreshold": min_threshold,
            "maxThreshold": max_threshold,
            "rawPrediction": str(prediction),
            "aiPrediction": ai_prediction,
            "previousPumpState": current_pump_state,
            "finalPumpCommand": pump_on,
            "lastUpdated": int(time.time())
        })

        # ================= SERIAL LOGS =================
        print("====================================")
        print("Soil Moisture:", soil_moisture)
        print("Min Threshold:", min_threshold)
        print("Max Threshold:", max_threshold)
        print("Raw Model Prediction:", prediction)
        print("AI Prediction:", "ON" if ai_prediction else "OFF")
        print("Previous Pump State:", "ON" if current_pump_state else "OFF")
        print("Final Pump Command:", "ON" if pump_on else "OFF")
        print("====================================")

    except Exception as e:
        print("AI Error:", e)

# ================= BACKGROUND LOOP =================
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