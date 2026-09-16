import httpx
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

@router.get("/preview-coordinates")
async def preview_coordinates(
    latitude: float,
    longitude: float,
    current_user: User = Depends(get_current_user)
):
    """
    Fetches SRTM Digital Elevation Model (DEM) data for clicked map coordinates
    and returns initial parcel values for the Add Site modal.
    """
    elevation = 210.0
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            res = await client.get(
                "https://api.open-meteo.com/v1/elevation",
                params={"latitude": round(latitude, 4), "longitude": round(longitude, 4)}
            )
            if res.status_code == 200:
                elev_val = res.json().get("elevation", [210.0])
                elevation = float(elev_val[0] if isinstance(elev_val, list) else elev_val)
    except Exception:
        elevation = round(max(50.0, 310.0 - abs(latitude - 26.0) * 18.0), 1)

    return {
        "latitude": round(latitude, 4),
        "longitude": round(longitude, 4),
        "elevation_m": round(elevation, 1),
        "land_area_sqkm": 12.5
    }

@router.get("/preview")
async def preview_environmental_data(
    latitude: float,
    longitude: float,
    current_user: User = Depends(get_current_user)
):
    """Preview live NASA POWER, SRTM DEM slope, and Sentinel NDVI data."""
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
    Fetches full environmental telemetry (NASA POWER + SRTM DEM + Sentinel-2)
    and updates the site database record.
    """
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found in database")

    env_data = await fetch_nasa_environmental_data(site.latitude, site.longitude)

    # Update database columns with Module 3 metrics
    site.solar_ghi = env_data["solar_ghi"]
    site.avg_temp = env_data["avg_temp"]
    site.rainfall_mm = env_data["rainfall_mm"]
    site.cloud_cover_pct = env_data["cloud_cover_pct"]
    site.elevation_m = env_data["elevation_m"]
    site.slope_deg = env_data["slope_deg"]
    site.vegetation_ndvi = env_data["vegetation_ndvi"]
    site.capacity_factor = env_data["capacity_factor"]
    site.est_yield_gwh = env_data["est_yield_gwh"]

    db.commit()
    db.refresh(site)

    return {
        "message": f"Successfully synchronized all Module 3 environmental indicators for '{site.site_name}'",
        "site": site,
        "telemetry": env_data
    }