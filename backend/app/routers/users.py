from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app import models, schemas, auth
from app.database import get_db
from app.security import log_action

router = APIRouter(prefix="/admin/users", tags=["Admin — User Management"])

ADMIN_ONLY = [models.RoleEnum.admin]


class RoleUpdate(BaseModel):
    role: models.RoleEnum


class ActiveUpdate(BaseModel):
    is_active: bool


class ImpersonateResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@router.get("/", response_model=List[schemas.UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(ADMIN_ONLY)),
):
    return db.query(models.User).all()


@router.patch("/{user_id}/role", response_model=schemas.UserOut)
def update_user_role(
    request: Request,
    user_id: int,
    body: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(ADMIN_ONLY)),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = body.role
    db.commit()
    db.refresh(user)

    log_action(
        db, current_user.id, "update_user_role", f"user:{user_id} -> {body.role.value}",
        request.client.host,
    )
    return user


@router.patch("/{user_id}/active", response_model=schemas.UserOut)
def update_user_active(
    request: Request,
    user_id: int,
    body: ActiveUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(ADMIN_ONLY)),
):
    if user_id == current_user.id and not body.is_active:
        raise HTTPException(status_code=400, detail="You cannot disable your own account")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = 1 if body.is_active else 0
    db.commit()
    db.refresh(user)

    log_action(
        db, current_user.id, "update_user_active", f"user:{user_id} -> {body.is_active}",
        request.client.host,
    )
    return user


@router.post("/{user_id}/impersonate", response_model=ImpersonateResponse)
def impersonate_user(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles(ADMIN_ONLY)),
):
    """
    "View as" — lets an Administrator browse the app as another user, to
    check what they see or reproduce a support issue, without knowing
    that user's password.

    Deliberately restricted:
    - Never yourself (pointless, and would be confusing in the UI)
    - Never another Administrator (an admin-to-admin takeover path is a
      meaningfully bigger risk than admin-to-anyone-else, and there's no
      legitimate "what does this admin see" use case that outweighs it)
    - Target account must be active

    Every impersonation is written to the audit log with both the acting
    admin's id and the target's id. The frontend is responsible for
    keeping the admin's own tokens stashed locally so "return to admin"
    doesn't need another server round-trip.
    """
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You're already signed in as yourself")

    target = db.query(models.User).filter(models.User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.role == models.RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Administrators cannot impersonate other Administrators")
    if not target.is_active:
        raise HTTPException(status_code=400, detail="Cannot impersonate a disabled account")

    access_token = auth.create_access_token(
        {"sub": str(target.id), "role": target.role.value, "impersonated_by": current_user.id}
    )
    # Also carried on the refresh token — see refresh_access_token in
    # routers/auth.py for why: without this, refreshing mid-impersonation
    # would silently turn the session back into a normal one.
    refresh_token = auth.create_refresh_token(
        {"sub": str(target.id), "impersonated_by": current_user.id}
    )

    log_action(
        db, current_user.id, "impersonate_start", f"user:{target.id}", request.client.host,
    )
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
