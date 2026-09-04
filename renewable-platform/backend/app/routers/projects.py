"""Module 2: Project & Site Management — project-level endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..auth import get_current_user

router = APIRouter(prefix="/api/projects", tags=["Projects"])


@router.post("", response_model=schemas.ProjectOut)
def create_project(payload: schemas.ProjectCreate, db: Session = Depends(get_db),
                    current_user: models.User = Depends(get_current_user)):
    project = models.Project(
        name=payload.name,
        description=payload.description,
        objective=payload.objective,
        region=payload.region,
        owner_id=current_user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    out = schemas.ProjectOut.model_validate(project)
    out.site_count = 0
    return out


@router.get("", response_model=List[schemas.ProjectOut])
def list_projects(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    projects = db.query(models.Project).filter(models.Project.owner_id == current_user.id).all()
    results = []
    for p in projects:
        out = schemas.ProjectOut.model_validate(p)
        out.site_count = len(p.sites)
        results.append(out)
    return results


@router.get("/{project_id}", response_model=schemas.ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    out = schemas.ProjectOut.model_validate(project)
    out.site_count = len(project.sites)
    return out


@router.put("/{project_id}", response_model=schemas.ProjectOut)
def update_project(project_id: int, payload: schemas.ProjectCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project.name = payload.name
    if payload.description is not None: project.description = payload.description
    if payload.objective is not None: project.objective = payload.objective
    if payload.region is not None: project.region = payload.region
    db.commit()
    db.refresh(project)
    out = schemas.ProjectOut.model_validate(project)
    out.site_count = len(project.sites)
    return out


@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return {"deleted": True}

