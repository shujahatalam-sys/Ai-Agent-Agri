import time
import random
from supabase import create_client

URL = "https://bzovjkwpqkgvntajepel.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ6b3Zqa3dwcWtndm50YWplcGVsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTYyNDI3MiwiZXhwIjoyMDkxMjAwMjcyfQ.TaWSaRsiY8hgq7vLDFGlbup3inzw96X78EoIjKed__A"
supabase = create_client(URL, KEY)

mock_data = {
    "soil_moisture": random.uniform(10.0, 30.0), # Low moisture should trigger watering
    "temp": random.uniform(25.0, 35.0),
    "humidity": random.uniform(40.0, 60.0),
    "light_intensity": random.uniform(500.0, 800.0),
    "air_quality": random.uniform(10.0, 50.0)
}

try:
    print(f"Inserting fake data to Supabase: {mock_data}")
    data, count = supabase.table("sensor_logs").insert(mock_data).execute()
    print(f"Successfully inserted: {data}")
except Exception as e:
    print(f"Error inserting: {e}")
