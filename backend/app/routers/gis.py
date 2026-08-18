from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app import models, auth, authz
from app.database import get_db

router = APIRouter(prefix="/gis", tags=["GIS"])


class GisSiteOut(BaseModel):
    site_id: int
    site_name: str
    project_id: int
    project_name: str
    latitude: float
    longitude: float
    elevation_m: Optional[float]
    land_slope_pct: Optional[float]
    land_area_hectares: Optional[float]
    distance_to_substation_km: Optional[float]
    protected_area_distance_km: Optional[float]
    water_body_distance_km: Optional[float]
    overall_score: Optional[float]
    resource_score: Optional[float]
    geographic_score: Optional[float]
    infrastructure_score: Optional[float]
    environmental_score: Optional[float]
    category: str


@router.get("/sites", response_model=List[GisSiteOut])
def gis_sites(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    All sites visible to the current user, with coordinates, terrain,
    environmental proximity, and latest suitability sub-scores — feeds
    the GIS Analyst Dashboard's four PDF-specified modules in one call:
    GIS visualization (map), Terrain maps (elevation/slope), Environmental
    analytics (protected-area/water proximity + environmental sub-score),
    and Site comparison reports (the sortable table this powers).
    """
    if current_user.role in authz.READ_ALL_ROLES:
        projects = db.query(models.Project).all()
    else:
        projects = db.query(models.Project).filter(models.Project.owner_id == current_user.id).all()

    project_map = {p.id: p.name for p in projects}
    sites = db.query(models.Site).filter(models.Site.project_id.in_(project_map.keys())).all() if project_map else []

    results = []
    for site in sites:
        latest = (
            db.query(models.SuitabilityScore)
            .filter(models.SuitabilityScore.site_id == site.id)
            .order_by(models.SuitabilityScore.computed_at.desc())
            .first()
        )
        env = (
            db.query(models.EnvironmentalConstraint)
            .filter(models.EnvironmentalConstraint.site_id == site.id)
            .order_by(models.EnvironmentalConstraint.fetched_at.desc())
            .first()
        )
        results.append(
            GisSiteOut(
                site_id=site.id,
                site_name=site.name,
                project_id=site.project_id,
                project_name=project_map.get(site.project_id, "Unknown"),
                latitude=site.latitude,
                longitude=site.longitude,
                elevation_m=site.elevation_m,
                land_slope_pct=site.land_slope_pct,
                land_area_hectares=site.land_area_hectares,
                distance_to_substation_km=site.distance_to_substation_km,
                protected_area_distance_km=env.protected_area_distance_km if env else None,
                water_body_distance_km=env.water_body_distance_km if env else None,
                overall_score=latest.overall_score if latest else None,
                resource_score=latest.resource_score if latest else None,
                geographic_score=latest.geographic_score if latest else None,
                infrastructure_score=latest.infrastructure_score if latest else None,
                environmental_score=latest.environmental_score if latest else None,
                category=latest.category if latest else "Unscored",
            )
        )
    return results
