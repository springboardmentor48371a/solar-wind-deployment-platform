"""
ML-Assisted Solar Performance Prediction (Beta) — a real, trained
scikit-learn model, run *alongside* the deterministic physics engine in
solar_engine.py, never in place of it.

This module only loads and serves an already-trained model. Training
happens offline via scripts/train_solar_model.py against real measured
plant data — see that script's docstring for exactly which dataset and
why. If no trained model file exists yet (the common case until someone
actually runs the training script with a downloaded dataset), every
function here returns None and the caller falls back to physics-only
results — same resilience pattern as every external API connector in
this codebase.

Why scikit-learn instead of TensorFlow/PyTorch: the real dataset this is
designed for (~140k rows, a handful of numeric features) doesn't need a
neural network — a Random Forest is the right-sized tool, trains in
seconds, and doesn't add TensorFlow/PyTorch's multi-GB footprint to the
Docker image for a model this small. The interface below is
framework-agnostic, so a deep learning model can be swapped in later
without changing solar_engine.py's calling code.
"""

import os

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ml_models")
MODEL_PATH = os.path.join(MODEL_DIR, "solar_performance_ratio_rf.joblib")
METADATA_PATH = os.path.join(MODEL_DIR, "solar_performance_ratio_rf.meta.json")

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
        print(f"Warning: failed to load trained solar ML model: {exc}")
        _model = None
        return None


def is_model_available() -> bool:
    return _load_model() is not None


def model_version() -> str | None:
    _load_model()
    return _metadata.get("version") if _metadata else None


def predict_performance_ratio_pct(avg_temp_c: float, avg_irradiance_kwh_m2_day: float) -> float | None:
    """
    Returns a learned performance-ratio estimate (0-100%) from real
    measured plant behavior, or None if no model has been trained yet.
    Same two inputs the physics formula uses, so the two numbers are
    directly comparable side by side.
    """
    model = _load_model()
    if model is None:
        return None
    try:
        import pandas as pd

        temp_x_irradiance = avg_temp_c * avg_irradiance_kwh_m2_day
        features = pd.DataFrame(
            [[avg_temp_c, avg_irradiance_kwh_m2_day, temp_x_irradiance]],
            columns=["ambient_temperature", "irradiation", "temp_x_irradiance"],
        )
        prediction = model.predict(features)[0]
        # Same realistic clamp the physics formula uses — a trained model
        # can extrapolate to nonsense outside its training data's range,
        # and this is a real PV system, not an unbounded quantity.
        return round(min(max(float(prediction), 0.0), 100.0), 1)
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: ML performance-ratio prediction failed: {exc}")
        return None
