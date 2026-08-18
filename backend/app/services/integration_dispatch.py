"""
Integration event dispatch — fires the actual outbound webhook calls to
connected IntegrationConnection rows, both for the manual "Test" button
(routers/integrations.py) and for real platform events (new alerts, new
suitability scores) via dispatch_event, called from alerting.py.

Split out from routers/integrations.py so a service module (alerting.py)
never has to import a router module to reach this — routers depend on
services, not the other way around.
"""

import datetime

import requests
from sqlalchemy.orm import Session

from app import models


def fire_integration_event(connection: models.IntegrationConnection, event_type: str, payload: dict) -> bool:
    """Best-effort outbound webhook call — never raises."""
    if not connection.is_active or not connection.endpoint_url:
        return False
    headers = {"Content-Type": "application/json"}
    if connection.auth_header_name and connection.auth_header_value:
        headers[connection.auth_header_name] = connection.auth_header_value
    try:
        response = requests.post(
            connection.endpoint_url,
            json={"event_type": event_type, "integration_type": connection.integration_type.value, **payload},
            headers=headers,
            timeout=8,
        )
        return response.ok
    except requests.RequestException as exc:  # noqa: BLE001
        print(f"Warning: integration webhook failed ({connection.name}): {exc}")
        return False


def dispatch_event(db: Session, project_id: int | None, event_type: str, payload: dict) -> None:
    """
    Fires event_type to every active IntegrationConnection scoped to
    project_id (plus any connection with no project_id set, treated as
    "fires on every project" — useful for a single portfolio-wide
    analytics/PM webhook). Best-effort per connection: one bad webhook
    endpoint never blocks the others or the caller (alert/score creation
    that triggered this).
    """
    query = db.query(models.IntegrationConnection).filter(models.IntegrationConnection.is_active == 1)
    if project_id is not None:
        query = query.filter(
            (models.IntegrationConnection.project_id == project_id)
            | (models.IntegrationConnection.project_id.is_(None))
        )
    connections = query.all()

    for connection in connections:
        ok = fire_integration_event(connection, event_type, payload)
        connection.last_status = "ok" if ok else "error"
        connection.last_used_at = datetime.datetime.utcnow()
    if connections:
        db.commit()
