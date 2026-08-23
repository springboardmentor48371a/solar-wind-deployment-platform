"""
Risk Assessment Model (PDF: "LSTM/Prophet") — see
app/ml_models/risk_assessment_rf.meta.json for full provenance and the
honest explanation of why this is a RandomForestClassifier predicting a
point-in-time risk category rather than an LSTM/Prophet time-series
forecast: a genuine LSTM/Prophet model needs far more historical data
per site than this platform's live 7-day NASA POWER window provides,
and building one on 7 days of data would be fabricated/overfit with no
real forecasting value.
"""

import os

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ml_models")
MODEL_PATH = os.path.join(MODEL_DIR, "risk_assessment_rf.joblib")
METADATA_PATH = os.path.join(MODEL_DIR, "risk_assessment_rf.meta.json")

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
        print(f"Warning: failed to load risk assessment model: {exc}")
        return None


def is_model_available() -> bool:
    return _load_model() is not None


def model_version() -> str | None:
    _load_model()
    return _metadata.get("version") if _metadata else None


def predict_risk_category(wind_speed_50m: float, protected_area_distance_km: float, land_slope_pct: float) -> dict | None:
    model = _load_model()
    if model is None:
        return None
    try:
        import pandas as pd

        features = pd.DataFrame(
            [[wind_speed_50m, protected_area_distance_km, land_slope_pct]],
            columns=["wind_speed_50m", "protected_area_distance_km", "land_slope_pct"],
        )
        prediction = model.predict(features)[0]
        probabilities = model.predict_proba(features)[0]
        confidence = round(float(max(probabilities)) * 100, 1)
        return {"risk_category": prediction, "confidence_pct": confidence}
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: ML risk assessment prediction failed: {exc}")
        return None
