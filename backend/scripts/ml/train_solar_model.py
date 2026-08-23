"""
Trains the ML-Assisted Solar Performance Prediction model (Beta) against
real, measured solar plant data — not the physics engine's own output.

This is an offline, run-it-yourself script. It is NOT called by the live
API (see app/services/ml_solar_predictor.py for that side). Run it once
after downloading the dataset below; the app picks up the resulting
model file automatically on next use (or next container start) — no
code changes needed elsewhere.

=====================================================================
DATASET — why this one
=====================================================================
"Solar Power Generation Data" (Kaggle, ANIKANNAL):
https://www.kaggle.com/datasets/anikannal/solar-power-generation-data

Real, measured inverter-level AC/DC power and plant-level weather sensor
readings from two grid-connected solar plants in India, 15-minute
resolution, 34 days, ~140,000 rows. This is actual generation data, not
a physics simulation — which is the entire point of adding an ML layer:
a model trained on real outcomes can in principle learn real-world
effects (soiling, inverter clipping, real temperature response) that a
hand-written formula can only approximate.

Free Kaggle account required to download (no cost). This script expects
the 4 files exactly as Kaggle provides them:
    Plant_1_Generation_Data.csv     Plant_1_Weather_Sensor_Data.csv
    Plant_2_Generation_Data.csv     Plant_2_Weather_Sensor_Data.csv
Place all four in the same directory and pass that directory as the
--data-dir argument (see bottom of this file).

=====================================================================
WHAT IS ACTUALLY BEING PREDICTED, AND WHY
=====================================================================
The raw target column (AC_POWER, in kW) isn't directly usable: it's
specific to each plant's installed capacity, which our app has no way
to know for an arbitrary new site. Instead this trains on **Performance
Ratio** — actual output divided by theoretical output at that
irradiance — the same normalized 0-100% metric solar_engine.py's
physics formula already computes as `performance_ratio_pct`. This
makes the ML output and the physics output directly comparable at
inference time, and means the model transfers to any site regardless
of installed capacity.

Rated capacity per inverter isn't given as a column, so it's estimated
robustly from the data itself: the 99th percentile of AC_POWER observed
when irradiation was high (>0.8, i.e. near-full sun) is a standard,
defensible proxy for nameplate capacity when the true value isn't
directly available.

=====================================================================
HONESTY NOTE
=====================================================================
This script prints real RMSE / MAE / R^2 on a held-out test split every
time it runs — read that output, don't assume a number. If the trained
model's test-set accuracy isn't clearly better than the existing physics
formula would produce, the honest conclusion is to keep using the
physics formula and treat this as a documented, unsuccessful experiment
— not to ship a worse model because it says "AI" on it.
"""

import argparse
import json
import os
import sys
import datetime

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib

FEATURE_COLUMNS = ["ambient_temperature", "irradiation", "temp_x_irradiance"]
TARGET_COLUMN = "performance_ratio_pct"

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "app", "ml_models")
MODEL_PATH = os.path.join(MODEL_DIR, "solar_performance_ratio_rf.joblib")
METADATA_PATH = os.path.join(MODEL_DIR, "solar_performance_ratio_rf.meta.json")


