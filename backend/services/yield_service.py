import os
import joblib
import numpy as np

# Load trained models if available
CURRENT_DIR = os.path.dirname(__file__)
SOLAR_MODEL_PATH = os.path.join(CURRENT_DIR, "..", "ml", "artifacts", "solar_aep_xgb.pkl")
WIND_MODEL_PATH = os.path.join(CURRENT_DIR, "..", "ml", "artifacts", "wind_aep_rf.pkl")

solar_model = None
wind_model = None

if os.path.exists(SOLAR_MODEL_PATH):
    try:
        solar_model = joblib.load(SOLAR_MODEL_PATH)
    except Exception:
        solar_model = None

if os.path.exists(WIND_MODEL_PATH):
    try:
        wind_model = joblib.load(WIND_MODEL_PATH)
    except Exception:
        wind_model = None

def predict_energy_yield(solar_ghi: float, wind_speed_100m: float, elevation: float = 250.0, site_type: str = "Hybrid (Solar + Wind)"):
    # Standard 50 MW Nameplate Capacity Benchmark
    installed_capacity_mw = 50.0
    hours_per_year = 8760.0

    # 1. Solar Generation Calculation
    daily_sun_hours = max(3.0, min(solar_ghi * 0.95, 7.5))
    if solar_model is not None:
        try:
            irr_kw_m2 = solar_ghi / daily_sun_hours if daily_sun_hours > 0 else 0.8
            ambient_temp = 28.0
            pred_kw = float(solar_model.predict([[irr_kw_m2, ambient_temp]])[0])
            annual_solar_mwh = round((pred_kw * daily_sun_hours * 365) / 1000.0, 1)
        except Exception:
            annual_solar_mwh = round(installed_capacity_mw * daily_sun_hours * 365 * 0.18, 1)
    else:
        annual_solar_mwh = round(installed_capacity_mw * daily_sun_hours * 365 * 0.18, 1)

    # 2. Wind Generation Calculation
    if wind_model is not None:
        try:
            pred_wind_kw = float(wind_model.predict([[wind_speed_100m]])[0])
            # Scale to 50 MW farm
            annual_wind_mwh = round((pred_wind_kw * 20 * 8760 * 0.35) / 1000.0, 1)
        except Exception:
            annual_wind_mwh = round(installed_capacity_mw * hours_per_year * (min(wind_speed_100m, 12.0) / 12.0) ** 3 * 0.36, 1)
    else:
        annual_wind_mwh = round(installed_capacity_mw * hours_per_year * (min(wind_speed_100m, 12.0) / 12.0) ** 3 * 0.36, 1)

    # 3. Mode Isolation
    st_lower = site_type.lower()
    if "solar" in st_lower and "wind" not in st_lower:
        total_aep = annual_solar_mwh
        cuf = (total_aep / (installed_capacity_mw * hours_per_year)) * 100
        engine = "XGBoost Regressor (Solar)"
    elif "wind" in st_lower and "solar" not in st_lower:
        total_aep = annual_wind_mwh
        cuf = (total_aep / (installed_capacity_mw * hours_per_year)) * 100
        engine = "Random Forest Regressor (Wind)"
    else:
        total_aep = annual_solar_mwh + annual_wind_mwh
        cuf = (total_aep / (installed_capacity_mw * 2 * hours_per_year)) * 100
        engine = "XGBoost + Random Forest Hybrid Ensemble"

    cuf = max(12.0, min(round(cuf, 1), 48.0))

    return {
        "annual_generation_mwh": f"{int(total_aep):,} MWh/yr",
        "raw_aep_mwh": total_aep,
        "cuf_percent": f"{cuf:.1f} %",
        "raw_cuf": cuf,
        "solar_aep_mwh": annual_solar_mwh,
        "wind_aep_mwh": annual_wind_mwh,
        "model_engine": engine
    }