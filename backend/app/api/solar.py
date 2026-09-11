from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.user import SessionLocal, User, UserRole
from app.models.project_site import Site
from app.api.auth import require_roles
from app.core.solar_model import solar_predictor

router = APIRouter(prefix="/solar", tags=["Module 5: Solar Potential Prediction"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/predict/{site_id}")
def predict_site_solar_potential(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([
        UserRole.PLANNER.value,
        UserRole.GIS_ANALYST.value,
        UserRole.PROJECT_MANAGER.value,
        UserRole.ADMIN.value
    ]))
):
    """
    Executes Module 5 Solar Machine Learning Prediction for a site.
    Computes capacity factor, cell temperature derating, and annual GWh generation.
    """
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Candidate site not found")

    # Ingest environmental metrics from site record (Module 3 telemetry)
    solar_results = solar_predictor.predict_solar_performance(
        latitude=site.latitude,
        elevation_m=site.elevation_m,
        solar_ghi=site.solar_ghi or 5.5,
        avg_temp=site.avg_temp or 26.0,
        cloud_cover_pct=site.cloud_cover_pct or 40.0,
        rainfall_mm=site.rainfall_mm or 150.0,
        land_area_sqkm=site.land_area_sqkm or 10.0
    )

    # Persist the ML predicted capacity factor and yield to the database
    site.capacity_factor = solar_results["predicted_capacity_factor"]
    site.est_yield_gwh = solar_results["annual_yield_gwh"]
    
    db.commit()
    db.refresh(site)

    return {
        "message": f"Module 5 Solar ML predictions computed for '{site.site_name}'",
        "site": site,
        "solar_analytics": solar_results
    }