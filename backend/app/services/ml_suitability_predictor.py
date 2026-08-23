"""
Suitability Quick-Estimate — different in kind from the solar/wind ML
models: its training ground truth genuinely IS the validated
deterministic scoring formula (scoring.py), re-derived exactly, not an
approximation of unknown real-world truth. This is "learn to predict
the trusted rule instantly," not "replace the trusted rule."

Real use case: a Planner screening many candidate locations can get an
instant rough category from ballpark/estimated inputs (e.g. "this
region typically gets ~6 kWh/m2/day, slope looks flat on the map, maybe
5km to the nearest substation") before committing to registering a site
and running the full external-data pipeline. Once a site is actually
registered and real data collected, scoring.py's real engine is always
the authoritative score — this is a triage tool, not a substitute.
"""

import os

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ml_models")
MODEL_PATH = os.path.join(MODEL_DIR, "suitability_quick_classifier_rf.joblib")
METADATA_PATH = os.path.join(MODEL_DIR, "suitability_quick_classifier_rf.meta.json")

FEATURE_ORDER = [
    "avg_irradiance", "avg_wind", "land_slope_pct", "elevation_m", "substation_km",
    "road_km", "transmission_km", "protected_area_km", "water_body_km", "agricultural_nearby",
]

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
        print(f"Warning: failed to load trained suitability ML model: {exc}")
        _model = None
        return None


def is_model_available() -> bool:
    return _load_model() is not None


def model_version() -> str | None:
    _load_model()
    return _metadata.get("version") if _metadata else None


def predict_category(features: dict) -> dict | None:
    """
    features must contain all keys in FEATURE_ORDER. Returns
    {"category": str, "confidence_pct": float} or None if untrained.
    """
    model = _load_model()
    if model is None:
        return None
    try:
        import pandas as pd

        row = pd.DataFrame([[features[k] for k in FEATURE_ORDER]], columns=FEATURE_ORDER)
        prediction = model.predict(row)[0]
        probabilities = model.predict_proba(row)[0]
        confidence = round(float(max(probabilities)) * 100, 1)
        return {"category": prediction, "confidence_pct": confidence}
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: ML suitability quick-estimate failed: {exc}")
        return None