def load_and_join(data_dir: str, plant_num: int) -> pd.DataFrame:
    gen_path = os.path.join(data_dir, f"Plant_{plant_num}_Generation_Data.csv")
    weather_path = os.path.join(data_dir, f"Plant_{plant_num}_Weather_Sensor_Data.csv")
    if not os.path.exists(gen_path) or not os.path.exists(weather_path):
        raise FileNotFoundError(
            f"Expected {gen_path} and {weather_path} — see this script's docstring "
            "for the exact Kaggle dataset and filenames expected."
        )

    gen = pd.read_csv(gen_path)
    weather = pd.read_csv(weather_path)

    # Kaggle's two files use slightly different DATE_TIME string formats
    # across the two plants' exports — parse permissively rather than
    # assuming one fixed format.
    gen["DATE_TIME"] = pd.to_datetime(gen["DATE_TIME"], dayfirst=True, errors="coerce")
    weather["DATE_TIME"] = pd.to_datetime(weather["DATE_TIME"], dayfirst=True, errors="coerce")

    # Generation is per-inverter (multiple SOURCE_KEY rows per timestamp);
    # weather is plant-level (one row per timestamp). Aggregate generation
    # to plant-level AC_POWER per timestamp so the two join cleanly.
    gen_agg = gen.groupby("DATE_TIME", as_index=False)["AC_POWER"].sum()

    merged = pd.merge(gen_agg, weather, on="DATE_TIME", how="inner")
    merged = merged.dropna(subset=["AC_POWER", "AMBIENT_TEMPERATURE", "IRRADIATION"])
    return merged


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.rename(columns={"AMBIENT_TEMPERATURE": "ambient_temperature", "IRRADIATION": "irradiation"})

    # Rated capacity proxy: 99th percentile of AC_POWER during
    # near-full-sun conditions. Robust to a handful of outlier spikes
    # without needing the true nameplate rating as an input.
    high_sun = df[df["irradiation"] > 0.8]
    if len(high_sun) < 10:
        raise ValueError("Not enough high-irradiance rows to estimate rated capacity reliably — check the data.")
    estimated_capacity_kw = high_sun["AC_POWER"].quantile(0.99)

    # Performance Ratio: actual output vs theoretical output at that
    # irradiance. irradiation is already normalized to STC (1.0 = full
    # 1000 W/m^2), so theoretical output = capacity * irradiation.
    theoretical_output = estimated_capacity_kw * df["irradiation"].clip(lower=0.01)
    df[TARGET_COLUMN] = (df["AC_POWER"] / theoretical_output * 100).clip(0, 150)
    # Drop physically implausible rows (near-zero irradiance divisions,
    # sensor glitches) rather than let them distort training.
    df = df[(df["irradiation"] > 0.02) & (df[TARGET_COLUMN] <= 150)]

    df["temp_x_irradiance"] = df["ambient_temperature"] * df["irradiation"]
    return df, estimated_capacity_kw


def train(data_dir: str, plants: list[int]) -> None:
    frames = []
    for plant_num in plants:
        print(f"Loading and joining Plant {plant_num} data...")
        frames.append(load_and_join(data_dir, plant_num))
    raw = pd.concat(frames, ignore_index=True)
    print(f"Loaded {len(raw)} joined generation+weather rows across {len(plants)} plant(s).")

    df, estimated_capacity_kw = engineer_features(raw)
    print(f"Estimated rated capacity used for normalization: {estimated_capacity_kw:.1f} kW")
    print(f"{len(df)} rows remain after removing implausible/low-irradiance rows.")

    X = df[["ambient_temperature", "irradiation", "temp_x_irradiance"]]
    y = df[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=100, max_depth=10, min_samples_leaf=5, random_state=42)
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    rmse = float(np.sqrt(mean_squared_error(y_test, predictions)))
    mae = float(mean_absolute_error(y_test, predictions))
    r2 = float(r2_score(y_test, predictions))

    print("\n=== Held-out test set accuracy (read this, don't assume it) ===")
    print(f"RMSE: {rmse:.2f} percentage points")
    print(f"MAE:  {mae:.2f} percentage points")
    print(f"R^2:  {r2:.3f}")
    print(
        "\nFor context: the physics formula in solar_engine.py clamps performance "
        "ratio to a 40-88% band. If RMSE here is large relative to that ~48-point "
        "range, or R^2 is close to 0, this model is not yet reliable enough to "
        "trust over the physics baseline — that's a legitimate, honest outcome, "
        "not a failure of the pipeline."
    )

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    with open(METADATA_PATH, "w") as f:
        json.dump(
            {
                "version": f"rf_v1_{datetime.date.today().isoformat()}",
                "trained_on_rows": len(df),
                "plants_used": plants,
                "estimated_capacity_kw": estimated_capacity_kw,
                "test_rmse": rmse,
                "test_mae": mae,
                "test_r2": r2,
                "feature_columns": FEATURE_COLUMNS,
            },
            f,
            indent=2,
        )
    print(f"\nModel saved to {MODEL_PATH}")
    print(f"Metadata saved to {METADATA_PATH}")
    print("Restart the backend container (or it'll pick this up on next site computation) to start using it.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", required=True, help="Directory containing the 4 Kaggle CSV files")
    parser.add_argument("--plants", default="1,2", help="Comma-separated plant numbers to train on (default: 1,2)")
    args = parser.parse_args()

    plant_list = [int(p.strip()) for p in args.plants.split(",")]
    try:
        train(args.data_dir, plant_list)
    except FileNotFoundError as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        sys.exit(1)
