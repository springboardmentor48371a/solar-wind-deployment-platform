from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models.site import Site, DeploymentHistory
from ..models.project import Project
from ..models.user import User, UserRole
from ..schemas.site import SiteCreate, SiteUpdate, SiteStatusUpdate, SiteResponse, DeploymentHistoryResponse, SiteCompareResponse
from ..core.dependencies import get_current_user, require_roles

router = APIRouter(prefix="/sites", tags=["Sites"])

@router.post("/", response_model=SiteResponse, status_code=201)
def create_site(payload: SiteCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not db.query(Project).filter(Project.id == payload.project_id).first():
        raise HTTPException(status_code=404, detail="Project not found")
    site = Site(**payload.model_dump(), created_by=current_user.id)
    db.add(site)
    db.commit()
    db.refresh(site)
    return site

@router.get("/", response_model=List[SiteResponse])
def list_sites(project_id: int = Query(None), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    q = db.query(Site)
    if project_id:
        q = q.filter(Site.project_id == project_id)
    return q.all()

@router.get("/compare", response_model=SiteCompareResponse)
def compare_sites(ids: str = Query(..., description="Comma separated site IDs e.g. 1,2,3"), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
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
