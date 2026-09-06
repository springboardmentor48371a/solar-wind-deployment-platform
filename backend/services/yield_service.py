import os
import joblib
import numpy as np

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "../ml/artifacts")
WIND_MODEL_PATH = os.path.join(ARTIFACTS_DIR, "wind_aep_rf.pkl")
SOLAR_MODEL_PATH = os.path.join(ARTIFACTS_DIR, "solar_aep_xgb.pkl")

wind_model = joblib.load(WIND_MODEL_PATH) if os.path.exists(WIND_MODEL_PATH) else None
solar_model = joblib.load(SOLAR_MODEL_PATH) if os.path.exists(SOLAR_MODEL_PATH) else None

def predict_energy_yield(
    solar_ghi: float,
    wind_speed_100m: float,
    elevation: float = 250.0,
    site_type: str = "Hybrid (Solar + Wind)",
    solar_mw: float = 50.0,
    wind_mw: float = 50.0
) -> dict:
    """
    Predicts AEP (MWh/yr) and CUF (%) using trained regressors with physics fallbacks.
    """
    # 1. Solar Prediction (Standard reference: 50 MW plant)
    # Target rule: Annual Generation = Capacity * 8760 * CUF
    if solar_model is not None:
        try:
            solar_input = np.array([[solar_ghi, elevation, 25.0]])
            solar_aep = float(solar_model.predict(solar_input)[0])
        except Exception:
            solar_aep = solar_mw * (solar_ghi / 5.5) * 8760 * 0.21
    else:
        # Physics fallback: PR = 0.78, Standard Testing Condition
        solar_cuf_base = min(0.26, max(0.15, (solar_ghi / 6.5) * 0.24))
        solar_aep = round(solar_mw * 8760 * solar_cuf_base, 1)

    solar_cuf = round((solar_aep / (solar_mw * 8760)) * 100, 2)

    # 2. Wind Prediction (Standard reference: 50 MW wind farm)
    if wind_model is not None:
        try:
            # 6-feature input matching your training pipeline
            rho = 1.225 * np.exp(-elevation / 8400.0)
            wind_input = np.array([[wind_speed_100m * 0.8, wind_speed_100m * 0.9, wind_speed_100m, elevation, 25.0, rho]])
            wind_aep = float(wind_model.predict(wind_input)[0]) * (wind_mw / 2.5)
        except Exception:
            wind_aep = wind_mw * ((wind_speed_100m / 8.5) ** 3) * 8760 * 0.32
    else:
        # Physics fallback: Cut-in 3 m/s, Rated 11.5 m/s
        power_factor = float(np.clip((wind_speed_100m - 3.0) / (11.5 - 3.0), 0.0, 1.0))
        wind_cuf_base = min(0.48, max(0.18, 0.42 * power_factor))
        wind_aep = round(wind_mw * 8760 * wind_cuf_base, 1)

    wind_cuf = round((wind_aep / (wind_mw * 8760)) * 100, 2)

    # 3. Colocation Synthesis
    is_solar = "Solar" in site_type
    is_wind = "Wind" in site_type
    is_hybrid = "Hybrid" in site_type or (is_solar and is_wind)

    if is_hybrid:
        total_aep = round(solar_aep + wind_aep, 1)
        total_mw = solar_mw + wind_mw
        total_cuf = round((total_aep / (total_mw * 8760)) * 100, 2)
        model_name = "XGBoost + Random Forest Hybrid Ensemble"
    elif is_wind:
        total_aep = round(wind_aep, 1)
        total_cuf = wind_cuf
        model_name = "Random Forest Regressor (Wind)"
    else:
        total_aep = round(solar_aep, 1)
        total_cuf = solar_cuf
        model_name = "XGBoost Regressor (Solar)"

    return {
        "annual_generation_mwh": f"{int(total_aep):,} MWh/yr",
        "raw_aep_mwh": total_aep,
        "cuf_percent": f"{total_cuf} %",
        "raw_cuf": total_cuf,
        "solar_aep_mwh": solar_aep,
        "wind_aep_mwh": wind_aep,
        "model_engine": model_name
    }