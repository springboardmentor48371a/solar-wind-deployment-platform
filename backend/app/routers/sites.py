import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session, joinedload

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.project import Project
from app.models.site import Site
from app.models.user import User
from app.schemas.site import SiteCreate, SiteResponse, SiteUpdate

router = APIRouter(tags=["Sites"])


def get_project_or_404(project_id: uuid.UUID, db: Session) -> Project:
    project = db.query(Project).filter(Project.project_id == project_id).first()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )
    return project


def get_site_or_404(site_id: uuid.UUID, db: Session) -> Site:
    site = (
        db.query(Site)
        .options(joinedload(Site.project))
        .filter(Site.site_id == site_id)
        .first()
    )
    if site is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found.",
        )
    return site


@router.post(
    "/projects/{project_id}/sites",
    response_model=SiteResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_site(
    project_id: uuid.UUID,
    site_data: SiteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_project_or_404(project_id, db)

    site = Site(
        project_id=project_id,
        site_name=site_data.site_name,
        latitude=site_data.latitude,
        longitude=site_data.longitude,
        region=site_data.region,
        land_area=site_data.land_area,
        elevation=site_data.elevation,
        land_type=site_data.land_type,
        ownership=site_data.ownership,
    )

    db.add(site)
    db.commit()
    db.refresh(site)

    return site


@router.get("/projects/{project_id}/sites", response_model=list[SiteResponse])
def list_project_sites(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_project_or_404(project_id, db)
    return (
        db.query(Site)
        .filter(Site.project_id == project_id)
        .order_by(Site.site_name.asc())
        .all()
    )


@router.get("/sites/{site_id}", response_model=SiteResponse)
def get_site(
    site_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_site_or_404(site_id, db)


@router.patch("/sites/{site_id}", response_model=SiteResponse)
def update_site(
    site_id: uuid.UUID,
    site_data: SiteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    site = get_site_or_404(site_id, db)
    update_data = site_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(site, field, value)

    db.commit()
    db.refresh(site)

    return site


@router.delete("/sites/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_site(
    site_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    site = get_site_or_404(site_id, db)
    db.delete(site)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
