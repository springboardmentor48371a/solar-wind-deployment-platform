from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas, auth, authz
from app.database import get_db

router = APIRouter(prefix="/alerts", tags=["Alerts"])


def _visible_alert_ids(db: Session, current_user: models.User) -> set | None:
    """
    Returns the set of project IDs whose alerts `current_user` is allowed
    to see, or None if they can see every project's alerts (the
    portfolio-wide roles). Mirrors authz.can_read_project's ownership rule
    so alerts never leak across users who each only own their own
    projects — a Planner should not see another Planner's "high wind
    speed" or "suitability updated" alerts just because both hit /alerts/.
    """
    if current_user.role in authz.READ_ALL_ROLES:
        return None
    owned = db.query(models.Project.id).filter(models.Project.owner_id == current_user.id).all()
    return {row[0] for row in owned}


@router.get("/", response_model=List[schemas.AlertOut])
def list_alerts(
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    query = db.query(models.Alert)
    if unread_only:
        query = query.filter(models.Alert.is_read == 0)

    visible_project_ids = _visible_alert_ids(db, current_user)
    if visible_project_ids is not None:
        # Alerts with no project_id are platform-wide/system alerts
        # (e.g. manually created by an admin without linking a project) —
        # those stay visible to everyone. Anything tied to a specific
        # project is scoped to that project's owner (or a portfolio-wide role).
        query = query.filter(
            (models.Alert.project_id.is_(None))
            | (models.Alert.project_id.in_(visible_project_ids))
        )

    return query.order_by(models.Alert.created_at.desc()).limit(100).all()


@router.post("/", response_model=schemas.AlertOut, status_code=201)
def create_alert(
    alert_in: schemas.AlertCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        auth.require_roles([models.RoleEnum.admin, models.RoleEnum.project_manager])
    ),
):
    """Manual alert creation — system-generated alerts come from the scoring/weather services."""
    alert = models.Alert(**alert_in.model_dump())
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@router.patch("/{alert_id}/read", response_model=schemas.AlertOut)
def mark_alert_read(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if alert.project_id is not None:
        project = db.query(models.Project).filter(models.Project.id == alert.project_id).first()
        # If the project was since deleted, fall through and allow — nothing
        # left to protect. Otherwise enforce the same ownership rule as
        # everywhere else so a user can't mark another user's alert read.
        if project is not None:
            authz.require_project_read(project, current_user)

    alert.is_read = 1
    db.commit()
    db.refresh(alert)
    return alert
