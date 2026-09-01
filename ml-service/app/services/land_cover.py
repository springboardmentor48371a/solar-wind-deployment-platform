import joblib
import numpy as np
from pathlib import Path

MODEL_PATH = Path(__file__).parent.parent / "models" / "land_cover_model.pkl"

CLASSES = ["vegetation", "urban", "barren", "water", "cropland"]

model = None

def load_model():
    global model
    if MODEL_PATH.exists():
        model = joblib.load(MODEL_PATH)

def predict_land_cover(ndvi: float, slope_deg: float, elevation: float) -> dict:
    if model is None:
        return {
            "cover_class": None, "vegetation_pct": None, "urban_pct": None,
            "water_pct": None, "barren_pct": None, "ndvi": None,
            "slope_deg": None, "land_cover_score": None,
        }

    features = np.array([[ndvi, slope_deg, elevation]])
    cover_class = CLASSES[int(model.predict(features)[0])]
    proba = model.predict_proba(features)[0]

    # score: vegetation and barren land are good, urban and water are bad
    score = round((proba[0] * 100 + proba[2] * 60) - (proba[1] * 80 + proba[3] * 100), 2)
    score = max(0.0, min(score, 100.0))

    return {
        "cover_class": cover_class,
        "vegetation_pct": round(float(proba[0]) * 100, 2),
        "urban_pct": round(float(proba[1]) * 100, 2),
        "barren_pct": round(float(proba[2]) * 100, 2),
        "water_pct": round(float(proba[3]) * 100, 2),
        "ndvi": ndvi,
        "slope_deg": slope_deg,
        "land_cover_score": score,
    }
