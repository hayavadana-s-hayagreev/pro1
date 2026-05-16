import pandas as pd
import numpy as np
from pathlib import Path
import json
import joblib
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import xgboost as xgb
import lightgbm as lgb
from catboost import CatBoostRegressor
import optuna
import mlflow

# Configuration
DATA_PATH = Path("data/raw/yield_df.csv")
MODEL_DIR = Path("models")
MODEL_DIR.mkdir(exist_ok=True, parents=True)

def engineer_features(df):
    df_feat = df.copy()
    
    # Ratios
    df_feat['rainfall_temp_ratio'] = df_feat['average_rain_fall_mm_per_year'] / (df_feat['avg_temp'] + 1e-5)
    df_feat['pesticide_intensity'] = df_feat['pesticides_tonnes'] / (df_feat['average_rain_fall_mm_per_year'] + 1e-5)
    df_feat['climate_stress_index'] = abs(df_feat['avg_temp'] - 20) * (2000 / (df_feat['average_rain_fall_mm_per_year'] + 1e-5))
    
    # Polynomials
    df_feat['rainfall_squared'] = df_feat['average_rain_fall_mm_per_year'] ** 2
    df_feat['temp_squared'] = df_feat['avg_temp'] ** 2
    
    # Time
    min_year = df_feat['Year'].min()
    df_feat['year_normalized'] = df_feat['Year'] - min_year
    df_feat['year_squared'] = df_feat['year_normalized'] ** 2
    
    # Rolling and lags (grouped by Area and Item)
    df_feat = df_feat.sort_values(by=['Area', 'Item', 'Year'])
    cols_to_lag = ['average_rain_fall_mm_per_year', 'avg_temp', 'hg/ha_yield']
    for col in cols_to_lag:
        df_feat[f'{col}_rolling_mean_3'] = df_feat.groupby(['Area', 'Item'])[col].transform(lambda x: x.rolling(3, min_periods=1).mean())
        df_feat[f'{col}_lag_1'] = df_feat.groupby(['Area', 'Item'])[col].shift(1)
        
    df_feat.fillna(method='bfill', inplace=True)
    return df_feat

def train_and_evaluate():
    print("Loading data...")
    df = pd.read_csv(DATA_PATH)
    
    print("Engineering features...")
    df = engineer_features(df)
    
    # Encoding
    encoder_mappings = {}
    for col in ['Area', 'Item']:
        le = LabelEncoder()
        df[f'{col}_encoded'] = le.fit_transform(df[col])
        encoder_mappings[col] = dict(zip(le.classes_, le.transform(le.classes_).tolist()))
        
    df['area_item_interaction'] = df['Area_encoded'] * df['Item_encoded']
    
    with open(MODEL_DIR / "encoder_mappings.json", "w") as f:
        json.dump(encoder_mappings, f, indent=2)
        
    # Temporal Split (Train: < 2010, Test: >= 2010)
    train_df = df[df['Year'] < 2010]
    test_df = df[df['Year'] >= 2010]
    
    features = [
        "Year", "average_rain_fall_mm_per_year", "pesticides_tonnes", "avg_temp",
        "rainfall_temp_ratio", "pesticide_intensity", "climate_stress_index",
        "rainfall_squared", "temp_squared", "year_normalized", "year_squared",
        "average_rain_fall_mm_per_year_rolling_mean_3", "average_rain_fall_mm_per_year_lag_1",
        "avg_temp_rolling_mean_3", "avg_temp_lag_1",
        "hg/ha_yield_rolling_mean_3", "hg/ha_yield_lag_1",
        "Area_encoded", "Item_encoded", "area_item_interaction"
    ]
    
    with open(MODEL_DIR / "feature_columns.json", "w") as f:
        json.dump(features, f, indent=2)
        
    target = "hg/ha_yield"
    
    X_train, y_train = train_df[features], train_df[target]
    X_test, y_test = test_df[features], test_df[target]
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    joblib.dump(scaler, MODEL_DIR / "scaler.joblib")
    
    models = {
        "LinearRegression": LinearRegression(),
        "RandomForest": RandomForestRegressor(n_estimators=100, max_depth=15, random_state=42),
        "XGBoost": xgb.XGBRegressor(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42),
        "LightGBM": lgb.LGBMRegressor(n_estimators=100, max_depth=8, random_state=42, verbose=-1)
    }
    
    metrics = {}
    best_r2 = -float('inf')
    best_model_name = ""
    best_model = None
    
    for name, model in models.items():
        print(f"Training {name}...")
        model.fit(X_train_scaled, y_train)
        preds = model.predict(X_test_scaled)
        
        r2 = r2_score(y_test, preds)
        rmse = np.sqrt(mean_squared_error(y_test, preds))
        mae = mean_absolute_error(y_test, preds)
        
        metrics[name] = {"rmse": rmse, "mae": mae, "r2": r2}
        print(f"{name} R2: {r2:.4f}, RMSE: {rmse:.2f}")
        
        if r2 > best_r2:
            best_r2 = r2
            best_model_name = name
            best_model = model
            
    print(f"\nBest Model: {best_model_name} (R2: {best_r2:.4f})")
    
    with open(MODEL_DIR / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
        
    with open(MODEL_DIR / "best_model_name.txt", "w") as f:
        f.write(best_model_name)
        
    joblib.dump(best_model, MODEL_DIR / "best_model.joblib")
    print("Training pipeline complete.")

if __name__ == "__main__":
    train_and_evaluate()
