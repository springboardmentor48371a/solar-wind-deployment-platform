from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.user import SessionLocal, User, UserRole
from app.models.project_site import Project, Site
from app.schemas.project_site import (
    ProjectCreate, ProjectResponse, 
    SiteCreate, SiteResponse, 
    SiteGisUpdate, SiteApprovalUpdate
)
from app.api.auth import get_current_user, require_roles

router = APIRouter(prefix="/projects", tags=["Project & Site Management Workflow"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------------------------------------------
# Project creation route accepting both "/" and ""
@router.post("", response_model=ProjectResponse)
@router.post("/", response_model=ProjectResponse)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([
        UserRole.PLANNER.value,
        UserRole.PROJECT_MANAGER.value,
        UserRole.ADMIN.value
    ]))
):
    project = Project(
        name=payload.name,
        description=payload.description,
        target_capacity_mw=payload.target_capacity_mw,
        region=payload.region,
        status=payload.status,
        timeline_cod=payload.timeline_cod,
        owner_id=current_user.id
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@router.get("", response_model=List[ProjectResponse])
@router.get("/", response_model=List[ProjectResponse])
def get_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Project).all()

    project = Project(
        name=payload.name,
        description=payload.description,
        target_capacity_mw=payload.target_capacity_mw,
        region=payload.region,
        status=payload.status,
        timeline_cod=payload.timeline_cod,
        owner_id=current_user.id
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@router.get("/", response_model=List[ProjectResponse])
def get_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Project).all()

# -------------------------------------------------------------
# 2. SITE REGISTRATION
# Allowed: Energy Planner, GIS Analyst, Admin
# -------------------------------------------------------------
@router.post("/sites", response_model=SiteResponse)
def register_site(
    payload: SiteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([
        UserRole.PLANNER.value,
        UserRole.GIS_ANALYST.value,
        UserRole.ADMIN.value
    ]))
):
    project = db.query(Project).filter(Project.id == payload.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Parent project does not exist")

    site = Site(
        project_id=payload.project_id,
        site_name=payload.site_name,
        latitude=payload.latitude,
        longitude=payload.longitude,
        elevation_m=payload.elevation_m,
        land_area_sqkm=payload.land_area_sqkm,
        region=payload.region,
        land_ownership=payload.land_ownership,
        existing_infrastructure=payload.existing_infrastructure
    )
    db.add(site)
    db.commit()
    db.refresh(site)
    return site

@router.get("/sites", response_model=List[SiteResponse])
def get_sites(
    project_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if project_id:
        return db.query(Site).filter(Site.project_id == project_id).all()
    return db.query(Site).all()

# -------------------------------------------------------------
# 3. GIS & TERRAIN DATA EDITING
# Allowed: GIS Analyst, Admin (Energy Planner and PM strictly forbidden)
# -------------------------------------------------------------
@router.put("/sites/{site_id}/gis-data", response_model=SiteResponse)
def update_gis_data(
    site_id: int,
    payload: SiteGisUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([
        UserRole.GIS_ANALYST.value,
        UserRole.ADMIN.value
    ]))
):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    for field, val in payload.dict(exclude_unset=True).items():
        setattr(site, field, val)

    db.commit()
    db.refresh(site)
    return site

# -------------------------------------------------------------
# 4. FINAL APPROVAL & SHORTLISTING
# Allowed: Project Manager, Admin (Planner and GIS Analyst strictly forbidden)
# -------------------------------------------------------------
@router.put("/sites/{site_id}/approval", response_model=SiteResponse)
def approve_site(
    site_id: int,
    payload: SiteApprovalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([
        UserRole.PROJECT_MANAGER.value,
        UserRole.ADMIN.value
    ]))
):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    site.is_approved = payload.is_approved
    if payload.is_shortlisted is not None:
        site.is_shortlisted = payload.is_shortlisted
    if payload.approval_notes is not None:
        site.approval_notes = payload.approval_notes

    db.commit()
    db.refresh(site)
    return site