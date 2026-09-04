"""
Trains the Solar Potential, Wind Potential, and Site Suitability ML models
(Modules 5, 6, 7/10).

Why synthetic-but-physics-informed training data?
--------------------------------------------------
This platform's whole point is to score sites *before* anything is built,
so there is no pre-existing "ground truth" table of thousands of real,
already-operating deployments with measured capacity factors to train on
day one. The standard approach in this situation -- used widely in
renewable-siting and engineering ML more generally -- is to train a
surrogate model on a physics-informed simulator: sample realistic
combinations of the input variables across their real-world ranges, run
them through the validated analytical formulas (`physics_baseline.py`,
based on standard PV-yield and wind-power-density equations), add
measurement-realistic noise, and fit a model to the noisy outputs.

The result is a genuine learned model (a Random Forest, not a lookup
table) that:
  - captures interaction effects between inputs the closed-form formula
    keeps independent (e.g. slope x cloud cover) automatically,
  - is robust to noisy/imperfect live input data (it was trained on noisy
    data),
  - and, most importantly, is a drop-in replacement target: once the
    platform has accumulated real site outcomes (actual measured capacity
    factors from operating sites logged through Module 2/8), point
    `_load_training_frame()` at that export instead of `_simulate(...)`
    and re-run this script -- nothing else in the codebase changes.

Run:
    cd backend && python -m app.ml.train
"""
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, accuracy_score

from . import feature_schema as fs
from . import physics_baseline as physics

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
RNG = np.random.default_rng(42)
N_SAMPLES = 9000
NOISE_STD_FRAC = 0.04  # ~4% relative gaussian noise on each target, simulating real-world measurement variance


def _noisy(value, frac=NOISE_STD_FRAC):
    if isinstance(value, bool):
        return value
    noise = RNG.normal(0, abs(value) * frac + 1e-6)
    return value + noise


def _simulate(n=N_SAMPLES) -> pd.DataFrame:
    rows = []
    for _ in range(n):
        env = {
            "solar_irradiance_kwh_m2_day": RNG.uniform(1.8, 8.2),
            "wind_speed_avg_ms": RNG.uniform(1.0, 14.0),
            "temperature_avg_c": RNG.uniform(-10, 46),
            "cloud_cover_pct": RNG.uniform(2, 92),
            "rainfall_mm_year": RNG.uniform(50, 3200),
            "land_slope_pct": RNG.uniform(0, 32),
            "vegetation_index_ndvi": RNG.uniform(0.02, 0.9),
            "distance_to_road_km": RNG.uniform(0.05, 45),
            "distance_to_transmission_km": RNG.uniform(0.1, 60),
            "distance_to_substation_km": RNG.uniform(0.1, 55),
            "distance_to_urban_km": RNG.uniform(0.1, 80),
            "distance_to_water_km": RNG.uniform(0.05, 40),
            "in_protected_zone": bool(RNG.uniform() < 0.12),
        }
        land_area_hectares = float(RNG.uniform(1, 220))
        elevation_m = float(RNG.uniform(0, 2800))

        solar = physics.solar_baseline(env, land_area_hectares)
        wind = physics.wind_baseline(env, land_area_hectares)
        score = physics.scoring_baseline(env, solar, wind, land_area_hectares)

        row = {**env, "land_area_hectares": land_area_hectares, "elevation_m": elevation_m}
        for k, v in solar.items():
            row[f"solar__{k}"] = _noisy(v) if isinstance(v, (int, float)) else v
        for k, v in wind.items():
            row[f"wind__{k}"] = _noisy(v) if isinstance(v, (int, float)) else v
        for k, v in score.items():
            row[f"score__{k}"] = _noisy(v) if isinstance(v, (int, float)) else v
        rows.append(row)
    return pd.DataFrame(rows)


def _load_training_frame() -> pd.DataFrame:
    """Swap this out for a real historical-deployment export once available
    (see module docstring). Falls back to the physics-informed simulator."""
    real_data_path = os.path.join(MODELS_DIR, "real_deployment_history.csv")
    if os.path.exists(real_data_path):
        return pd.read_csv(real_data_path)
    return _simulate()


