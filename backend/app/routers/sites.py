from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models.site import Site, DeploymentHistory
from ..models.project import Project, Region
from ..models.user import User, UserRole
from ..schemas.site import SiteCreate, SiteUpdate, SiteStatusUpdate, SiteResponse, DeploymentHistoryResponse, SiteCompareResponse, LocationPreview
from ..core.dependencies import get_current_user, require_roles
from ..services.geocoding import reverse_geocode
from ..services.environmental import fetch_elevation

router = APIRouter(prefix="/sites", tags=["Sites"])

async def get_or_create_region(db: Session, country: str, state: str) -> Region:
    """Find existing region or create a new one from geocoded data."""
    region = db.query(Region).filter(
        Region.country == country,
        Region.state == state
    ).first()
    if not region:
        region = Region(
            name=state or country,
            country=country,
            state=state,
        )
        db.add(region)
        db.commit()
        db.refresh(region)
    return region

@router.get("/preview", response_model=LocationPreview)
async def preview_location(
    lat: float = Query(...),
    lon: float = Query(...),
    _: User = Depends(get_current_user)
):
    """Preview what location coordinates resolve to before creating a site."""
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        raise HTTPException(status_code=400, detail="Invalid coordinates. Latitude must be -90 to 90, longitude -180 to 180.")

    location = await reverse_geocode(lat, lon)
    if not location:
        raise HTTPException(status_code=404, detail="No location found for these coordinates. Please check and try again.")

    elevation = await fetch_elevation(lat, lon)

    return LocationPreview(
        latitude=lat,
        longitude=lon,
        country=location["country"],
        state=location.get("state"),
        city=location.get("city"),
        display_name=location["display_name"],
        elevation=elevation,
    )

@router.post("/", response_model=SiteResponse, status_code=201)
async def create_site(payload: SiteCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not db.query(Project).filter(Project.id == payload.project_id).first():
        raise HTTPException(status_code=404, detail="Project not found")

    if not (-90 <= payload.latitude <= 90) or not (-180 <= payload.longitude <= 180):
        raise HTTPException(status_code=400, detail="Invalid coordinates.")

    # Reverse geocode to get region
    location = await reverse_geocode(payload.latitude, payload.longitude)
    if not location:
        raise HTTPException(status_code=400, detail="No location found for these coordinates. Please check and try again.")

    # Auto fetch elevation
    elevation = await fetch_elevation(payload.latitude, payload.longitude)

    # Get or create region
    region = await get_or_create_region(db, location["country"], location.get("state", ""))

    # Auto assign region to project if not already set
    project = db.query(Project).filter(Project.id == payload.project_id).first()
    if not project.region_id:
        project.region_id = region.id
        db.commit()

    # Create site
    site = Site(
        name=payload.name,
        project_id=payload.project_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        elevation=elevation,
        energy_type=payload.energy_type,
        land_ownership=payload.land_ownership,
        notes=payload.notes,
        created_by=current_user.id,
    )
    db.add(site)
    db.commit()
    db.refresh(site)

    # Auto-fetch environmental data
    try:
        from ..models.environmental import EnvironmentalData
        from ..services.environmental import collect_environmental_data
        records = await collect_environmental_data(site.latitude, site.longitude, 30)
        for r in records:
            db.add(EnvironmentalData(site_id=site.id, **r))
        db.commit()
    except Exception:
        pass

    return site

@router.get("/", response_model=List[SiteResponse])
def list_sites(project_id: int = Query(None), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    q = db.query(Site)
    if project_id:
        q = q.filter(Site.project_id == project_id)
    return q.all()

@router.get("/compare", response_model=SiteCompareResponse)
def compare_sites(ids: str = Query(...), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    site_ids = [int(i) for i in ids.split(",")]
    sites = db.query(Site).filter(Site.id.in_(site_ids)).all()
    if len(sites) < 2:
        raise HTTPException(status_code=400, detail="Provide at least 2 site IDs to compare")
    return SiteCompareResponse(sites=sites)

@router.get("/{site_id}", response_model=SiteResponse)
def get_site(site_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return site

@router.patch("/{site_id}", response_model=SiteResponse)
def update_site(site_id: int, payload: SiteUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    if site.created_by != current_user.id and current_user.role != UserRole.administrator:
        raise HTTPException(status_code=403, detail="Not authorized")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(site, field, value)
    db.commit()
    db.refresh(site)
    return site

@router.patch("/{site_id}/status", response_model=SiteResponse)
def update_site_status(site_id: int, payload: SiteStatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.administrator, UserRole.energy_planner, UserRole.project_manager))):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    history = DeploymentHistory(
        site_id=site.id,
        changed_by=current_user.id,
        previous_status=site.status,
        new_status=payload.status,
        notes=payload.notes
    )
    site.status = payload.status
    db.add(history)
    db.commit()
    db.refresh(site)
    return site

@router.get("/{site_id}/history", response_model=List[DeploymentHistoryResponse])
def get_site_history(site_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return site.history

@router.delete("/{site_id}", status_code=204)
def delete_site(site_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    if site.created_by != current_user.id and current_user.role != UserRole.administrator:
        raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(site)
    db.commit()
