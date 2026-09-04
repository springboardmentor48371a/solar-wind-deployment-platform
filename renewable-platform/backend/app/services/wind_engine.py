"""Wind Potential Prediction Engine (Module 6).

Predicts wind power density, turbulence intensity, capacity factor and
expected annual output using the trained `wind_model.joblib`
(RandomForestRegressor, see app/ml/train.py), with the physics-informed
baseline (standard P = 0.5 * air_density * v^3 relation) as a transparent
fallback when the model can't be loaded.
"""
from ..ml import predictor


def predict_wind(env: dict, land_area_hectares: float = 5.0, elevation_m: float = 500.0) -> dict:
    return predictor.predict_wind(env, land_area_hectares, elevation_m)
