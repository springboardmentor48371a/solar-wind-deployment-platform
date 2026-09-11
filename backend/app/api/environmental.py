from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import SessionLocal, User, UserRole
from app.models.project_site import Site
from app.api.auth import get_current_user, require_roles
from app.core.nasa_power import fetch_nasa_environmental_data

router = APIRouter(prefix="/environmental", tags=["Module 3: Environmental Data Engine"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/preview")
async def preview_environmental_data(
    latitude: float,
    longitude: float,
    current_user: User = Depends(get_current_user)
):
    """Preview live NASA POWER climate and solar variables for any coordinate."""
    data = await fetch_nasa_environmental_data(latitude, longitude)
    return data

@router.post("/sync/{site_id}")
async def sync_site_environmental_data(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([
        UserRole.PLANNER.value,
        UserRole.GIS_ANALYST.value,
        UserRole.ADMIN.value
    ]))
):
    """
    Fetches real NASA POWER irradiance and weather data for the site's GPS coordinates,
    and updates the site's database record.
    """
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    env_data = await fetch_nasa_environmental_data(site.latitude, site.longitude)

    site.solar_ghi = env_data["solar_ghi"]
    site.avg_temp = env_data["avg_temp"]
    site.rainfall_mm = env_data["rainfall_mm"]
    site.cloud_cover_pct = env_data["cloud_cover_pct"]
    site.capacity_factor = env_data["capacity_factor"]
    site.est_yield_gwh = env_data["est_yield_gwh"]

    db.commit()
    db.refresh(site)

    return {
        "message": f"Successfully synchronized site '{site.site_name}' with NASA POWER API",
        "site": site,
        "telemetry": env_data
    }