import joblib
from pathlib import Path
import json
import numpy as np

# Load models and configurations
MODEL_DIR = Path("models")
try:
    with open(MODEL_DIR / "best_model_name.txt", "r") as f:
        best_model_name = f.read().strip()
    
    model = joblib.load(MODEL_DIR / "best_model.joblib")
    scaler = joblib.load(MODEL_DIR / "scaler.joblib")
    
    with open(MODEL_DIR / "feature_columns.json", "r") as f:
        feature_columns = json.load(f)
        
    with open(MODEL_DIR / "encoder_mappings.json", "r") as f:
        encoder_mappings = json.load(f)
except Exception as e:
    model = None
    scaler = None
    feature_columns = []
    encoder_mappings = {}
    print(f"Error loading models: {e}")

def determine_yield_level(yield_val):
    if yield_val > 50000:
        return "High"
    elif yield_val > 25000:
        return "Medium"
    return "Low"

def predict_yield(crop: str, country: str, year: int, rainfall: float, pesticide: float, temp: float):
    if model is None:
        raise ValueError("Model not loaded properly.")
        
    # Feature Engineering exactly as in training
    rainfall_temp_ratio = rainfall / (temp + 1e-5)
    pesticide_intensity = pesticide / (rainfall + 1e-5)
    climate_stress = abs(temp - 20) * (2000 / (rainfall + 1e-5))
    
    area_encoded = encoder_mappings.get("Area", {}).get(country, -1)
    item_encoded = encoder_mappings.get("Item", {}).get(crop, -1)
    
    # Construct input array in the correct order
    input_dict = {
        "Year": year,
        "average_rain_fall_mm_per_year": rainfall,
        "pesticides_tonnes": pesticide,
        "avg_temp": temp,
        "rainfall_temp_ratio": rainfall_temp_ratio,
        "pesticide_intensity": pesticide_intensity,
        "climate_stress_index": climate_stress,
        "rainfall_squared": rainfall ** 2,
        "temp_squared": temp ** 2,
        "year_normalized": year - 1990,
        "year_squared": (year - 1990) ** 2,
        "average_rain_fall_mm_per_year_rolling_mean_3": rainfall, # Approximation
        "average_rain_fall_mm_per_year_lag_1": rainfall, # Approximation
        "avg_temp_rolling_mean_3": temp, # Approximation
        "avg_temp_lag_1": temp, # Approximation
        "hg/ha_yield_rolling_mean_3": 38295.0, # Median fallback
        "hg/ha_yield_lag_1": 38295.0, # Median fallback
        "Area_encoded": area_encoded,
        "Item_encoded": item_encoded,
        "area_item_interaction": area_encoded * item_encoded if area_encoded != -1 and item_encoded != -1 else 0
    }
    
    # Ensure all columns are present
    input_array = []
    for col in feature_columns:
        input_array.append(input_dict.get(col, 0))
        
    X_pred = np.array(input_array).reshape(1, -1)
    
    if scaler:
        X_pred = scaler.transform(X_pred)
        
    pred = model.predict(X_pred)[0]
    return max(0, pred) # Yield cannot be negative
