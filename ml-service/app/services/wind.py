import joblib
import numpy as np
from pathlib import Path
from datetime import datetime

MODEL_PATH = Path(__file__).parent.parent / "models" / "wind_model.pkl"

model = None

def load_model():
    global model
    if MODEL_PATH.exists():
        model = joblib.load(MODEL_PATH)

def predict_wind(wind_speed: float, wind_direction: float, temperature_avg: float = None) -> dict:
    if model is None:
        return {"wind_power_kw": None, "wind_capacity_factor": None, "wind_score": None}

    now = datetime.utcnow()
    hour  = now.hour
    month = now.month

    # Engineered features — must match training order exactly
    wind_speed_cubed     = wind_speed ** 3
    theoretical_power    = wind_speed_cubed * 0.5 * 1.225 * (41.0 ** 2) * np.pi / 4 / 1000  # Betz limit estimate
    sin_wind_dir         = np.sin(np.radians(wind_direction))
    cos_wind_dir         = np.cos(np.radians(wind_direction))
    sin_hour             = np.sin(2 * np.pi * hour / 24)
    cos_hour             = np.cos(2 * np.pi * hour / 24)
    wind_speed_lag_1     = wind_speed       # no history at prediction time — use current as proxy
    wind_speed_roll_mean = wind_speed       # no rolling window at prediction time — use current as proxy

    features = np.array([[
        wind_speed,
        wind_speed_cubed,
        theoretical_power,
        sin_wind_dir,
        cos_wind_dir,
        sin_hour,
        cos_hour,
        month,
        wind_speed_lag_1,
        wind_speed_roll_mean,
    ]])

    power_kw = float(model.predict(features)[0])

    # Model predicts negative below cut-in speed (~9 m/s for the SCADA turbine).
    # Fall back to Betz-limit power curve for low wind speeds.
    if power_kw < 0:
        # P = 0.5 * Cp * rho * A * v^3, Cp=0.35 (realistic), rotor radius=41m
        power_kw = max(0.0, 0.35 * 0.5 * 1.225 * (np.pi * 41.0**2) * wind_speed**3 / 1000)
    capacity_factor = min(power_kw / 2000.0, 1.0)
    score           = min(round(capacity_factor / 0.35 * 100, 2), 100.0)

    return {
        "wind_power_kw":       round(power_kw, 2),
        "wind_capacity_factor": round(capacity_factor, 4),
        "wind_score":           score,
    }
