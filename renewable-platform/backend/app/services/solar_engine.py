"""Solar Potential Prediction Engine (Module 5).

Predicts panel efficiency, performance ratio, capacity factor, shading loss
and expected annual output using the trained `solar_model.joblib`
(RandomForestRegressor, see app/ml/train.py). If the model isn't loaded for
any reason, transparently falls back to the physics-informed baseline
formula in app/ml/physics_baseline.py, so this function always returns a
complete, usable result.
"""
from ..ml import predictor


def predict_solar(env: dict, land_area_hectares: float = 5.0) -> dict:
    return predictor.predict_solar(env, land_area_hectares)
