"""
Trains the ML-Assisted Wind Capacity Factor model against real, measured
turbine SCADA data — mirrors train_solar_model.py's approach for wind.

=====================================================================
DATASET — why this one
=====================================================================
Kelmarsh Wind Farm SCADA data (Zenodo, Cubico Sustainable Investments Ltd,
CC-BY-4.0): https://zenodo.org/records/5841834

Real 10-minute SCADA readings from 6 actual Senvion MM92 turbines (2.05MW
each) in Northamptonshire, UK, spanning 2016-2021. Real measured wind
speed and real measured power output — not a simulation.

Expects the raw Greenbyte-format export files exactly as Zenodo provides
them, e.g. "Turbine_Data_Kelmarsh_1_2016-01-03_-_2017-01-01_228.csv"
inside a "Kelmarsh_SCADA_<year>_<id>.zip" file. Pass the zip file(s) via
--zip-path (repeatable) and the turbine CSV name(s) via --csv-name
(repeatable, same order).

=====================================================================
KNOWN SIMPLIFICATION — read this before trusting the model blindly
=====================================================================
Kelmarsh's wind speed sensor is a nacelle-mounted anemometer at actual
hub height (~90m for the MM92), not the 50m reference height NASA
POWER's WS50M parameter provides. This script applies the same
wind-shear extrapolation transform used at serve time (see
app/services/ml_wind_predictor.py) to keep train/serve feature
engineering consistent — it does NOT claim this real sensor physically
needed shear-extrapolating. Site elevation is held constant (single
real site) since this dataset has no per-row elevation variation, so
the trained model has not learned genuine elevation sensitivity.
"""

import argparse
import json
import os
import sys
import datetime
import zipfile
import io

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "app", "ml_models")
MODEL_PATH = os.path.join(MODEL_DIR, "wind_capacity_factor_rf.joblib")
METADATA_PATH = os.path.join(MODEL_DIR, "wind_capacity_factor_rf.meta.json")


def load_turbine_csv(zip_path: str, csv_name: str) -> pd.DataFrame:
    with zipfile.ZipFile(zip_path) as zf:
        with zf.open(csv_name) as f:
            # Real Greenbyte export quirk: even the header row is
            # prefixed with "# " — strip it after loading.
            df = pd.read_csv(
                io.TextIOWrapper(f, encoding="utf-8"),
                skiprows=9,
                usecols=lambda c: c.strip("# ") in ("Date and time", "Wind speed (m/s)", "Power (kW)"),
            )
    df.columns = [c.strip("# ").strip() for c in df.columns]
    return df


def train(zip_csv_pairs: list[tuple[str, str]], rated_capacity_kw: float, site_elevation_m: float) -> None:
    frames = []
    for zip_path, csv_name in zip_csv_pairs:
        print(f"Loading {csv_name} from {zip_path}...")
        frames.append(load_turbine_csv(zip_path, csv_name))
    raw = pd.concat(frames, ignore_index=True)
    print(f"Loaded {len(raw)} raw readings across {len(zip_csv_pairs)} turbine file(s).")

    raw = raw.dropna(subset=["Wind speed (m/s)", "Power (kW)"])
    raw = raw[raw["Wind speed (m/s)"] >= 0]
    raw["capacity_factor_pct"] = (raw["Power (kW)"] / rated_capacity_kw * 100).clip(0, 105)
    raw = raw[raw["capacity_factor_pct"] <= 105]
    print(f"{len(raw)} rows remain after cleaning.")

    raw["wind_speed_50m"] = raw["Wind speed (m/s)"]
    raw["elevation_m"] = site_elevation_m
    raw["hub_wind_speed"] = raw["wind_speed_50m"] * (80.0 / 50.0) ** (1.0 / 7.0)

    X = raw[["wind_speed_50m", "elevation_m", "hub_wind_speed"]]
    y = raw["capacity_factor_pct"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=100, max_depth=10, min_samples_leaf=10, random_state=42)
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    rmse = float(np.sqrt(mean_squared_error(y_test, predictions)))
    mae = float(mean_absolute_error(y_test, predictions))
    r2 = float(r2_score(y_test, predictions))

    print("\n=== Held-out test set accuracy (read this, don't assume it) ===")
    print(f"RMSE: {rmse:.2f} percentage points")
    print(f"MAE:  {mae:.2f} percentage points")
    print(f"R^2:  {r2:.3f}")

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH, compress=3)
    with open(METADATA_PATH, "w") as f:
        json.dump(
            {
                "version": f"rf_v1_real_{datetime.date.today().isoformat()}",
                "trained_on_rows": len(raw),
                "training_data_type": "REAL measured turbine SCADA telemetry (not synthetic)",
                "data_source_url": "https://zenodo.org/records/5841834",
                "data_license": "CC-BY-4.0, Cubico Sustainable Investments Ltd",
                "rated_capacity_kw_used": rated_capacity_kw,
                "site_elevation_m_used": site_elevation_m,
                "test_rmse": rmse,
                "test_mae": mae,
                "test_r2": r2,
                "feature_columns": ["wind_speed_50m", "elevation_m", "hub_wind_speed"],
            },
            f,
            indent=2,
        )
    print(f"\nModel saved to {MODEL_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--zip-path", action="append", required=True, help="Path to a Kelmarsh_SCADA_<year>.zip file (repeatable)")
    parser.add_argument("--csv-name", action="append", required=True, help="Turbine CSV filename inside that zip (repeatable, same order as --zip-path)")
    parser.add_argument("--rated-capacity-kw", type=float, default=2050.0, help="Turbine nameplate rating (default: 2050 kW, Senvion MM92)")
    parser.add_argument("--site-elevation-m", type=float, default=140.0, help="Site elevation in meters (default: ~140m, Kelmarsh, Northamptonshire UK)")
    args = parser.parse_args()

    if len(args.zip_path) != len(args.csv_name):
        print("Error: --zip-path and --csv-name must be given the same number of times.", file=sys.stderr)
        sys.exit(1)

    train(list(zip(args.zip_path, args.csv_name)), args.rated_capacity_kw, args.site_elevation_m)
