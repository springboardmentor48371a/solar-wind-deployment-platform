"""
Integrations — CRUD + outbound firing for the platform's five
integration categories (financial modeling, project management, SCADA/IoT,
power simulation, third-party analytics), backed by
models.IntegrationConnection. Generic webhook/REST connector by design:
point it at any compatible endpoint (Zapier, a Jira webhook, an
MQTT-to-HTTP bridge, Segment, a custom SCADA gateway) rather than
building five separate vendor SDK integrations with no way to know in
advance which vendor a given deployment actually uses.

Only Administrators and Project Managers manage connections — a stored
auth_header_value is effectively a credential, same trust level as the
platform's own database credentials.
"""

import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app import models, schemas, auth, authz
from app.database import get_db
from app.security import log_action
from app.services.integration_dispatch import fire_integration_event

router = APIRouter(prefix="/integrations", tags=["Integrations"])


def _require_manage_permission(current_user: models.User) -> None:
    if current_user.role not in authz.FULL_ACCESS_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Only Administrators and Project Managers can manage integration connections",
        )


@router.post("/", response_model=schemas.IntegrationConnectionOut, status_code=201)
def create_integration(
    request: Request,
    body: schemas.IntegrationConnectionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    _require_manage_permission(current_user)
    if body.project_id is not None:
        project = db.query(models.Project).filter(models.Project.id == body.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

    connection = models.IntegrationConnection(
        project_id=body.project_id,
        created_by_id=current_user.id,
        integration_type=body.integration_type,
        name=body.name,
        endpoint_url=body.endpoint_url,
        auth_header_name=body.auth_header_name,
        auth_header_value=body.auth_header_value,
        is_active=1,
    )
    db.add(connection)
    db.commit()
    db.refresh(connection)
    log_action(db, current_user.id, "create_integration", f"integration:{connection.id}", request.client.host)
    return connection


@router.get("/", response_model=list[schemas.IntegrationConnectionOut])
def list_integrations(
    project_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    query = db.query(models.IntegrationConnection)
    if project_id is not None:
        query = query.filter(models.IntegrationConnection.project_id == project_id)
    return query.order_by(models.IntegrationConnection.created_at.desc()).all()


@router.delete("/{integration_id}", status_code=204)
def delete_integration(
    integration_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    _require_manage_permission(current_user)
    connection = (
        db.query(models.IntegrationConnection)
        .filter(models.IntegrationConnection.id == integration_id)
        .first()
    )
    if not connection:
        raise HTTPException(status_code=404, detail="Integration connection not found")
    db.delete(connection)
    db.commit()


@router.post("/{integration_id}/test", response_model=schemas.IntegrationConnectionOut)
def test_integration(
    integration_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Fires a small test payload at the connection's endpoint_url and
    records whether it succeeded — lets an admin verify a webhook is
    reachable and correctly authenticated before relying on it for real
    events (see fire_integration_event below, called from alerting.py).
    """
    _require_manage_permission(current_user)
    connection = (
        db.query(models.IntegrationConnection)
        .filter(models.IntegrationConnection.id == integration_id)
        .first()
    )
    if not connection:
        raise HTTPException(status_code=404, detail="Integration connection not found")

    ok = fire_integration_event(connection, event_type="test", payload={"message": "Solstice OS test event"})
    connection.last_status = "ok" if ok else "error"
    connection.last_used_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(connection)
    return connection
