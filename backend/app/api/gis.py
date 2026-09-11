from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import SessionLocal, User, UserRole
from app.models.project_site import Site
from app.api.auth import get_current_user, require_roles
from app.core.osm_service import scan_osm_infrastructure

router = APIRouter(prefix="/gis", tags=["Module 4: Geographic Intelligence & Spatial Analysis"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/proximity-preview")
async def preview_infrastructure_proximity(
    latitude: float,
    longitude: float,
    current_user: User = Depends(get_current_user)
):
    """Preview distances to substations, transmission corridors, and roads using OpenStreetMap."""
    data = await scan_osm_infrastructure(latitude, longitude)
    return data

@router.post("/scan/{site_id}")
async def scan_and_update_site_gis(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([
        UserRole.GIS_ANALYST.value,
        UserRole.ADMIN.value
    ]))
):
    """
    Scans OpenStreetMap around the site's coordinates and updates its
    existing infrastructure summary in the database.
    """
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    gis_data = await scan_osm_infrastructure(site.latitude, site.longitude)

    site.existing_infrastructure = gis_data["infrastructure_summary"]
    db.commit()
    db.refresh(site)

    return {
        "message": f"OSM infrastructure scan completed for '{site.site_name}'",
        "site": site,
        "spatial_analytics": gis_data
    }