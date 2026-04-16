from flask import Flask, jsonify
import firebase_admin
from firebase_admin import credentials, db
import pandas as pd
import joblib
import os
import json

app = Flask(__name__)

firebase_creds = json.loads(os.getenv("FIREBASE_CREDENTIALS"))

cred = credentials.Certificate(firebase_creds)

firebase_admin.initialize_app(cred, {
    'databaseURL': os.getenv("FIREBASE_DATABASE_URL")
})

model = joblib.load("irrigation_model.pkl")

@app.route('/')
def home():
    return "AI Irrigation Running 🚀"

@app.route('/run-ai', methods=['GET'])
def run_ai():
    try:
        sensor_ref = db.reference('/sensor_data')
        sensor_data = sensor_ref.get()

        input_df = pd.DataFrame([{
            'Soil_Moisture': sensor_data['soil_moisture'],
            'Temperature': sensor_data['temperature'],
            'Humidity': sensor_data['humidity'],
            'Light_Intensity': sensor_data['light_intensity'],
            'Air_Quality': sensor_data['air_quality']
        }])

        prediction = model.predict(input_df)[0]

        pump_ref = db.reference('/pump_control')
        pump_ref.set({
            'pump_active': bool(prediction)
        })

        return jsonify({
            "prediction": int(prediction),
            "status": "Watering" if prediction else "Idle"
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))