from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from geoalchemy2 import WKTElement
from ..core.database import get_db
from ..models.site import Site
from ..models.project import Project
from ..models.user import User
from ..schemas.site import SiteCreate, SiteUpdate, SiteResponse
from .auth import get_current_user

router = APIRouter(prefix="/sites", tags=["Sites"])

@router.post("/", response_model=SiteResponse)
def create_site(
    site_data: SiteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == site_data.project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    point_wkt = f"POINT({site_data.longitude} {site_data.latitude})"
    geometry = WKTElement(point_wkt, srid=4326)
    
    new_site = Site(
        **site_data.model_dump(exclude={'project_id'}),
        project_id=site_data.project_id,
        geometry=geometry
    )
    
    db.add(new_site)
    db.commit()
    db.refresh(new_site)
    return new_site

@router.get("/", response_model=List[SiteResponse])
def get_sites(
    project_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Site)
    if project_id:
        query = query.filter(Site.project_id == project_id)
    sites = query.offset(skip).limit(limit).all()
    return sites

@router.get("/{site_id}", response_model=SiteResponse)
def get_site(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found"
        )
    return site

@router.put("/{site_id}", response_model=SiteResponse)
def update_site(
    site_id: int,
    site_data: SiteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found"
        )
    
    for key, value in site_data.model_dump(exclude_unset=True).items():
        setattr(site, key, value)
    
    db.commit()
    db.refresh(site)
    return site

@router.delete("/{site_id}")
def delete_site(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found"
        )
    
    db.delete(site)
    db.commit()
    return {"message": "Site deleted successfully"}