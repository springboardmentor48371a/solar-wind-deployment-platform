import joblib
import numpy as np
from pathlib import Path
from datetime import datetime

MODEL_PATH = next(
    (p for p in [
        Path(__file__).parent.parent / "models" / "solar_model.pkl",
        Path(__file__).parent.parent / "models" / "solar_model2.pkl",
    ] if p.exists()),
    Path(__file__).parent.parent / "models" / "solar_model.pkl",
)

model = None

def load_model():
    global model
    if MODEL_PATH.exists():
        model = joblib.load(MODEL_PATH)

def predict_solar(solar_irradiance: float, temperature_avg: float, cloud_cover: float, peak_sun_hours: float, module_temp: float | None = None) -> dict:
    if model is None:
        return {"solar_yield_kwh": None, "solar_capacity_factor": None, "solar_score": None}

    # Scale daily insolation (kWh/m²/day) to daily mean hourly irradiance (kW/m²) expected by the model
    solar_irradiance = solar_irradiance / 24.0

    temp_delta = (module_temp - temperature_avg) if module_temp is not None else max(0.0, (1 - cloud_cover / 100) * 15)

    now = datetime.utcnow()
    hour = now.hour
    sin_time = np.sin(2 * np.pi * hour / 24)
    cos_time = np.cos(2 * np.pi * hour / 24)

    # inv_perf: inverter performance proxy — estimated from irradiance and cloud cover
    inv_perf = max(0.0, (1 - cloud_cover / 100) * min(solar_irradiance / 0.6, 1.0))

    # lag/rolling features — no history at prediction time, use current irradiance as proxy
    irr_lag_1     = solar_irradiance
    irr_lag_2     = solar_irradiance
    irr_roll_mean = solar_irradiance

    # FEATURES order must match training exactly:
    # solar_irradiance, temperature_avg, cloud_cover, temp_delta,
    # sin_time, cos_time, inv_perf, irr_lag_1, irr_lag_2, irr_roll_mean
    features = np.array([[
        solar_irradiance,
        temperature_avg,
        cloud_cover,
        temp_delta,
        sin_time,
        cos_time,
        inv_perf,
        irr_lag_1,
        irr_lag_2,
        irr_roll_mean,
    ]])

    capacity_factor = float(np.clip(model.predict(features)[0], 0.0, 1.0))
    solar_yield_kwh = round(capacity_factor * 24.0, 2)
    score = min(round(capacity_factor / 0.25 * 100, 2), 100.0)

    return {
        "solar_yield_kwh": solar_yield_kwh,
        "solar_capacity_factor": round(capacity_factor, 4),
        "solar_score": score,
    }
