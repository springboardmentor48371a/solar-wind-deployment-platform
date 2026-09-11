from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.user import SessionLocal, User, UserRole
from app.models.project_site import Site
from app.api.auth import require_roles
from app.core.wind_model import wind_predictor

router = APIRouter(prefix="/wind", tags=["Module 6: Wind Potential Prediction"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/predict/{site_id}")
def predict_site_wind_potential(
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
    Executes Module 6 Wind Resource Assessment and Hub-Height Extrapolation.
    Computes 100m wind velocity, WPD, and annual wind generation GWh.
    """
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Candidate site not found")

    wind_results = wind_predictor.predict_wind_performance(
        latitude=site.latitude,
        longitude=site.longitude,
        elevation_m=site.elevation_m,
        wind_speed_50m=5.8,  # Default or synced NASA telemetry
        land_area_sqkm=site.land_area_sqkm or 10.0
    )

    # Persist metrics to database record
    site.capacity_factor = wind_results["predicted_capacity_factor"]
    site.est_yield_gwh = wind_results["annual_yield_gwh"]
    
    db.commit()
    db.refresh(site)

    return {
        "message": f"Module 6 Wind potential model computed for '{site.site_name}'",
        "site": site,
        "wind_analytics": wind_results
    }