import time
import joblib
import pandas as pd
from supabase import create_client

# Credentials
URL = "https://bzovjkwpqkgvntajepel.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ6b3Zqa3dwcWtndm50YWplcGVsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTYyNDI3MiwiZXhwIjoyMDkxMjAwMjcyfQ.TaWSaRsiY8hgq7vLDFGlbup3inzw96X78EoIjKed__A"
supabase = create_client(URL, KEY)

# Load the trained brain
model = joblib.load('irrigation_model.pkl')

def run_ai_logic():
    # 1. Get latest row from NodeMCU via Supabase
    res = supabase.table("sensor_logs").select("*").order("created_at", desc=True).limit(1).execute()
    
    if res.data:
        latest = res.data[0]
        
        # 2. Format data for prediction
        input_df = pd.DataFrame([{
            'Soil_Moisture': latest['soil_moisture'],
            'Temperature': latest['temp'],
            'Humidity': latest['humidity'],
            'Light_Intensity': latest['light_intensity'],
            'Air_Quality': latest['air_quality']
        }])

        # 3. AI Prediction (0 or 1)
        prediction = model.predict(input_df)[0]
        
        # 4. Update Control Table for NodeMCU to act
        supabase.table("device_control").update({"pump_active": bool(prediction)}).eq("device_id", "nodemcu_01").execute()
        print(f"Prediction: {'Watering' if prediction else 'Idle'}")

while True:
    try:
        run_ai_logic()
    except Exception as e:
        print(f"Error: {e}")
    time.sleep(30) # Check every 30 seconds