"""
Land cover classification and scoring.

Normal path  : Earth Engine extracts 8 real features → XGBoost model → probability-weighted score.
Fallback path: EE unavailable or model missing → rule-based NDVI+slope classifier → fixed score.

Feature order (MUST match land_cover_feature_order.json and training):
  [ndvi, ndbi, elevation, slope_deg,
   ndvi_seasonal_std, ndvi_seasonal_amplitude, ndvi_texture, night_lights_log]
"""

import logging
import joblib
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).parent.parent / "models" / "land_cover_model.pkl"

# Label map — fixed at training time, NOT alphabetical.
# XGBoost integer output → class name.
_LABEL_MAP = ["cropland", "forest", "grassland", "urban", "water", "barren"]

# Feature order — must match training exactly.
_FEATURE_ORDER = [
    "ndvi", "ndbi", "elevation", "slope_deg",
    "ndvi_seasonal_std", "ndvi_seasonal_amplitude",
    "ndvi_texture", "night_lights_log",
]

_model = None
_model_failed = False  # True if load failed — skip retry on every request


def load_model() -> None:
    global _model, _model_failed
    if not MODEL_PATH.exists():
        logger.warning("land_cover_model.pkl not found — will use rule-based fallback.")
        _model_failed = True
        return
    try:
        _model = joblib.load(MODEL_PATH)
        logger.info(
            "Land cover model loaded (%d classes, %d features).",
            len(_model.classes_), _model.n_features_in_,
        )
    except Exception as exc:
        logger.warning("Failed to load land_cover_model.pkl (%s) — will use rule-based fallback.", exc)
        _model_failed = True


# ---------------------------------------------------------------------------
# Rule-based fallback — used when model or EE is unavailable.
# Kept from the previous implementation; never used in normal operation.
# ---------------------------------------------------------------------------

def _classify_rule_based(ndvi: float, slope_deg: float) -> str:
    if ndvi < 0.0:
        return "water"
    if ndvi < 0.1:
        return "barren"
    if slope_deg > 20:
        return "forest" if ndvi > 0.4 else "barren"
    if ndvi >= 0.5:
        return "forest"
    if ndvi >= 0.3:
        return "grassland"
    if ndvi >= 0.15:
        return "cropland"
    return "barren"

_FALLBACK_SCORES = {
    "grassland": 80, "cropland": 65, "barren": 60,
    "forest": -20,   "urban": -80,   "water": -100,
}

def _score_from_class(cover_class: str) -> float:
    return max(0.0, min(float(_FALLBACK_SCORES[cover_class]), 100.0))

def _predict_fallback(ndvi: float, slope_deg: float, elevation: float) -> dict:
    logger.warning("Using rule-based land cover fallback — EE or model unavailable.")
    cover_class = _classify_rule_based(ndvi, slope_deg)
    return {
        "cover_class":      cover_class,
        "vegetation_pct":   None,
        "urban_pct":        None,
        "barren_pct":       None,
        "water_pct":        None,
        "ndvi":             ndvi,
        "slope_deg":        slope_deg,
        "land_cover_score": _score_from_class(cover_class),
    }


# ---------------------------------------------------------------------------
# Probability-weighted score formula
# Literature: Ayodele et al. 2018; Wolaita AHP-GIS Sci Reports 2023;
#             Prieto-Amparán et al. 2021 (Land); Gaziantep PV study;
#             Burundi F-AHP wind study (Frontiers in Energy Research 2024);
#             GIS-agrovoltaics study 2026 (Valle d'Aosta / Almería / Azores).
# ---------------------------------------------------------------------------

def _score_from_proba(proba: np.ndarray) -> float:
    p_cropland, p_forest, p_grassland, p_urban, p_water, p_barren = proba
    score = (
          p_grassland * 100   # dominant land type in "most suitable" tier across all siting studies
        + p_cropland  *  90   # highly suitable per GIS-MCDA literature (solar + wind)
        + p_barren    *  60   # open buildable land; usable, not preferred
        - p_forest    *  40   # soft penalty: 76% recall means some cropland leaks here
        - p_urban     *  80   # strong exclusion; urban recall now 87% (was 53%)
        - p_water     * 100   # hard exclusion; 98% recall — most reliable class
    )
    return round(max(0.0, min(score, 100.0)), 2)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def predict_land_cover(
    ndvi: float,
    slope_deg: float,
    elevation: float,
    ee_features: dict | None = None,
) -> dict:
    """
    Predict land cover class and score for a site.

    ee_features: dict returned by earth_engine.extract_features() — if provided
                 and the model is loaded, uses the full 8-feature path.
                 If None (EE unavailable) or model missing, falls back to
                 rule-based classification using ndvi/slope/elevation.
    """
    if _model_failed or _model is None or ee_features is None:
        return _predict_fallback(ndvi, slope_deg, elevation)

    try:
        features = np.array([[ee_features[f] for f in _FEATURE_ORDER]])
        proba       = _model.predict_proba(features)[0]
        cover_class = _LABEL_MAP[int(_model.predict(features)[0])]
        score       = _score_from_proba(proba)

        p_cropland, p_forest, p_grassland, p_urban, p_water, p_barren = proba

        return {
            "cover_class":      cover_class,
            "vegetation_pct":   round(float(p_grassland) * 100, 2),  # stored in vegetation_pct column
            "urban_pct":        round(float(p_urban)     * 100, 2),
            "barren_pct":       round(float(p_barren)    * 100, 2),
            "water_pct":        round(float(p_water)     * 100, 2),
            "ndvi":             ee_features["ndvi"],
            "slope_deg":        ee_features["slope_deg"],
            "land_cover_score": score,
        }

    except Exception as exc:
        logger.warning("Model inference failed (%s) — using rule-based fallback.", exc)
        return _predict_fallback(ndvi, slope_deg, elevation)
