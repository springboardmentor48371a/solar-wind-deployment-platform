"""
ML-Assisted Wind Capacity Factor Prediction — same pattern as
ml_solar_predictor.py: a real, pre-trained scikit-learn model, run
alongside the deterministic physics engine in wind_engine.py, never in
place of it. See app/ml_models/wind_capacity_factor_rf.meta.json for
this model's training-data provenance.
"""

import os

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ml_models")
MODEL_PATH = os.path.join(MODEL_DIR, "wind_capacity_factor_rf.joblib")
METADATA_PATH = os.path.join(MODEL_DIR, "wind_capacity_factor_rf.meta.json")

_model = None
_metadata = None
_load_attempted = False


def _load_model():
    global _model, _metadata, _load_attempted
    if _load_attempted:
        return _model
    _load_attempted = True
    if not os.path.exists(MODEL_PATH):
        return None
    try:
        import joblib
        import json

        _model = joblib.load(MODEL_PATH)
        if os.path.exists(METADATA_PATH):
            with open(METADATA_PATH) as f:
                _metadata = json.load(f)
        return _model
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: failed to load trained wind ML model: {exc}")
        _model = None
        return None


def is_model_available() -> bool:
    return _load_model() is not None


def model_version() -> str | None:
    _load_model()
    return _metadata.get("version") if _metadata else None


def predict_capacity_factor_pct(wind_speed_50m: float, elevation_m: float) -> float | None:
    """Returns a learned capacity-factor estimate, or None if untrained."""
    model = _load_model()
    if model is None:
        return None
    try:
        import pandas as pd

        hub_wind_speed = wind_speed_50m * (80.0 / 50.0) ** (1.0 / 7.0)
        features = pd.DataFrame(
            [[wind_speed_50m, elevation_m, hub_wind_speed]],
            columns=["wind_speed_50m", "elevation_m", "hub_wind_speed"],
        )
        prediction = model.predict(features)[0]
        return round(min(max(float(prediction), 0.0), 100.0), 1)
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: ML wind capacity-factor prediction failed: {exc}")
        return None
