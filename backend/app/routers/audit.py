from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
import datetime

from app import models, auth
from app.database import get_db

router = APIRouter(prefix="/admin/audit-logs", tags=["Admin — Audit Log"])


class AuditLogOut(BaseModel):
    id: int
    user_id: Optional[int]
    action: str
    resource: Optional[str]
    ip_address: Optional[str]
    created_at: datetime.datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=List[AuditLogOut])
def list_audit_logs(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles([models.RoleEnum.admin])),
):
    return (
        db.query(models.AuditLog)
        .order_by(models.AuditLog.created_at.desc())
        .limit(min(limit, 500))
        .all()
    )
