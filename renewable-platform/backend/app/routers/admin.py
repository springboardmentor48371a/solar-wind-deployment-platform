"""
Module 1 & 21: Administrator Panel Router.

Provides user management, role assignments, platform stats, and system diagnostic endpoints.
Only users with role `administrator` are permitted.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from .. import models, schemas
from ..database import get_db
from ..auth import get_current_user

router = APIRouter(prefix="/api/admin", tags=["Administrator"])


def _require_admin(user: models.User = Depends(get_current_user)):
    if user.role != models.RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Administrator privileges required")
    return user


class RoleUpdatePayload(BaseModel):
    role: models.RoleEnum


@router.get("/users", response_model=List[schemas.UserOut])
def list_all_users(db: Session = Depends(get_db), current_user: models.User = Depends(_require_admin)):
    return db.query(models.User).all()


@router.put("/users/{user_id}/role", response_model=schemas.UserOut)
def update_user_role(
    user_id: int, payload: RoleUpdatePayload, db: Session = Depends(get_db), current_user: models.User = Depends(_require_admin)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = payload.role
    db.commit()
    db.refresh(user)
    return user


@router.get("/system-stats")
def get_system_stats(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    total_users = db.query(models.User).count()
    total_projects = db.query(models.Project).count()
    total_sites = db.query(models.Site).count()

    scores = db.query(models.SiteScore).all()
    avg_score = (sum(s.overall_score for s in scores) / len(scores)) if scores else 0.0

    tech_counts = {"solar": 0, "wind": 0, "hybrid": 0}
    for s in scores:
        if s.recommended_technology:
            tech_counts[s.recommended_technology.value] = tech_counts.get(s.recommended_technology.value, 0) + 1

    return {
        "total_users": total_users,
        "total_projects": total_projects,
        "total_sites": total_sites,
        "average_suitability_score": round(avg_score, 1),
        "technology_distribution": tech_counts,
        "data_providers": {
            "climatology": "NASA POWER API (Climatology)",
            "elevation": "Open-Elevation API / SRTM",
            "infrastructure": "OpenStreetMap Overpass API",
            "geocoding": "Nominatim OpenStreetMap",
        }
    }
