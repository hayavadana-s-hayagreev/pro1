"""
Crop Yield Estimator - Complete Application
"""

import argparse
import json
import os
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from loguru import logger

warnings.filterwarnings("ignore")


def convert(obj):
    """Convert numpy types to Python types for JSON."""
    if isinstance(obj, dict):
        return {str(k): convert(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert(i) for i in obj]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


def save_json(data, filepath):
    """Save data to JSON safely, converting all numpy types."""
    with open(filepath, "w") as f:
        json.dump(convert(data), f, indent=2)


def load_config(path="configs/config.yaml"):
    if Path(path).exists():
        with open(path, "r") as f:
            return yaml.safe_load(f) or {}
    return {}


CONFIG = load_config()
SEED = CONFIG.get("project", {}).get("seed", 42)


def load_data(path=None):
    path = path or CONFIG.get("data", {}).get("raw_path", "data/raw/yield_df.csv")
    if not Path(path).exists():
        logger.error(f"Dataset not found at {path}")
        logger.info("Download from: https://www.kaggle.com/datasets/patelris/crop-yield-prediction-dataset")
        sys.exit(1)
    df = pd.read_csv(path)
    if "Unnamed: 0" in df.columns:
        df.drop(columns=["Unnamed: 0"], inplace=True)
    logger.info(f"Data loaded: {df.shape[0]} rows x {df.shape[1]} columns")
    logger.info(f"Countries: {df['Area'].nunique()}, Crops: {df['Item'].nunique()}")
    logger.info(f"Years: {df['Year'].min()} - {df['Year'].max()}")
    return df


def clean_data(df):
    logger.info("Cleaning data...")
    missing = df.isnull().sum()
    if missing.sum() > 0:
        for col in df.columns:
            if df[col].isnull().sum() > 0:
                if df[col].dtype in [np.float64, np.int64]:
                    df[col].fillna(df[col].median(), inplace=True)
                else:
                    df[col].fillna(df[col].mode()[0], inplace=True)
        logger.info("Missing values filled")
    else:
        logger.info("No missing values found")
    dup_count = df.duplicated().sum()
    if dup_count > 0:
        df = df.drop_duplicates().reset_index(drop=True)
        logger.info(f"Removed {dup_count} duplicate rows")
    else:
        logger.info("No duplicate rows found")
    numeric_cols = ["average_rain_fall_mm_per_year", "pesticides_tonnes", "avg_temp"]
    for col in numeric_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        outliers = ((df[col] < lower) | (df[col] > upper)).sum()
        if outliers > 0:
            df[col] = df[col].clip(lower, upper)
            logger.info(f"Capped {outliers} outliers in {col}")
    logger.info(f"Data cleaned: {df.shape[0]} rows x {df.shape[1]} columns")
    return df


def engineer_features(df):
    logger.info("Engineering features...")
    df["rainfall_temp_ratio"] = df["average_rain_fall_mm_per_year"] / (df["avg_temp"] + 1e-8)
    df["pesticide_intensity"] = df["pesticides_tonnes"] / (df["average_rain_fall_mm_per_year"] + 1e-8)
    temp_norm = (df["avg_temp"] - df["avg_temp"].min()) / (df["avg_temp"].max() - df["avg_temp"].min() + 1e-8)
    rain_norm = (df["average_rain_fall_mm_per_year"] - df["average_rain_fall_mm_per_year"].min()) / (df["average_rain_fall_mm_per_year"].max() - df["average_rain_fall_mm_per_year"].min() + 1e-8)
    df["climate_stress_index"] = temp_norm * (1 - rain_norm)
    df["rainfall_squared"] = df["average_rain_fall_mm_per_year"] ** 2
    df["temp_squared"] = df["avg_temp"] ** 2
    min_year = df["Year"].min()
    max_year = df["Year"].max()
    df["year_normalized"] = (df["Year"] - min_year) / (max_year - min_year + 1e-8)
    df["year_squared"] = df["year_normalized"] ** 2
    df["decade"] = (df["Year"] // 10) * 10
    df = df.sort_values(["Area", "Item", "Year"]).reset_index(drop=True)
    for col in ["average_rain_fall_mm_per_year", "avg_temp", "hg/ha_yield"]:
        df[f"{col}_rolling_mean_3"] = (
            df.groupby(["Area", "Item"])[col]
            .transform(lambda x: x.rolling(window=3, min_periods=1).mean())
        )
        df[f"{col}_lag_1"] = (
            df.groupby(["Area", "Item"])[col]
            .transform(lambda x: x.shift(1))
        )
        df[f"{col}_lag_1"] = df[f"{col}_lag_1"].fillna(df[col].median())
    from sklearn.preprocessing import LabelEncoder
    area_encoder = LabelEncoder()
    item_encoder = LabelEncoder()
    df["Area_encoded"] = area_encoder.fit_transform(df["Area"])
    df["Item_encoded"] = item_encoder.fit_transform(df["Item"])
    df["area_item_interaction"] = df["Area_encoded"] * 100 + df["Item_encoded"]
    logger.info(f"Features engineered: {df.shape[1]} total columns")
    return df, area_encoder, item_encoder


def get_feature_columns(df):
    exclude = {"Area", "Item", "hg/ha_yield", "decade"}
    return [col for col in df.columns if col not in exclude]


def train_models(df, feature_cols):
    from sklearn.linear_model import LinearRegression
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import cross_val_score, TimeSeriesSplit
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    from sklearn.preprocessing import StandardScaler
    import xgboost as xgb
    import lightgbm as lgb
    from catboost import CatBoostRegressor
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    logger.info("Preparing data for modeling...")
    df_sorted = df.sort_values("Year").reset_index(drop=True)
    split_year = df_sorted["Year"].quantile(0.8)
    train_df = df_sorted[df_sorted["Year"] <= split_year].copy()
    test_df = df_sorted[df_sorted["Year"] > split_year].copy()
    X_train = train_df[feature_cols]
    y_train = train_df["hg/ha_yield"]
    X_test = test_df[feature_cols]
    y_test = test_df["hg/ha_yield"]
    scale_cols = ["average_rain_fall_mm_per_year", "pesticides_tonnes", "avg_temp"]
    scale_cols = [c for c in scale_cols if c in feature_cols]
    scaler = StandardScaler()
    X_train[scale_cols] = scaler.fit_transform(X_train[scale_cols])
    X_test[scale_cols] = scaler.transform(X_test[scale_cols])
    logger.info(f"Train: {len(X_train)} samples (Year <= {split_year:.0f})")
    logger.info(f"Test: {len(X_test)} samples (Year > {split_year:.0f})")

    models = {
        "LinearRegression": LinearRegression(),
        "RandomForest": RandomForestRegressor(
            n_estimators=300, max_depth=20, min_samples_split=5,
            min_samples_leaf=2, random_state=SEED, n_jobs=-1
        ),
        "XGBoost": xgb.XGBRegressor(
            n_estimators=500, max_depth=6, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, random_state=SEED, n_jobs=-1
        ),
        "LightGBM": lgb.LGBMRegressor(
            n_estimators=500, max_depth=8, learning_rate=0.05,
            num_leaves=31, random_state=SEED, n_jobs=-1, verbose=-1
        ),
        "CatBoost": CatBoostRegressor(
            iterations=500, depth=6, learning_rate=0.05,
            random_state=SEED, verbose=0
        ),
    }

    results = {}
    trained_models = {}
    feature_importance = {}

    logger.info("Training models...")
    logger.info("=" * 60)

    for name, model in models.items():
        logger.info(f"\nTraining {name}...")
        model.fit(X_train, y_train)
        trained_models[name] = model
        y_pred = model.predict(X_test)
        rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
        mae = float(mean_absolute_error(y_test, y_pred))
        r2 = float(r2_score(y_test, y_pred))
        tscv = TimeSeriesSplit(n_splits=3)
        cv_scores = cross_val_score(model, X_train, y_train, cv=tscv,
                                     scoring="neg_root_mean_squared_error", n_jobs=-1)
        cv_rmse = float(-cv_scores.mean())
        results[name] = {"rmse": rmse, "mae": mae, "r2": r2, "cv_rmse": cv_rmse}
        logger.info(f"   RMSE: {rmse:.2f}")
        logger.info(f"   MAE:  {mae:.2f}")
        logger.info(f"   R2:   {r2:.4f}")
        logger.info(f"   CV RMSE: {cv_rmse:.2f}")
        if hasattr(model, "feature_importances_"):
            imp = dict(zip(feature_cols, [float(x) for x in model.feature_importances_]))
            imp = dict(sorted(imp.items(), key=lambda x: x[1], reverse=True))
            feature_importance[name] = imp
        elif name == "LinearRegression" and hasattr(model, "coef_"):
            imp = dict(zip(feature_cols, [float(x) for x in np.abs(model.coef_)]))
            imp = dict(sorted(imp.items(), key=lambda x: x[1], reverse=True))
            feature_importance[name] = imp

    best_name = min(results, key=lambda k: results[k]["rmse"])
    best_model = trained_models[best_name]
    logger.info("\n" + "=" * 60)
    logger.info(f"BEST MODEL: {best_name}")
    logger.info(f"   RMSE: {results[best_name]['rmse']:.2f}")
    logger.info(f"   MAE:  {results[best_name]['mae']:.2f}")
    logger.info(f"   R2:   {results[best_name]['r2']:.4f}")
    logger.info("=" * 60)

    # Hyperparameter tuning
    logger.info(f"\nTuning {best_name} with Optuna (30 trials)...")

    def create_objective(model_type):
        def objective(trial):
            if model_type == "XGBoost":
                params = {
                    "n_estimators": trial.suggest_int("n_estimators", 100, 1000),
                    "max_depth": trial.suggest_int("max_depth", 3, 10),
                    "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                    "subsample": trial.suggest_float("subsample", 0.6, 1.0),
                    "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
                    "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
                }
                m = xgb.XGBRegressor(**params, random_state=SEED, n_jobs=-1)
            elif model_type == "LightGBM":
                params = {
                    "n_estimators": trial.suggest_int("n_estimators", 100, 1000),
                    "max_depth": trial.suggest_int("max_depth", 3, 12),
                    "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                    "num_leaves": trial.suggest_int("num_leaves", 10, 100),
                    "subsample": trial.suggest_float("subsample", 0.6, 1.0),
                }
                m = lgb.LGBMRegressor(**params, random_state=SEED, n_jobs=-1, verbose=-1)
            elif model_type == "CatBoost":
                params = {
                    "iterations": trial.suggest_int("iterations", 100, 1000),
                    "depth": trial.suggest_int("depth", 3, 10),
                    "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                }
                m = CatBoostRegressor(**params, random_state=SEED, verbose=0)
            elif model_type == "RandomForest":
                params = {
                    "n_estimators": trial.suggest_int("n_estimators", 100, 500),
                    "max_depth": trial.suggest_int("max_depth", 5, 30),
                    "min_samples_split": trial.suggest_int("min_samples_split", 2, 20),
                    "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 10),
                }
                m = RandomForestRegressor(**params, random_state=SEED, n_jobs=-1)
            else:
                return float("inf")
            tscv = TimeSeriesSplit(n_splits=3)
            scores = cross_val_score(m, X_train, y_train, cv=tscv,
                                     scoring="neg_root_mean_squared_error", n_jobs=-1)
            return float(-scores.mean())
        return objective

    best_name_final = best_name
    if best_name in ["XGBoost", "LightGBM", "CatBoost", "RandomForest"]:
        study = optuna.create_study(direction="minimize")
        study.optimize(create_objective(best_name), n_trials=30, timeout=600)
        logger.info(f"Best Optuna RMSE: {study.best_value:.2f}")
        best_params = study.best_params
        if best_name == "XGBoost":
            tuned_model = xgb.XGBRegressor(**best_params, random_state=SEED, n_jobs=-1)
        elif best_name == "LightGBM":
            tuned_model = lgb.LGBMRegressor(**best_params, random_state=SEED, n_jobs=-1, verbose=-1)
        elif best_name == "CatBoost":
            tuned_model = CatBoostRegressor(**best_params, random_state=SEED, verbose=0)
        elif best_name == "RandomForest":
            tuned_model = RandomForestRegressor(**best_params, random_state=SEED, n_jobs=-1)
        tuned_model.fit(X_train, y_train)
        y_pred_tuned = tuned_model.predict(X_test)
        tuned_rmse = float(np.sqrt(mean_squared_error(y_test, y_pred_tuned)))
        tuned_mae = float(mean_absolute_error(y_test, y_pred_tuned))
        tuned_r2 = float(r2_score(y_test, y_pred_tuned))
        results[best_name + "_Tuned"] = {"rmse": tuned_rmse, "mae": tuned_mae, "r2": tuned_r2, "cv_rmse": float(study.best_value)}
        if tuned_rmse < results[best_name]["rmse"]:
            best_model = tuned_model
            best_name_final = best_name + "_Tuned"
            logger.info(f"Tuned model is BETTER! RMSE: {tuned_rmse:.2f}")

    # Save artifacts
    logger.info("\nSaving model and artifacts...")
    import joblib
    Path("models").mkdir(exist_ok=True)
    joblib.dump(best_model, "models/best_model.joblib")
    joblib.dump(scaler, "models/scaler.joblib")

    # SAVE ALL JSON FILES USING save_json (converts numpy types)
    save_json(feature_cols, "models/feature_columns.json")
    save_json(results, "models/metrics.json")

    with open("models/best_model_name.txt", "w") as f:
        f.write(best_name_final)

    logger.info("All artifacts saved to models/")
    return {
        "results": results,
        "best_name": best_name_final,
        "best_model": best_model,
        "scaler": scaler,
        "feature_cols": feature_cols,
        "feature_importance": feature_importance,
    }


def predict_yield(crop, country, rainfall, pesticide, temperature, year):
    import joblib
    from sklearn.preprocessing import LabelEncoder
    model = joblib.load("models/best_model.joblib")
    scaler = joblib.load("models/scaler.joblib")
    with open("models/feature_columns.json", "r") as f:
        feature_cols = json.load(f)
    with open("models/encoder_mappings.json", "r") as f:
        encoder_mappings = json.load(f)
    input_df = pd.DataFrame([{
        "Year": year,
        "average_rain_fall_mm_per_year": rainfall,
        "pesticides_tonnes": pesticide,
        "avg_temp": temperature,
        "Area": country,
        "Item": crop,
        "hg/ha_yield": 0,
    }])
    input_df["rainfall_temp_ratio"] = input_df["average_rain_fall_mm_per_year"] / (input_df["avg_temp"] + 1e-8)
    input_df["pesticide_intensity"] = input_df["pesticides_tonnes"] / (input_df["average_rain_fall_mm_per_year"] + 1e-8)
    temp_min, temp_max = 1.29, 30.85
    rain_min, rain_max = 51, 3240
    temp_norm = (input_df["avg_temp"] - temp_min) / (temp_max - temp_min + 1e-8)
    rain_norm = (input_df["average_rain_fall_mm_per_year"] - rain_min) / (rain_max - rain_min + 1e-8)
    input_df["climate_stress_index"] = temp_norm * (1 - rain_norm)
    input_df["rainfall_squared"] = input_df["average_rain_fall_mm_per_year"] ** 2
    input_df["temp_squared"] = input_df["avg_temp"] ** 2
    input_df["year_normalized"] = (input_df["Year"] - 1961) / (2019 - 1961 + 1e-8)
    input_df["year_squared"] = input_df["year_normalized"] ** 2
    input_df["decade"] = (input_df["Year"] // 10) * 10
    for col in ["average_rain_fall_mm_per_year", "avg_temp", "hg/ha_yield"]:
        input_df[f"{col}_rolling_mean_3"] = input_df[col]
        input_df[f"{col}_lag_1"] = input_df[col]
    area_map = encoder_mappings.get("Area", {})
    item_map = encoder_mappings.get("Item", {})
    input_df["Area_encoded"] = area_map.get(country, 0)
    input_df["Item_encoded"] = item_map.get(crop, 0)
    input_df["area_item_interaction"] = input_df["Area_encoded"] * 100 + input_df["Item_encoded"]
    scale_cols = ["average_rain_fall_mm_per_year", "pesticides_tonnes", "avg_temp"]
    scale_cols_existing = [c for c in scale_cols if c in input_df.columns]
    input_df[scale_cols_existing] = scaler.transform(input_df[scale_cols_existing])
    for col in feature_cols:
        if col not in input_df.columns:
            input_df[col] = 0.0
    X = input_df[feature_cols]
    prediction = model.predict(X)[0]
    return float(prediction)


def generate_recommendations(crop, country, rainfall, pesticide, temperature, predicted_yield):
    recommendations = []
    if rainfall < 500:
        recommendations.append(
            f"IRRIGATION: Rainfall of {rainfall}mm is very low for {crop} in {country}. "
            f"Install drip irrigation. Use rainwater harvesting and mulching."
        )
    elif rainfall < 800:
        recommendations.append(
            f"IRRIGATION: Rainfall of {rainfall}mm is below optimal for {crop}. "
            f"Add supplemental irrigation during flowering and grain-filling stages."
        )
    elif rainfall < 1200:
        recommendations.append(
            f"IRRIGATION: Rainfall of {rainfall}mm is adequate for {crop}. "
            f"Ensure proper drainage to prevent waterlogging."
        )
    else:
        recommendations.append(
            f"IRRIGATION: High rainfall ({rainfall}mm) may cause waterlogging. "
            f"Build drainage systems. Consider raised bed planting."
        )
    if predicted_yield < 20000:
        recommendations.append(
            f"FERTILIZER: Low predicted yield suggests nutrient deficiency. "
            f"Apply balanced NPK fertilizer for {crop}. Add organic compost. Get a soil test done."
        )
    elif predicted_yield < 80000:
        recommendations.append(
            f"FERTILIZER: Moderate yield potential for {crop}. "
            f"Apply stage-specific fertilization for yield improvement."
        )
    else:
        recommendations.append(
            f"FERTILIZER: High yield expected for {crop}! Maintain current regime. "
            f"Use slow-release fertilizers and split applications."
        )
    if predicted_yield < 20000 and rainfall < 600:
        recommendations.append(
            f"CROP ALTERNATIVES: Low yield + low rainfall means {crop} may not be ideal. "
            f"Try drought-resistant crops like sorghum, millet, or cassava."
        )
    elif predicted_yield < 20000 and temperature > 30:
        recommendations.append(
            f"CROP ALTERNATIVES: Low yield + high temperature. "
            f"Try heat-tolerant crops like sunflower or sesame."
        )
    elif predicted_yield >= 80000:
        recommendations.append(
            f"CROP ALTERNATIVES: {crop} is doing great! Keep growing it. "
            f"Add crop rotation with legumes to keep soil healthy."
        )
    if temperature > 30:
        recommendations.append(
            f"CLIMATE ADAPTATION: High temperature ({temperature}C) may stress {crop}. "
            f"Use shade nets. Plant heat-tolerant varieties."
        )
    elif temperature < 15:
        recommendations.append(
            f"CLIMATE ADAPTATION: Low temperature ({temperature}C) may slow {crop} growth. "
            f"Use greenhouse covers. Apply mulch to warm soil."
        )
    else:
        recommendations.append(
            f"CLIMATE ADAPTATION: Temperature ({temperature}C) is good for {crop}. "
            f"Monitor weather and have backup plans for extreme events."
        )
    if pesticide > 500:
        recommendations.append(
            f"PEST MANAGEMENT: High pesticide usage ({pesticide} tonnes). "
            f"Switch to Integrated Pest Management. Use biological controls."
        )
    elif pesticide < 50:
        recommendations.append(
            f"PEST MANAGEMENT: Low pesticide usage ({pesticide} tonnes). "
            f"Stay alert for pest outbreaks. Check fields weekly."
        )
    else:
        recommendations.append(
            f"PEST MANAGEMENT: Moderate pesticide usage for {crop}. "
            f"Continue monitoring. Rotate pesticide types to prevent resistance."
        )
    region_insights = {
        "India": "Plan around monsoon seasons. Government subsidies available for irrigation and seeds.",
        "Brazil": "No-till farming is common. Consider soybean-maize double cropping.",
        "United States": "Precision agriculture tools available through USDA programs.",
        "Australia": "Drought-resistant varieties are essential. Use conservation agriculture.",
        "Nigeria": "Improved seed varieties and micro-dosing of fertilizers recommended.",
        "France": "EU agricultural subsidies support sustainable practices.",
        "Japan": "Focus on quality. Smart agriculture with drones and sensors is growing.",
        "Thailand": "System of Rice Intensification can produce more rice with less water.",
        "Mexico": "Traditional milpa farming is sustainable. Climate change is shifting zones.",
        "China": "Intensive farming needs careful nutrient management.",
    }
    insight = region_insights.get(country)
    if insight:
        recommendations.append(f"REGION INSIGHT for {country}: {insight}")
    return recommendations


def run_eda(df):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns
    plt.style.use("seaborn-v0_8-whitegrid")
    output_dir = Path("reports/figures")
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Generating EDA charts...")
    numeric_df = df.select_dtypes(include=[np.number])

    # 1. Correlation Heatmap
    fig, ax = plt.subplots(figsize=(10, 8))
    mask = np.triu(np.ones_like(numeric_df.corr(), dtype=bool))
    sns.heatmap(numeric_df.corr(), mask=mask, annot=True, fmt=".2f",
                cmap="RdYlBu_r", center=0, square=True, linewidths=0.5, ax=ax)
    ax.set_title("Feature Correlation Heatmap", fontsize=16, fontweight="bold")
    plt.tight_layout()
    fig.savefig(output_dir / "correlation_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close()

    # 2. Yield Distribution
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    axes[0].hist(df["hg/ha_yield"], bins=50, edgecolor="black", alpha=0.7, color="steelblue")
    axes[0].set_xlabel("Yield (hg/ha)")
    axes[0].set_ylabel("Frequency")
    axes[0].set_title("Yield Distribution")
    axes[0].axvline(df["hg/ha_yield"].mean(), color="red", linestyle="--")
    sns.boxplot(y=df["hg/ha_yield"], ax=axes[1], color="steelblue")
    axes[1].set_title("Yield Box Plot")
    plt.tight_layout()
    fig.savefig(output_dir / "yield_distribution.png", dpi=150, bbox_inches="tight")
    plt.close()

    # 3. Crop-wise Yield
    crop_yield = df.groupby("Item")["hg/ha_yield"].mean().sort_values(ascending=True)
    fig, ax = plt.subplots(figsize=(12, 8))
    crop_yield.plot(kind="barh", ax=ax, color="steelblue", alpha=0.8)
    ax.set_xlabel("Average Yield (hg/ha)")
    ax.set_title("Average Yield by Crop Type", fontsize=16, fontweight="bold")
    plt.tight_layout()
    fig.savefig(output_dir / "crop_wise_yield.png", dpi=150, bbox_inches="tight")
    plt.close()

    # 4. Country-wise Yield
    country_yield = df.groupby("Area")["hg/ha_yield"].mean().nlargest(20).sort_values()
    fig, ax = plt.subplots(figsize=(12, 8))
    country_yield.plot(kind="barh", ax=ax, color="coral", alpha=0.8)
    ax.set_xlabel("Average Yield (hg/ha)")
    ax.set_title("Top 20 Countries by Average Yield", fontsize=16, fontweight="bold")
    plt.tight_layout()
    fig.savefig(output_dir / "country_wise_yield.png", dpi=150, bbox_inches="tight")
    plt.close()

    # 5. Rainfall vs Yield
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(df["average_rain_fall_mm_per_year"], df["hg/ha_yield"], alpha=0.3, s=20, c="steelblue")
    ax.set_xlabel("Annual Rainfall (mm)")
    ax.set_ylabel("Yield (hg/ha)")
    ax.set_title("Rainfall vs Yield", fontweight="bold")
    plt.tight_layout()
    fig.savefig(output_dir / "rainfall_vs_yield.png", dpi=150, bbox_inches="tight")
    plt.close()

    # 6. Temperature vs Yield
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(df["avg_temp"], df["hg/ha_yield"], alpha=0.3, s=20, c="coral")
    ax.set_xlabel("Average Temperature (C)")
    ax.set_ylabel("Yield (hg/ha)")
    ax.set_title("Temperature vs Yield", fontweight="bold")
    plt.tight_layout()
    fig.savefig(output_dir / "temperature_vs_yield.png", dpi=150, bbox_inches="tight")
    plt.close()

    # 7. Yearly Trend
    yearly = df.groupby("Year")["hg/ha_yield"].mean()
    fig, ax = plt.subplots(figsize=(12, 6))
    yearly.plot(ax=ax, linewidth=2, color="green", marker="o", markersize=4)
    ax.set_xlabel("Year")
    ax.set_ylabel("Average Yield (hg/ha)")
    ax.set_title("Average Crop Yield Over Time", fontsize=16, fontweight="bold")
    plt.tight_layout()
    fig.savefig(output_dir / "yearly_trend.png", dpi=150, bbox_inches="tight")
    plt.close()

    # 8. Pesticide vs Yield
    fig, ax = plt.subplots(figsize=(10, 6))
    scatter = ax.scatter(df["pesticides_tonnes"], df["hg/ha_yield"],
                          alpha=0.3, s=20, c=df["avg_temp"], cmap="RdYlBu_r")
    plt.colorbar(scatter, ax=ax, label="Temperature (C)")
    ax.set_xlabel("Pesticide Usage (tonnes)")
    ax.set_ylabel("Yield (hg/ha)")
    ax.set_title("Pesticide Usage vs Yield", fontweight="bold")
    plt.tight_layout()
    fig.savefig(output_dir / "pesticide_vs_yield.png", dpi=150, bbox_inches="tight")
    plt.close()

    logger.info(f"All EDA charts saved to {output_dir}")


def create_app():
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field

    app = FastAPI(title="Crop Yield Estimator API", version="1.0.0")
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                       allow_methods=["*"], allow_headers=["*"])

    class PredictionInput(BaseModel):
        crop: str = Field(..., description="Crop type")
        country: str = Field(..., description="Country")
        rainfall: float = Field(..., gt=0, description="Annual rainfall mm")
        pesticide: float = Field(..., ge=0, description="Pesticide tonnes")
        temperature: float = Field(..., description="Temperature C")
        year: int = Field(..., ge=1961, le=2100, description="Year")

    @app.get("/")
    async def root():
        return {"name": "Crop Yield Estimator API", "version": "1.0.0", "docs": "/docs"}

    @app.get("/health")
    async def health():
        return {"status": "healthy", "model_loaded": Path("models/best_model.joblib").exists()}

    @app.post("/predict")
    async def predict(input_data: PredictionInput):
        try:
            prediction = predict_yield(
                input_data.crop, input_data.country, input_data.rainfall,
                input_data.pesticide, input_data.temperature, input_data.year,
            )
            recs = generate_recommendations(
                input_data.crop, input_data.country, input_data.rainfall,
                input_data.pesticide, input_data.temperature, prediction,
            )
            level = "LOW" if prediction < 20000 else "HIGH" if prediction >= 80000 else "MODERATE"
            return {
                "predicted_yield_hg_ha": round(prediction, 2),
                "predicted_yield_tonnes_ha": round(prediction / 10000, 4),
                "yield_level": level,
                "recommendations": recs,
                "input": input_data.model_dump(),
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/metrics")
    async def metrics():
        p = Path("models/metrics.json")
        if not p.exists():
            raise HTTPException(status_code=404, detail="No metrics. Train first.")
        with open(p, "r") as f:
            return json.load(f)

    @app.post("/recommendations")
    async def recommendations(input_data: PredictionInput):
        try:
            prediction = 50000
            if Path("models/best_model.joblib").exists():
                prediction = predict_yield(
                    input_data.crop, input_data.country, input_data.rainfall,
                    input_data.pesticide, input_data.temperature, input_data.year,
                )
            recs = generate_recommendations(
                input_data.crop, input_data.country, input_data.rainfall,
                input_data.pesticide, input_data.temperature, prediction,
            )
            return {"recommendations": recs}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return app


def run_training_pipeline():
    import joblib
    from sklearn.preprocessing import LabelEncoder

    logger.info("=" * 60)
    logger.info("CROP YIELD ESTIMATOR - TRAINING PIPELINE")
    logger.info("=" * 60)

    # Step 1: Load
    df = load_data()

    # Step 2: Clean
    df = clean_data(df)

    # Step 3: Engineer Features
    df, area_encoder, item_encoder = engineer_features(df)
    feature_cols = get_feature_columns(df)
    logger.info(f"Features for modeling: {len(feature_cols)}")

    # Step 4: Train Models
    training_results = train_models(df, feature_cols)

    # Step 5: Save encoder mappings using save_json (NOT json.dump directly)
    encoder_mappings = {
        "Area": {str(k): int(v) for k, v in zip(area_encoder.classes_, area_encoder.transform(area_encoder.classes_))},
        "Item": {str(k): int(v) for k, v in zip(item_encoder.classes_, item_encoder.transform(item_encoder.classes_))},
    }
    save_json(encoder_mappings, "models/encoder_mappings.json")

    # Step 6: Save known crops and countries using save_json
    save_json(sorted(df["Item"].unique().tolist()), "models/known_crops.json")
    save_json(sorted(df["Area"].unique().tolist()), "models/known_countries.json")

    # Step 7: Run EDA
    run_eda(df)

    # Step 8: Sample prediction
    logger.info("\n" + "=" * 60)
    logger.info("SAMPLE PREDICTION")
    logger.info("=" * 60)
    sample = predict_yield("Rice", "India", 1200, 150, 28, 2025)
    recs = generate_recommendations("Rice", "India", 1200, 150, 28, sample)
    logger.info(f"  Crop: Rice, Country: India, Rainfall: 1200mm")
    logger.info(f"  Pesticide: 150t, Temperature: 28C, Year: 2025")
    logger.info(f"  Predicted Yield: {sample:,.0f} hg/ha ({sample/10000:.2f} tonnes/ha)")
    for rec in recs:
        logger.info(f"  {rec}")

    logger.info("\n" + "=" * 60)
    logger.info("TRAINING PIPELINE COMPLETE!")
    logger.info("=" * 60)
    logger.info("\nNext steps:")
    logger.info("  1. See charts in: reports/figures/")
    logger.info("  2. Start API:     python main.py --mode serve")
    logger.info("  3. Open browser:  http://localhost:8000/docs")

    return training_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crop Yield Estimator")
    parser.add_argument("--mode", choices=["train", "predict", "serve", "eda", "full"],
                        default="train")
    args = parser.parse_args()

    for folder in ["data/raw", "data/processed", "models", "logs", "reports/figures", "configs"]:
        Path(folder).mkdir(parents=True, exist_ok=True)

    if args.mode in ["train", "full"]:
        run_training_pipeline()
    elif args.mode == "predict":
        if not Path("models/best_model.joblib").exists():
            logger.error("No trained model found! Run: python main.py --mode train")
            sys.exit(1)
        result = predict_yield("Rice", "India", 1200, 150, 28, 2025)
        recs = generate_recommendations("Rice", "India", 1200, 150, 28, result)
        print(f"\nPredicted Yield: {result:,.0f} hg/ha ({result/10000:.2f} tonnes/ha)")
        print("\nRecommendations:")
        for i, rec in enumerate(recs, 1):
            print(f"  {i}. {rec}")
    elif args.mode == 'serve':
        import uvicorn
        port = int(os.environ.get('PORT', 8000))
        uvicorn.run(create_app(), host='0.0.0.0', port=port)
    elif args.mode == "eda":
        df = load_data()
        df = clean_data(df)
        run_eda(df)
app = create_app()