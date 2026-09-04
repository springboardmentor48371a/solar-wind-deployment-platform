"""
Site Suitability Intelligence Engine (Module 7) + Site Scoring Engine
(Module 10).

Predicts the five weighted sub-scores, the overall Deployment Suitability
Score, the suitability category, and the recommended technology using
trained ML models (`suitability_score_model.joblib`,
`suitability_category_model.joblib`, `technology_model.joblib` -- see
app/ml/train.py). The models were trained against the same weighted formula
the spec defines:

    Deployment Suitability Score =
        Renewable Resource Availability   35%
        Geographic Suitability            25%
        Infrastructure Accessibility      15%
        Environmental Impact              15%
        Economic Feasibility              10%

so ML predictions stay anchored to that spec even as the learned model adds
robustness to noisy/live input data. Falls back to the closed-form formula
directly (app/ml/physics_baseline.py) if models aren't available.
"""
from ..ml import predictor


def score_site(env: dict, solar: dict, wind: dict, land_area_hectares: float = 5.0, site_type: str = "hybrid") -> dict:
    return predictor.predict_suitability(env, solar, wind, land_area_hectares, site_type=site_type)
