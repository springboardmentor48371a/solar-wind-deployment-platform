"""
Inference layer for the Solar/Wind/Suitability ML models. Models are loaded
once (module-level singletons) and reused across requests. If a model file
is missing (not yet trained) or prediction raises for any reason, callers
transparently get the physics-informed baseline instead -- the API never
errors out because of an ML issue.
"""
import logging
import os

import numpy as np
import pandas as pd

from . import feature_schema as fs
from . import physics_baseline as physics

logger = logging.getLogger("ml.predictor")

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")

_models = {}
_load_attempted = False


def _load_all():
    global _load_attempted
    _load_attempted = True
    try:
        import joblib
    except ImportError:
        logger.warning("joblib not installed; ML predictions disabled, using physics baseline only.")
        return

    names = {
        "solar": "solar_model.joblib",
        "wind": "wind_model.joblib",
        "suitability_scores": "suitability_score_model.joblib",
        "suitability_category": "suitability_category_model.joblib",
        "technology": "technology_model.joblib",
    }
    for key, filename in names.items():
        path = os.path.join(MODELS_DIR, filename)
        if os.path.exists(path):
            try:
                _models[key] = joblib.load(path)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to load ML model %s: %s", filename, exc)
        else:
            logger.info("ML model %s not found (run `python -m app.ml.train` to train it); "
                        "using physics baseline for this component.", filename)


def _ensure_loaded():
    if not _load_attempted:
        _load_all()


def models_available() -> dict:
    _ensure_loaded()
    return {k: (k in _models) for k in ["solar", "wind", "suitability_scores", "suitability_category", "technology"]}


def predict_solar(env: dict, land_area_hectares: float = 5.0) -> dict:
    _ensure_loaded()
    model = _models.get("solar")
    if model is None:
        result = physics.solar_baseline(env, land_area_hectares)
        result["_model_used"] = "physics_baseline"
        return result
    try:
        features = {**env, "land_area_hectares": land_area_hectares}
        X = pd.DataFrame([[features[f] for f in fs.SOLAR_FEATURES]], columns=fs.SOLAR_FEATURES)
        pred = model.predict(X)[0]
        result = {name: round(float(val), 3) for name, val in zip(fs.SOLAR_TARGETS, pred)}
        result["capacity_factor_pct"] = min(result["capacity_factor_pct"], 35.0)
        result["_model_used"] = "random_forest_regressor"
        return result
    except Exception as exc:  # noqa: BLE001
        logger.warning("Solar ML prediction failed, using physics baseline: %s", exc)
        result = physics.solar_baseline(env, land_area_hectares)
        result["_model_used"] = "physics_baseline"
        return result


def predict_wind(env: dict, land_area_hectares: float = 5.0, elevation_m: float = 500.0) -> dict:
    _ensure_loaded()
    model = _models.get("wind")
    v = env["wind_speed_avg_ms"]
    if model is None:
        result = physics.wind_baseline(env, land_area_hectares)
        result["_model_used"] = "physics_baseline"
        return result
    try:
        features = {**env, "land_area_hectares": land_area_hectares, "elevation_m": elevation_m}
        X = pd.DataFrame([[features[f] for f in fs.WIND_FEATURES]], columns=fs.WIND_FEATURES)
        pred = model.predict(X)[0]
        result = {name: round(float(val), 3) for name, val in zip(fs.WIND_TARGETS, pred)}
        result["avg_wind_speed_ms"] = v
        result["capacity_factor_pct"] = max(0.0, min(result["capacity_factor_pct"], 60.0))
        if v < 3:
            result["turbine_suitability"] = "Unsuitable"
        elif v < 5.5:
            result["turbine_suitability"] = "Marginal"
        elif v < 7.5:
            result["turbine_suitability"] = "Suitable"
        else:
            result["turbine_suitability"] = "Highly Suitable"
        result["_model_used"] = "random_forest_regressor"
        return result
    except Exception as exc:  # noqa: BLE001
        logger.warning("Wind ML prediction failed, using physics baseline: %s", exc)
        result = physics.wind_baseline(env, land_area_hectares)
        result["_model_used"] = "physics_baseline"
        return result


def predict_suitability(env: dict, solar: dict, wind: dict, land_area_hectares: float = 5.0, site_type: str = "hybrid") -> dict:
    _ensure_loaded()
    score_model = _models.get("suitability_scores")
    cat_model = _models.get("suitability_category")
    tech_model = _models.get("technology")

    if not (score_model and cat_model and tech_model):
        result = physics.scoring_baseline(env, solar, wind, land_area_hectares, site_type=site_type)
        result["_model_used"] = "physics_baseline"
        return result

    try:
        feat_dict = {
            **env,
            "land_area_hectares": land_area_hectares,
            "in_protected_zone": int(bool(env["in_protected_zone"])),
            "solar_capacity_factor_pct": solar["capacity_factor_pct"],
            "wind_capacity_factor_pct": wind["capacity_factor_pct"],
        }
        X = pd.DataFrame([[feat_dict[f] for f in fs.SUITABILITY_FEATURES]], columns=fs.SUITABILITY_FEATURES)

        score_pred = score_model.predict(X)[0]
        scores = {name: round(float(val), 2) for name, val in zip(fs.SUITABILITY_SCORE_TARGETS, score_pred)}
        for k in scores:
            scores[k] = max(0.0, min(100.0, scores[k]))

        category = str(cat_model.predict(X)[0])

        site_type_str = str(site_type).lower() if site_type else "hybrid"
        if site_type_str in ("solar", "wind"):
            technology = site_type_str
        else:
            technology = str(tech_model.predict(X)[0])

        scores["category"] = category
        scores["recommended_technology"] = technology
        scores["_model_used"] = "random_forest"
        return scores
    except Exception as exc:  # noqa: BLE001
        logger.warning("Suitability ML prediction failed, using physics baseline: %s", exc)
        result = physics.scoring_baseline(env, solar, wind, land_area_hectares, site_type=site_type)
        result["_model_used"] = "physics_baseline"
        return result
