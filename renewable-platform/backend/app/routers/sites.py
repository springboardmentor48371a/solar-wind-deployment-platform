"""
Module 2 (site side): site registration & comparison
Modules 3-10: on site creation, runs the full pipeline —
  environmental collection -> solar/wind prediction -> suitability scoring
  -> energy forecasting
so a new site immediately has usable intelligence, matching the workflow
diagram (steps 4 through 15).
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..auth import get_current_user
from ..services.environmental_engine import fetch_environmental_data
from ..services.solar_engine import predict_solar
from ..services.wind_engine import predict_wind
from ..services.scoring_engine import score_site
from ..services.forecasting_engine import forecast_energy

router = APIRouter(prefix="/api/projects/{project_id}/sites", tags=["Sites"])


def _run_intelligence_pipeline(db: Session, site: models.Site):
    """Executes modules 3, 5, 6, 7/10, 8 for a given site and persists results."""
    env_dict = fetch_environmental_data(site.id, site.latitude, site.longitude, site.elevation_m or 0.0)
    env = models.EnvironmentalData(site_id=site.id, **env_dict)
    db.add(env)

    solar_dict = predict_solar(env_dict, site.land_area_hectares or 5.0)
    solar = models.SolarPrediction(site_id=site.id, **solar_dict)
    db.add(solar)

    wind_dict = predict_wind(env_dict, site.land_area_hectares or 5.0)
    wind = models.WindPrediction(site_id=site.id, **wind_dict)
    db.add(wind)

    score_dict = score_site(env_dict, solar_dict, wind_dict, site.land_area_hectares or 5.0)
    score = models.SiteScore(site_id=site.id, **score_dict)
    db.add(score)

    forecast_dict = forecast_energy(solar_dict, wind_dict, score_dict["recommended_technology"], site.land_area_hectares or 5.0)
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

    site = models.Site(project_id=project_id, **payload.model_dump())
    db.add(site)
    db.commit()
    db.refresh(site)

    _run_intelligence_pipeline(db, site)
    db.refresh(site)

    return _build_site_detail(site)


@router.get("", response_model=List[schemas.SiteOut])
def list_sites(project_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    _get_project_or_404(db, project_id)
    sites = db.query(models.Site).filter(models.Site.project_id == project_id).all()
    return sites


@router.get("/ranking", response_model=List[schemas.RankedSite])
def rank_sites(project_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Module 10: AI Site Scoring & Ranking — best sites first."""
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


def _build_site_detail(site: models.Site) -> schemas.SiteDetailOut:
    return schemas.SiteDetailOut(
        site=schemas.SiteOut.model_validate(site),
        environmental=schemas.EnvironmentalDataOut.model_validate(site.environmental_data) if site.environmental_data else None,
        solar=schemas.SolarPredictionOut.model_validate(site.solar_prediction) if site.solar_prediction else None,
        wind=schemas.WindPredictionOut.model_validate(site.wind_prediction) if site.wind_prediction else None,
        score=schemas.SiteScoreOut.model_validate(site.score) if site.score else None,
        forecast=schemas.EnergyForecastOut.model_validate(site.forecast) if site.forecast else None,
    )
