import os
import joblib
import pandas as pd

# Load the trained XGBoost model
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "ml", "artifacts", "solar_aep_xgb.pkl")
solar_xgb_model = joblib.load(MODEL_PATH) if os.path.exists(MODEL_PATH) else None

def compute_site_suitability(env: dict) -> dict:
    """
    Computes suitability score (0-10) using AHP criteria and runs 
    the trained XGBoost solar model for energy yield prediction.
    """
    # 1. Resource Factor (GHI)
    res_factor = min(1.0, env.get("solar_irradiance", 5.5) / 5.8) * 100.0

    # 2. Geographic Factor (Elevation)
    elevation = env.get("elevation", 25.0)
    geo_factor = min(100.0, max(40.0, (elevation / 400.0) * 100.0))

    # 3. Environmental Factor (Derated by extreme heat and cloud cover)
    max_temp = env.get("max_temperature", 30.0)
    temp_penalty = max(0.0, (max_temp - 35.0) * 2.5)
    cloud_penalty = (env.get("cloud_cover", 50.0) / 100.0) * 20.0
    rain_penalty = min(15.0, (env.get("total_rainfall", 50.0) / 300.0) * 10.0)
    env_factor = max(20.0, 100.0 - temp_penalty - cloud_penalty - rain_penalty)

    # 4. Infrastructure & Economic Baselines
    infra_factor = 78.0
    econ_factor = 85.0

    # Weighted composite index: 35% Res, 25% Geo, 15% Infra, 15% Env, 10% Econ
    raw_score_100 = (
        (res_factor * 0.35) + 
        (geo_factor * 0.25) + 
        (infra_factor * 0.15) + 
        (env_factor * 0.15) + 
        (econ_factor * 0.10)
    )

    score_10 = round(raw_score_100 / 10.0, 1)

    if score_10 >= 8.5:
        category = "Excellent"
    elif score_10 >= 7.0:
        category = "Highly Suitable"
    elif score_10 >= 5.5:
        category = "Moderately Suitable"
    else:
        category = "Low Suitability"

    # ML Inference via trained XGBoost model
    if solar_xgb_model:
        features_df = pd.DataFrame([{
            "solar_irradiance": env.get("solar_irradiance", 5.5),
            "peak_sun_hours": env.get("peak_sun_hours", 5.5),
            "temperature_avg": env.get("temperature_avg", 28.0),
            "cloud_cover": env.get("cloud_cover", 50.0),
            "elevation": env.get("elevation", 25.0)
        }])
        daily_yield_per_kwp = float(solar_xgb_model.predict(features_df)[0])
        annual_yield = round(daily_yield_per_kwp * 365.0, 1)
    else:
        annual_yield = round(env.get("solar_irradiance", 5.5) * 365 * 0.78 * (1.0 - (temp_penalty / 100.0)), 1)

    capacity_factor = round((annual_yield / 8760.0) * 100, 1)

    return {
        "suitability_score": score_10,
        "suitability_category": category,
        "capacity_factor": capacity_factor,
        "est_yield": annual_yield
    }