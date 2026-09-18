"""Small, reproducible ML layer for the academic prototype.

Two Random Forest regressors are trained from a generated development dataset.
The targets are synthetic engineering-style estimates, so this is a demonstration
model, not a validated real-world forecasting model.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

BASE = Path(__file__).resolve().parent
MODEL_DIR = BASE / "models"
MODEL_DIR.mkdir(exist_ok=True)
DATA_DIR = BASE / "data"
DATA_DIR.mkdir(exist_ok=True)
DATA_FILE = DATA_DIR / "renewable_training_data.csv"
SOLAR_FILE = MODEL_DIR / "solar_random_forest.joblib"
WIND_FILE = MODEL_DIR / "wind_random_forest.joblib"
META_FILE = MODEL_DIR / "metrics.joblib"

FEATURES = [
    "solar_irradiance", "wind_speed", "temperature", "rainfall", "cloud_cover",
    "elevation", "slope", "vegetation_index", "roads_distance",
    "transmission_distance", "land_area", "latitude", "longitude", "wind_direction"
]


def make_dataset(n=1800, seed=42):
    rng = np.random.default_rng(seed)
    solar = rng.uniform(2.5, 7.5, n)
    wind = rng.uniform(2.5, 13.0, n)
    temp = rng.uniform(10, 42, n)
    rainfall = rng.uniform(100, 1800, n)
    cloud = rng.uniform(0, 90, n)
    elev = rng.uniform(0, 2200, n)
    slope = rng.uniform(0, 25, n)
    veg = rng.uniform(-0.1, 0.9, n)
    road = rng.uniform(0.2, 30, n)
    transmission = rng.uniform(0.5, 40, n)
    area = rng.uniform(10, 500, n)
    lat = rng.uniform(8, 35, n)
    lon = rng.uniform(68, 90, n)
    direction = rng.uniform(0, 360, n)

    # Development targets: transparent synthetic relationships for model demonstration.
    solar_target = (
        solar * area * 0.18 * 365
        * (1 - cloud / 220)
        * (1 - np.maximum(0, slope - 5) / 120)
        * (1 - np.maximum(0, np.abs(temp - 25) - 8) / 160)
        + rng.normal(0, 70, n)
    )
    wind_target = (
        (wind ** 3) * area * 0.003 * 365
        * (1 - np.maximum(0, slope - 8) / 160)
        * (1 - np.maximum(0, transmission - 20) / 300)
        + rng.normal(0, 90, n)
    )
    df = pd.DataFrame({
        "solar_irradiance": solar, "wind_speed": wind, "temperature": temp,
        "rainfall": rainfall, "cloud_cover": cloud, "elevation": elev,
        "slope": slope, "vegetation_index": veg, "roads_distance": road,
        "transmission_distance": transmission, "land_area": area,
        "latitude": lat, "longitude": lon, "wind_direction": direction,
        "solar_mwh_year": np.maximum(0, solar_target),
        "wind_mwh_year": np.maximum(0, wind_target),
    })
    return df


def train_models(force=False):
    if not force and SOLAR_FILE.exists() and WIND_FILE.exists() and META_FILE.exists() and DATA_FILE.exists():
        return load_models()

    df = make_dataset()
    df.to_csv(DATA_FILE, index=False)
    X = df[FEATURES]
    y_solar = df["solar_mwh_year"]
    y_wind = df["wind_mwh_year"]
    X_train, X_test, ys_train, ys_test, yw_train, yw_test = train_test_split(
        X, y_solar, y_wind, test_size=0.2, random_state=42
    )

    solar_model = RandomForestRegressor(n_estimators=250, random_state=42, n_jobs=-1, min_samples_leaf=2)
    wind_model = RandomForestRegressor(n_estimators=250, random_state=42, n_jobs=-1, min_samples_leaf=2)
    solar_model.fit(X_train, ys_train)
    wind_model.fit(X_train, yw_train)

    solar_pred = solar_model.predict(X_test)
    wind_pred = wind_model.predict(X_test)
    metrics = {
        "solar_mae": float(mean_absolute_error(ys_test, solar_pred)),
        "solar_r2": float(r2_score(ys_test, solar_pred)),
        "wind_mae": float(mean_absolute_error(yw_test, wind_pred)),
        "wind_r2": float(r2_score(yw_test, wind_pred)),
        "model": "Random Forest Regressor",
        "training_rows": len(df),
        "features": FEATURES,
        "data_note": "Synthetic development dataset; replace with validated historical observations for production.",
    }
    joblib.dump(solar_model, SOLAR_FILE)
    joblib.dump(wind_model, WIND_FILE)
    joblib.dump(metrics, META_FILE)
    return solar_model, wind_model, metrics


def load_models():
    if not (SOLAR_FILE.exists() and WIND_FILE.exists() and META_FILE.exists()):
        return train_models(force=True)
    return joblib.load(SOLAR_FILE), joblib.load(WIND_FILE), joblib.load(META_FILE)


def predict_site(site):
    solar_model, wind_model, metrics = load_models()
    row = pd.DataFrame([{f: float(site.get(f, 0) or 0) for f in FEATURES}])
    solar = max(0.0, float(solar_model.predict(row)[0]))
    wind = max(0.0, float(wind_model.predict(row)[0]))
    return {
        "ml_model": metrics["model"],
        "ml_solar_mwh_year": round(solar, 1),
        "ml_wind_mwh_year": round(wind, 1),
        "ml_total_mwh_year": round(solar + wind, 1),
        "solar_model_r2": round(metrics["solar_r2"], 3),
        "wind_model_r2": round(metrics["wind_r2"], 3),
    }


SOLAR_MODEL, WIND_MODEL, MODEL_METRICS = train_models()