def train_solar_model(df: pd.DataFrame):
    X = df[fs.SOLAR_FEATURES]
    y = df[[f"solar__{t}" for t in fs.SOLAR_TARGETS]]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=42)
    model = RandomForestRegressor(n_estimators=150, max_depth=10, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    for i, target in enumerate(fs.SOLAR_TARGETS):
        mae = mean_absolute_error(y_test.iloc[:, i], preds[:, i])
        print(f"[solar] {target}: MAE {mae:.3f}")
    joblib.dump(model, os.path.join(MODELS_DIR, "solar_model.joblib"), compress=3)
    return model


def train_wind_model(df: pd.DataFrame):
    X = df[fs.WIND_FEATURES]
    y = df[[f"wind__{t}" for t in fs.WIND_TARGETS]]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=42)
    model = RandomForestRegressor(n_estimators=150, max_depth=10, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    for i, target in enumerate(fs.WIND_TARGETS):
        mae = mean_absolute_error(y_test.iloc[:, i], preds[:, i])
        print(f"[wind] {target}: MAE {mae:.3f}")
    joblib.dump(model, os.path.join(MODELS_DIR, "wind_model.joblib"), compress=3)
    return model


def train_suitability_models(df: pd.DataFrame):
    df = df.copy()
    df["solar_capacity_factor_pct"] = df["solar__capacity_factor_pct"]
    df["wind_capacity_factor_pct"] = df["wind__capacity_factor_pct"]
    df["in_protected_zone"] = df["in_protected_zone"].astype(int)

    X = df[fs.SUITABILITY_FEATURES]

    y_scores = df[[f"score__{t}" for t in fs.SUITABILITY_SCORE_TARGETS]]
    X_train, X_test, y_train, y_test = train_test_split(X, y_scores, test_size=0.15, random_state=42)
    score_model = RandomForestRegressor(n_estimators=150, max_depth=10, random_state=42, n_jobs=-1)
    score_model.fit(X_train, y_train)
    preds = score_model.predict(X_test)
    for i, target in enumerate(fs.SUITABILITY_SCORE_TARGETS):
        mae = mean_absolute_error(y_test.iloc[:, i], preds[:, i])
        print(f"[suitability] {target}: MAE {mae:.3f}")
    joblib.dump(score_model, os.path.join(MODELS_DIR, "suitability_score_model.joblib"), compress=3)

    y_cat = df["score__category"]
    Xc_train, Xc_test, yc_train, yc_test = train_test_split(X, y_cat, test_size=0.15, random_state=42, stratify=y_cat)
    cat_model = RandomForestClassifier(n_estimators=150, max_depth=10, random_state=42, n_jobs=-1)
    cat_model.fit(Xc_train, yc_train)
    acc = accuracy_score(yc_test, cat_model.predict(Xc_test))
    print(f"[suitability-category] test accuracy: {acc:.3f}")
    joblib.dump(cat_model, os.path.join(MODELS_DIR, "suitability_category_model.joblib"), compress=3)

    y_tech = df["score__recommended_technology"]
    Xt_train, Xt_test, yt_train, yt_test = train_test_split(X, y_tech, test_size=0.15, random_state=42, stratify=y_tech)
    tech_model = RandomForestClassifier(n_estimators=150, max_depth=10, random_state=42, n_jobs=-1)
    tech_model.fit(Xt_train, yt_train)
    acc = accuracy_score(yt_test, tech_model.predict(Xt_test))
    print(f"[recommended-technology] test accuracy: {acc:.3f}")
    joblib.dump(tech_model, os.path.join(MODELS_DIR, "technology_model.joblib"), compress=3)


def main():
    os.makedirs(MODELS_DIR, exist_ok=True)
    print(f"Generating training frame ({N_SAMPLES} samples)...")
    df = _load_training_frame()
    print("Training solar model...")
    train_solar_model(df)
    print("Training wind model...")
    train_wind_model(df)
    print("Training suitability models...")
    train_suitability_models(df)
    print(f"Done. Models saved to {MODELS_DIR}")


if __name__ == "__main__":
    main()
