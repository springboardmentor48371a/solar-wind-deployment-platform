from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app import models, schemas, auth, authz
from app.database import get_db
from app.security import log_action

router = APIRouter(prefix="/projects", tags=["Projects"])

# Roles allowed to create projects at all (ownership rules on top of this
# are enforced via app.authz for read/update/delete on a *specific* project)
CAN_CREATE = list(authz.CAN_CREATE_ROLES)


@router.post("/", response_model=schemas.ProjectOut, status_code=201)
def create_project(
    request: Request,
    project_in: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(CAN_CREATE)),
):
    if project_in.region_id is not None:
        region = db.query(models.Region).filter(models.Region.id == project_in.region_id).first()
        if not region:
            raise HTTPException(status_code=404, detail="Region not found")

    project = models.Project(
        name=project_in.name,
        objective=project_in.objective,
        region=project_in.region,
        region_id=project_in.region_id,
        owner_id=current_user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    log_action(db, current_user.id, "create_project", f"project:{project.id}", request.client.host)
    return project


@router.get("/", response_model=List[schemas.ProjectOut])
def list_projects(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if current_user.role in authz.READ_ALL_ROLES:
        return db.query(models.Project).all()
    return db.query(models.Project).filter(models.Project.owner_id == current_user.id).all()


@router.get("/{project_id}", response_model=schemas.ProjectOut)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    authz.require_project_read(project, current_user)
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(
    request: Request,
    project_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    authz.require_project_write(project, current_user)

    db.delete(project)
    db.commit()

    log_action(db, current_user.id, "delete_project", f"project:{project_id}", request.client.host)
    return None
