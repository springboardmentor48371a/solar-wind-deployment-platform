from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import SessionLocal, User, UserRole
from app.models.project_site import Site
from app.api.auth import require_roles
from app.core.osm_service import scan_osm_infrastructure

router = APIRouter(prefix="/gis", tags=["Module 4: Geographic Intelligence & Spatial Analysis"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/scan/{site_id}")
async def run_osm_spatial_scan(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([
        UserRole.PLANNER.value,
        UserRole.GIS_ANALYST.value,
        UserRole.ADMIN.value
    ]))
):
    """
    Module 4: Executes Overpass spatial proximity analysis for a candidate site.
    Computes distances to grid substations, transmission lines, access roads,
    and protected buffer zones, then updates the site record.
    """
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Candidate site not found")

    spatial_data = await scan_osm_infrastructure(site.latitude, site.longitude)

    # Persist the infrastructure analysis directly to the site model
    site.existing_infrastructure = (
        f"Substation: {spatial_data['substation_dist_km']} km | "
        f"Line: {spatial_data['transmission_line_dist_km']} km | "
        f"Road: {spatial_data['access_road_dist_km']} km | "
        f"Risk: {spatial_data['interconnect_risk']}"
    )

    db.commit()
    db.refresh(site)

    return {
        "message": f"Spatial analysis completed for '{site.site_name}'",
        "site": site,
        "spatial_analytics": spatial_data
    }