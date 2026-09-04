"""
Module 2 (site side): site registration & comparison
Modules 3-10: on site creation, runs the full pipeline --
  live site-attribute derivation (land area/elevation/region/infra/ownership)
  -> environmental collection -> ML solar/wind prediction -> ML suitability
  scoring -> energy forecasting
so a new site immediately has usable intelligence from nothing but its
coordinates, matching the workflow diagram (steps 4 through 15).
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..auth import get_current_user
from ..services import site_intelligence
from ..services.environmental_engine import fetch_environmental_data
from ..services.solar_engine import predict_solar
from ..services.wind_engine import predict_wind
from ..services.scoring_engine import score_site
from ..services.forecasting_engine import forecast_energy

router = APIRouter(prefix="/api/projects/{project_id}/sites", tags=["Sites"])
standalone_router = APIRouter(prefix="/api/sites", tags=["Sites (Standalone)"])


def _apply_derived_site_attributes(db: Session, site: models.Site, user_supplied: dict) -> dict:
    """Fills site-info fields from live data or overrides."""
    derived = site_intelligence.derive_site_attributes(site.latitude, site.longitude)
    merged = site_intelligence.merge_with_overrides(derived, user_supplied)

    site.region = merged["region"]
    site.land_area_hectares = merged["land_area_hectares"]
    site.elevation_m = merged["elevation_m"]
    site.existing_infrastructure = merged["existing_infrastructure"]
    site.land_ownership = merged["land_ownership"]
    site.attributes_source = derived["data_source"]
    db.add(site)
    db.commit()
    db.refresh(site)
    return derived


def _run_intelligence_pipeline(db: Session, site: models.Site, derived_attrs: dict):
    """Executes modules 3, 5, 6, 7/10, 8 for a given site and persists results."""
    env_dict = fetch_environmental_data(
        site.id, site.latitude, site.longitude,
        elevation_m=derived_attrs.get("elevation_m"),
        osm_context=derived_attrs.get("osm_context"),
    )
    env = models.EnvironmentalData(site_id=site.id, **env_dict)
    db.add(env)

    land_area = site.land_area_hectares or 5.0

    solar_dict = dict(predict_solar(env_dict, land_area))
    solar_dict["model_used"] = solar_dict.pop("_model_used", "physics_baseline")
    solar = models.SolarPrediction(site_id=site.id, **solar_dict)
    db.add(solar)

    wind_dict = dict(predict_wind(env_dict, land_area, elevation_m=site.elevation_m or 500.0))
    wind_dict["model_used"] = wind_dict.pop("_model_used", "physics_baseline")
    wind = models.WindPrediction(site_id=site.id, **wind_dict)
    db.add(wind)

    score_dict = dict(score_site(env_dict, solar_dict, wind_dict, land_area, site_type=site.site_type))
    score_dict["model_used"] = score_dict.pop("_model_used", "physics_baseline")
    score = models.SiteScore(site_id=site.id, **score_dict)
    db.add(score)

    forecast_dict = forecast_energy(solar_dict, wind_dict, score_dict["recommended_technology"], land_area)
    forecast = models.EnergyForecast(site_id=site.id, **forecast_dict)
    db.add(forecast)

    db.commit()


def _get_project_or_404(db: Session, project_id: int) -> models.Project:
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("", response_model=schemas.SiteDetailOut)
def create_site(project_id: int, payload: schemas.SiteCreate, db: Session = Depends(get_db),
                 current_user: models.User = Depends(get_current_user)):
    _get_project_or_404(db, project_id)

    payload_dict = payload.model_dump()
    user_supplied = {
        k: payload_dict.pop(k) for k in
        ("region", "land_area_hectares", "elevation_m", "existing_infrastructure", "land_ownership")
    }

    site = models.Site(project_id=project_id, **payload_dict)
    db.add(site)
    db.commit()
    db.refresh(site)

    derived_attrs = _apply_derived_site_attributes(db, site, user_supplied)
    _run_intelligence_pipeline(db, site, derived_attrs)
    db.refresh(site)

    return _build_site_detail(site)


@router.get("", response_model=List[schemas.SiteOut])
def list_sites(project_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    _get_project_or_404(db, project_id)
    sites = db.query(models.Site).filter(models.Site.project_id == project_id).all()
    return sites


@router.get("/ranking", response_model=List[schemas.RankedSite])
def rank_sites(project_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    _get_project_or_404(db, project_id)
    sites = db.query(models.Site).filter(models.Site.project_id == project_id).all()
    ranked = []
    for s in sites:
        if s.score:
            ranked.append(schemas.RankedSite(
                site_id=s.id, site_name=s.name,
                overall_score=s.score.overall_score,
                category=s.score.category,
                recommended_technology=s.score.recommended_technology,
            ))
    ranked.sort(key=lambda r: r.overall_score, reverse=True)
    return ranked


@router.post("/{site_id}/recompute", response_model=schemas.SiteDetailOut)
def recompute_site(project_id: int, site_id: int, db: Session = Depends(get_db),
                    current_user: models.User = Depends(get_current_user)):
    site = db.query(models.Site).filter(models.Site.id == site_id, models.Site.project_id == project_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    for existing in (site.environmental_data, site.solar_prediction, site.wind_prediction, site.score, site.forecast):
        if existing:
            db.delete(existing)
    db.commit()

    user_supplied = {
        "region": None, "land_area_hectares": None, "elevation_m": None,
        "existing_infrastructure": None, "land_ownership": None,
    }
    derived_attrs = _apply_derived_site_attributes(db, site, user_supplied)
    _run_intelligence_pipeline(db, site, derived_attrs)
    db.refresh(site)
    return _build_site_detail(site)


@router.get("/{site_id}", response_model=schemas.SiteDetailOut)
def get_site(project_id: int, site_id: int, db: Session = Depends(get_db),
             current_user: models.User = Depends(get_current_user)):
    site = db.query(models.Site).filter(models.Site.id == site_id, models.Site.project_id == project_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return _build_site_detail(site)


@router.delete("/{site_id}")
def delete_site(project_id: int, site_id: int, db: Session = Depends(get_db),
                 current_user: models.User = Depends(get_current_user)):
    site = db.query(models.Site).filter(models.Site.id == site_id, models.Site.project_id == project_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    db.delete(site)
    db.commit()
    return {"deleted": True}


# ---------- STANDALONE SITES ROUTER (/api/sites/...) ----------

@standalone_router.get("/{site_id}", response_model=schemas.SiteDetailOut)
def get_site_standalone(site_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    site = db.query(models.Site).filter(models.Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return _build_site_detail(site)


@standalone_router.put("/{site_id}", response_model=schemas.SiteDetailOut)
def update_site_standalone(site_id: int, payload: schemas.SiteCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    site = db.query(models.Site).filter(models.Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    site.name = payload.name
    site.latitude = payload.latitude
    site.longitude = payload.longitude
    site.site_type = payload.site_type
    if payload.region is not None: site.region = payload.region
    if payload.land_area_hectares is not None: site.land_area_hectares = payload.land_area_hectares
    if payload.elevation_m is not None: site.elevation_m = payload.elevation_m
    
    db.commit()
    db.refresh(site)
    return _build_site_detail(site)


@standalone_router.delete("/{site_id}")
def delete_site_standalone(site_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    site = db.query(models.Site).filter(models.Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    db.delete(site)
    db.commit()
    return {"deleted": True}


@standalone_router.post("/{site_id}/analyze", response_model=schemas.SiteDetailOut)
def analyze_site_standalone(site_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    site = db.query(models.Site).filter(models.Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    for existing in (site.environmental_data, site.solar_prediction, site.wind_prediction, site.score, site.forecast):
        if existing:
            db.delete(existing)
    db.commit()

    user_supplied = {"region": site.region, "land_area_hectares": site.land_area_hectares, "elevation_m": site.elevation_m, "existing_infrastructure": site.existing_infrastructure, "land_ownership": site.land_ownership}
    derived_attrs = _apply_derived_site_attributes(db, site, user_supplied)
    _run_intelligence_pipeline(db, site, derived_attrs)
    db.refresh(site)
    return _build_site_detail(site)


@standalone_router.get("/{site_id}/analysis")
def get_site_analysis_standalone(site_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    site = db.query(models.Site).filter(models.Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    detail = _build_site_detail(site)
    return {
        "site_id": site.id,
        "solar": detail.solar,
        "wind": detail.wind,
        "score": detail.score,
    }


@standalone_router.get("/{site_id}/environment", response_model=Optional[schemas.EnvironmentalDataOut])
def get_site_environment_standalone(site_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    site = db.query(models.Site).filter(models.Site.id == site_id).first()
    if not site or not site.environmental_data:
        raise HTTPException(status_code=404, detail="Environmental data not found for site")
    return schemas.EnvironmentalDataOut.model_validate(site.environmental_data)


@standalone_router.get("/{site_id}/forecast", response_model=Optional[schemas.EnergyForecastOut])
def get_site_forecast_standalone(site_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    site = db.query(models.Site).filter(models.Site.id == site_id).first()
    if not site or not site.forecast:
        raise HTTPException(status_code=404, detail="Forecast data not found for site")
    return schemas.EnergyForecastOut.model_validate(site.forecast)


def _build_site_detail(site: models.Site) -> schemas.SiteDetailOut:
    return schemas.SiteDetailOut(
        site=schemas.SiteOut.model_validate(site),
        environmental=schemas.EnvironmentalDataOut.model_validate(site.environmental_data) if site.environmental_data else None,
        solar=schemas.SolarPredictionOut.model_validate(site.solar_prediction) if site.solar_prediction else None,
        wind=schemas.WindPredictionOut.model_validate(site.wind_prediction) if site.wind_prediction else None,
        score=schemas.SiteScoreOut.model_validate(site.score) if site.score else None,
        forecast=schemas.EnergyForecastOut.model_validate(site.forecast) if site.forecast else None,
    )
