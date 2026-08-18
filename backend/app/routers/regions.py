"""
Region management — PDF item "2. Project & Site Management > Region
management", previously only a free-text field on Project. This gives
regions a real lifecycle: create/list/get/update/delete, independent of
any one project, so a GIS Analyst or Admin can maintain a canonical list
of regions (with a bounding box for map framing) that Planners then pick
from when creating a project.

Permissions: any authenticated user can read; creating/editing/deleting
a region is restricted to roles that manage geographic/reference data
(Admin, GIS Analyst, Project Manager) — the same roles trusted to
run analysis on any project in authz.py, since maintaining the region
list is the same kind of platform-reference-data responsibility.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func

from app import models, schemas, auth
from app.database import get_db
from app.security import log_action

router = APIRouter(prefix="/regions", tags=["Regions"])

MANAGE_REGIONS_ROLES = [
    models.RoleEnum.admin,
    models.RoleEnum.gis_analyst,
    models.RoleEnum.project_manager,
]


def _get_region_or_404(region_id: int, db: Session) -> models.Region:
    region = db.query(models.Region).filter(models.Region.id == region_id).first()
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    return region


def _with_project_count(db: Session, region: models.Region) -> schemas.RegionOut:
    count = db.query(func.count(models.Project.id)).filter(
        models.Project.region_id == region.id
    ).scalar()
    out = schemas.RegionOut.model_validate(region)
    out.project_count = count or 0
    return out


@router.post("/", response_model=schemas.RegionOut, status_code=201)
def create_region(
    request: Request,
    region_in: schemas.RegionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(MANAGE_REGIONS_ROLES)),
):
    existing = db.query(models.Region).filter(models.Region.name == region_in.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="A region with this name already exists")

    region = models.Region(**region_in.model_dump(), created_by_id=current_user.id)
    db.add(region)
    db.commit()
    db.refresh(region)

    log_action(db, current_user.id, "create_region", f"region:{region.id}", request.client.host)
    return _with_project_count(db, region)


@router.get("/", response_model=List[schemas.RegionOut])
def list_regions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    regions = db.query(models.Region).order_by(models.Region.name).all()
    return [_with_project_count(db, r) for r in regions]


@router.get("/{region_id}", response_model=schemas.RegionOut)
def get_region(
    region_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    region = _get_region_or_404(region_id, db)
    return _with_project_count(db, region)


@router.put("/{region_id}", response_model=schemas.RegionOut)
def update_region(
    request: Request,
    region_id: int,
    region_in: schemas.RegionUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(MANAGE_REGIONS_ROLES)),
):
    region = _get_region_or_404(region_id, db)

    updates = region_in.model_dump(exclude_unset=True)
    if "name" in updates and updates["name"] and updates["name"] != region.name:
        clash = db.query(models.Region).filter(models.Region.name == updates["name"]).first()
        if clash:
            raise HTTPException(status_code=409, detail="A region with this name already exists")

    for field, value in updates.items():
        setattr(region, field, value)

    db.commit()
    db.refresh(region)
    log_action(db, current_user.id, "update_region", f"region:{region.id}", request.client.host)
    return _with_project_count(db, region)


@router.delete("/{region_id}", status_code=204)
def delete_region(
    request: Request,
    region_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(MANAGE_REGIONS_ROLES)),
):
    region = _get_region_or_404(region_id, db)

    linked = db.query(func.count(models.Project.id)).filter(
        models.Project.region_id == region.id
    ).scalar()
    if linked:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot delete: {linked} project(s) still reference this region. "
            "Reassign or clear their region first.",
        )

    db.delete(region)
    db.commit()
    log_action(db, current_user.id, "delete_region", f"region:{region_id}", request.client.host)
