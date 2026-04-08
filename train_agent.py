import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

def train():
    # Load your local file
    df = pd.read_excel("smart_irrigation_dataset.csv", engine="openpyxl")
    
    # Define features and target
    X = df[['Soil_Moisture', 'Temperature', 'Humidity', 'Light_Intensity', 'Air_Quality']]
    y = df['Irrigation']

    # Train model
    model = RandomForestClassifier(n_estimators=100)
    model.fit(X, y)
    
    # Save the model to a file
    joblib.dump(model, 'irrigation_model.pkl')
    print("AI Model trained and saved locally as irrigation_model.pkl")

if __name__ == "__main__":
    train()