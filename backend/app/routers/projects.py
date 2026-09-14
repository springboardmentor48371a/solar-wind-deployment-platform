from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models.project import Project, Region
from ..models.user import User, UserRole
from ..schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, RegionCreate, RegionResponse
from ..core.dependencies import get_current_user, require_roles

router = APIRouter(prefix="/projects", tags=["Projects"])
region_router = APIRouter(prefix="/regions", tags=["Regions"])

# --- Regions ---

@region_router.post("/", response_model=RegionResponse, status_code=201)
def create_region(payload: RegionCreate, db: Session = Depends(get_db), _: User = Depends(require_roles(UserRole.energy_planner, UserRole.project_manager))):
    region = Region(**payload.model_dump())
    db.add(region)
    db.commit()
    db.refresh(region)
    return region

@region_router.get("/", response_model=List[RegionResponse])
def list_regions(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Region).all()

@region_router.delete("/{region_id}", status_code=204)
def delete_region(region_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(UserRole.energy_planner, UserRole.project_manager))):
    region = db.query(Region).filter(Region.id == region_id).first()
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    db.delete(region)
    db.commit()

# --- Projects ---

@router.post("/", response_model=ProjectResponse, status_code=201)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.energy_planner, UserRole.project_manager))):
    project = Project(**payload.model_dump(), created_by=current_user.id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@router.get("/", response_model=List[ProjectResponse])
def list_projects(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Project).all()

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: int, payload: ProjectUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.energy_planner, UserRole.project_manager))):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if current_user.role != UserRole.project_manager and project.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project

@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.energy_planner, UserRole.project_manager))):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if current_user.role != UserRole.project_manager and project.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(project)
    db.commit()
