from flask import Flask, jsonify
import joblib
import pandas as pd
from supabase import create_client
import os

app = Flask(__name__)

# Use environment variables (IMPORTANT)
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(URL, KEY)

model = joblib.load('irrigation_model.pkl')

@app.route('/')
def home():
    return "AI Irrigation Running 🚀"

@app.route('/run-ai', methods=['GET'])
def run_ai_logic():
    try:
        res = supabase.table("sensor_logs") \
            .select("*") \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()

        if not res.data:
            return jsonify({"error": "No data found"})

        latest = res.data[0]

        input_df = pd.DataFrame([{
            'Soil_Moisture': latest['soil_moisture'],
            'Temperature': latest['temp'],
            'Humidity': latest['humidity'],
            'Light_Intensity': latest['light_intensity'],
            'Air_Quality': latest['air_quality']
        }])

        prediction = model.predict(input_df)[0]

        supabase.table("device_control") \
            .update({"pump_active": bool(prediction)}) \
            .eq("device_id", "nodemcu_01") \
            .execute()

        return jsonify({
            "prediction": int(prediction),
            "status": "Watering" if prediction else "Idle"
        })

    except Exception as e:
        return jsonify({"error": str(e)})