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

    # NASA POWER delivers kWh/m²/day (daily total insolation).
    # The model expects mean hourly irradiance (kW/m²) — divide by 24.
    irradiance_hourly = solar_irradiance / 24.0

    # Score directly from irradiance rather than the ML capacity factor.
    # The model was trained on instantaneous SCADA readings with time-of-day
    # features (sin/cos hour) that are inconsistent with averaged daily inputs —
    # feeding a 30-day mean irradiance with the current wall-clock hour produces
    # unreliable capacity factors that saturate at 100 for almost every site.
    #
    # Benchmark: 0.21 kW/m² mean hourly irradiance ≈ 5.0 kWh/m²/day, which
    # corresponds to a strong solar resource (top ~25% globally per NASA POWER).
    # Sites above this threshold score 100; sites scale linearly below it.
    BENCHMARK_HOURLY = 0.21  # kW/m²
    raw_score = (irradiance_hourly / BENCHMARK_HOURLY) * 100.0

    # Apply a cloud cover penalty on top — two sites with the same mean irradiance
    # but different cloud cover have different reliability/predictability.
    cloud_fraction = (cloud_cover or 0.0) / 100.0
    cloud_penalty  = cloud_fraction * 15.0  # max 15-point penalty at 100% cloud cover
    score = round(min(max(raw_score - cloud_penalty, 0.0), 100.0), 2)

    # Still run the model to get capacity_factor and yield for display purposes,
    # but do not use the model output for the score.
    temp_delta = (module_temp - temperature_avg) if module_temp is not None else max(0.0, (1 - cloud_fraction) * 15)
    now = datetime.utcnow()
    hour = now.hour
    sin_time = np.sin(2 * np.pi * hour / 24)
    cos_time = np.cos(2 * np.pi * hour / 24)
    inv_perf = max(0.0, (1 - cloud_fraction) * min(irradiance_hourly / 0.6, 1.0))
    features = np.array([[
        irradiance_hourly, temperature_avg, cloud_cover, temp_delta,
        sin_time, cos_time, inv_perf,
        irradiance_hourly, irradiance_hourly, irradiance_hourly,
    ]])
    capacity_factor = float(np.clip(model.predict(features)[0], 0.0, 1.0))
    solar_yield_kwh = round(capacity_factor * 24.0, 2)

    return {
        "solar_yield_kwh": solar_yield_kwh,
        "solar_capacity_factor": round(capacity_factor, 4),
        "solar_score": score,
    }
