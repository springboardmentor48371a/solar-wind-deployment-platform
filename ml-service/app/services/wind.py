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

def predict_wind(wind_speed: float, wind_speed_50m: float | None, wind_direction: float, temperature_avg: float = None) -> dict:
    if model is None:
        return {"wind_power_kw": None, "wind_capacity_factor": None, "wind_score": None}

    # Use 50 m wind speed if available — closer to turbine hub height (~80–100 m).
    # 10 m wind speed (WS10M) is too low and produces near-zero scores.
    effective_speed = wind_speed_50m if wind_speed_50m is not None else wind_speed

    now = datetime.utcnow()
    hour  = now.hour
    month = now.month

    # Engineered features — must match training order exactly
    wind_speed_cubed     = effective_speed ** 3
    # Rotor area = π × r²  where r = 41 m → A ≈ 5,281 m²
    theoretical_power    = wind_speed_cubed * 0.5 * 1.225 * (np.pi * 41.0**2) / 1000
    sin_wind_dir         = np.sin(np.radians(wind_direction))
    cos_wind_dir         = np.cos(np.radians(wind_direction))
    sin_hour             = np.sin(2 * np.pi * hour / 24)
    cos_hour             = np.cos(2 * np.pi * hour / 24)
    wind_speed_lag_1     = effective_speed
    wind_speed_roll_mean = effective_speed

    features = np.array([[
        effective_speed,
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
        power_kw = max(0.0, 0.35 * 0.5 * 1.225 * (np.pi * 41.0**2) * effective_speed**3 / 1000)
    capacity_factor = min(power_kw / 2000.0, 1.0)
    score           = min(round(capacity_factor / 0.35 * 100, 2), 100.0)

    return {
        "wind_power_kw":       round(power_kw, 2),
        "wind_capacity_factor": round(capacity_factor, 4),
        "wind_score":           score,
    }
