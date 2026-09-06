"""
AI/ML Prediction Layer — the platform's ML-Assisted predictions surfaced
as first-class endpoints, distinct from the physics engines (solar_engine.py,
wind_engine.py, scoring.py) they run alongside.

Six real, trained models ship with this platform (see app/services/ml_*.py
and app/ml_models/*.meta.json for full training-data provenance on each):
  1. Solar performance-ratio predictor (Random Forest, real Kaggle plant
     data) — surfaced via SolarPotentialOut's ml_* fields, computed
     automatically alongside the physics engine, not duplicated here
  2. Wind capacity-factor predictor (Random Forest, real Kelmarsh SCADA
     data) — same, via WindPotentialOut's ml_* fields
  3. Suitability quick-classifier — THIS router's endpoint, since unlike
     1/2 it doesn't need a registered site with collected data first;
     it's meant for triage before that. Ground truth is the real,
     validated scoring.py formula.
  4. Investment prediction (Gradient Boosting) — surfaced via sites.py's
     ml-investment-estimate endpoint
  5. Risk assessment (Random Forest) — surfaced via sites.py's
     ml-risk-assessment endpoint
  6. Land cover classification (CNN, trained on real EuroSAT imagery) —
     surfaced automatically via satellite.py using AWS Earth Search's
     public Sentinel-2 archive (no account/API key needed). The
     standalone image-upload testing endpoint that used to live here
     was removed once the Sentinel Hub registration issue it worked
     around was fixed by the AWS Earth Search replacement — the model
     itself is unaffected, only that separate manual-testing tool.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

from app import models, auth
from app.services import ml_solar_predictor, ml_wind_predictor, ml_suitability_predictor, ml_investment_predictor, ml_risk_predictor, ml_landcover_predictor

router = APIRouter(prefix="/ml", tags=["AI/ML Prediction Layer"])


class ModelStatusOut(BaseModel):
    name: str
    available: bool
    version: Optional[str]
    purpose: str


@router.get("/status", response_model=list[ModelStatusOut])
def ml_model_status(current_user: models.User = Depends(auth.get_current_user)):
    """Which ML models are actually loaded and ready right now — same honesty pattern as /data-sources/status."""
    return [
        ModelStatusOut(
            name="Solar Performance Ratio (Random Forest)",
            available=ml_solar_predictor.is_model_available(),
            version=ml_solar_predictor.model_version(),
            purpose="Predicts panel performance ratio from temperature/irradiance, alongside the physics engine.",
        ),
        ModelStatusOut(
            name="Wind Capacity Factor (Random Forest)",
            available=ml_wind_predictor.is_model_available(),
            version=ml_wind_predictor.model_version(),
            purpose="Predicts turbine capacity factor from wind speed/elevation, alongside the physics engine.",
        ),
        ModelStatusOut(
            name="Suitability Quick-Classifier (Random Forest)",
            available=ml_suitability_predictor.is_model_available(),
            version=ml_suitability_predictor.model_version(),
            purpose="Instant rough suitability category from estimated inputs, before registering a full site.",
        ),
        ModelStatusOut(
            name="Investment Prediction Model (Gradient Boosting, substituted for XGBoost)",
            available=ml_investment_predictor.is_model_available(),
            version=ml_investment_predictor.model_version(),
            purpose="Instant NPV/IRR estimate from a trained model, without running the full financial calculation.",
        ),
        ModelStatusOut(
            name="Risk Assessment Model (Random Forest, substituted for LSTM/Prophet)",
            available=ml_risk_predictor.is_model_available(),
            version=ml_risk_predictor.model_version(),
            purpose="Point-in-time risk category from wind speed and siting factors \u2014 see model metadata for an important honest limitation on what it actually uses.",
        ),
        ModelStatusOut(
            name="Land Cover Classification Model (CNN, trained on real EuroSAT imagery)",
            available=ml_landcover_predictor.is_model_available(),
            version=ml_landcover_predictor.model_version(),
            purpose="Classifies a real Sentinel-2 RGB image tile into one of 10 land-use/land-cover classes \u2014 trained from scratch, 74.8% held-out test accuracy (see model metadata for the honest per-class breakdown).",
        ),
    ]


class QuickSuitabilityRequest(BaseModel):
    avg_irradiance: float = Field(..., ge=0, le=15, description="Estimated kWh/m^2/day")
    avg_wind: float = Field(..., ge=0, le=30, description="Estimated wind speed, m/s")
    land_slope_pct: float = Field(0, ge=0, le=100)
    elevation_m: float = Field(0, ge=-500, le=9000)
    substation_km: float = Field(10, ge=0)
    road_km: float = Field(5, ge=0)
    transmission_km: float = Field(10, ge=0)
    protected_area_km: float = Field(20, ge=0)
    water_body_km: float = Field(5, ge=0)
    agricultural_nearby: bool = False


class QuickSuitabilityResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())  # "model_version" is intentional, not a real conflict

    category: str
    confidence_pct: float
    model_version: str
    note: str


@router.post("/quick-suitability-estimate", response_model=QuickSuitabilityResponse)
def quick_suitability_estimate(
    body: QuickSuitabilityRequest,
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Instant rough category estimate from estimated/ballpark inputs — no
    site registration required. Not a replacement for the real
    suitability score: once a site is registered and real data is
    collected, GET /projects/{id}/sites/{id}/suitability is always the
    authoritative answer.
    """
    if not ml_suitability_predictor.is_model_available():
        raise HTTPException(status_code=503, detail="Suitability quick-estimate model is not available.")

    features = {
        "avg_irradiance": body.avg_irradiance,
        "avg_wind": body.avg_wind,
        "land_slope_pct": body.land_slope_pct,
        "elevation_m": body.elevation_m,
        "substation_km": body.substation_km,
        "road_km": body.road_km,
        "transmission_km": body.transmission_km,
        "protected_area_km": body.protected_area_km,
        "water_body_km": body.water_body_km,
        "agricultural_nearby": 1 if body.agricultural_nearby else 0,
    }
    result = ml_suitability_predictor.predict_category(features)
    if result is None:
        raise HTTPException(status_code=503, detail="Prediction failed — see server logs.")

    return QuickSuitabilityResponse(
        category=result["category"],
        confidence_pct=result["confidence_pct"],
        model_version=ml_suitability_predictor.model_version() or "unknown",
        note="Rough estimate from provided inputs only. Register the site and run the full pipeline for the real, authoritative suitability score.",
    )

