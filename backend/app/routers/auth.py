from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional

from app import models, schemas, auth
from app.database import get_db
from app.security import limiter, log_action
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Used only to keep login's response time roughly constant whether or not
# the email exists (see login() below) — a real bcrypt hash of an
# arbitrary fixed string, generated once at import time rather than
# hardcoded, so there's no risk of it accidentally matching a real
# password hash format from a different bcrypt cost setting.
_DUMMY_PASSWORD_HASH = auth.hash_password("not-a-real-password-timing-safety-only")


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(schemas.Token):
    refresh_token: str


# All 6 roles are self-service — no staff PIN gate. This was removed as a
# deliberate, temporary simplification (see git history / conversation for
# context): registering as GIS Analyst, Project Manager, or Administrator
# no longer requires anything beyond picking the role. This is a real
# security tradeoff, not a cosmetic one — anyone can now self-register as
# Administrator with full platform access. Revisit before any real/public
# deployment.
NORMAL_ROLE = models.RoleEnum.planner
ALL_ROLES = {
    models.RoleEnum.planner,
    models.RoleEnum.investor_developer,
    models.RoleEnum.government_regulator,
    models.RoleEnum.gis_analyst,
    models.RoleEnum.project_manager,
    models.RoleEnum.admin,
}


@router.post("/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.rate_limit_auth)
def register(request: Request, user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    auth.validate_password_strength(user_in.password)

    requested_role = user_in.role
    if requested_role not in ALL_ROLES:
        # Anything that isn't one of the 6 known roles falls back to the
        # safest default — never trust an unrecognized client-supplied value.
        requested_role = NORMAL_ROLE

    user = models.User(
        full_name=user_in.full_name,
        email=user_in.email,
        hashed_password=auth.hash_password(user_in.password),
        role=requested_role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_action(db, user.id, "register", f"user:{user.id}", request.client.host)
    return user


@router.post("/login", response_model=TokenPair)
@limiter.limit(settings.rate_limit_auth)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    # OAuth2PasswordRequestForm uses "username" field for the email
    user = db.query(models.User).filter(models.User.email == form_data.username).first()

    # Always run a bcrypt verify, even when the user doesn't exist, against
    # a fixed dummy hash — bcrypt is deliberately slow, so skipping this
    # step for unknown emails would make "unknown email" respond
    # measurably faster than "known email, wrong password." That timing
    # gap is enough to enumerate which emails are registered without ever
    # seeing an error message that says so.
    password_ok = auth.verify_password(
        form_data.password, user.hashed_password if user else _DUMMY_PASSWORD_HASH
    )

    if not user or not password_ok:
        # Deliberately generic message — don't reveal whether the email exists
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    access_token = auth.create_access_token({"sub": str(user.id), "role": user.role.value})
    refresh_token = auth.create_refresh_token({"sub": str(user.id)})

    log_action(db, user.id, "login", f"user:{user.id}", request.client.host)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/refresh", response_model=schemas.Token)
@limiter.limit(settings.rate_limit_auth)
def refresh_access_token(
    request: Request, body: RefreshRequest, db: Session = Depends(get_db)
):
    payload = auth.decode_refresh_token(body.refresh_token)
    user_id = int(payload["sub"])
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    new_claims = {"sub": str(user.id), "role": user.role.value}
    # Carry the impersonation marker forward — otherwise a silent
    # access-token refresh partway through an admin's "view as" session
    # would drop the "impersonated_by" claim, and the frontend's banner
    # (and the audit trail's context) would misleadingly disappear while
    # the session is still, in fact, an impersonation.
    if payload.get("impersonated_by") is not None:
        new_claims["impersonated_by"] = payload["impersonated_by"]

    access_token = auth.create_access_token(new_claims)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.UserOut)
def read_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=120)
    email: Optional[str] = None


@router.patch("/me", response_model=schemas.UserOut)
def update_profile(
    body: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    User Profile Management (project spec, Module 1) — was only a
    change-password endpoint until this pass; a user had no way to
    update their own name or email at all.
    """
    if body.full_name is not None:
        current_user.full_name = body.full_name

    if body.email is not None and body.email != current_user.email:
        existing = db.query(models.User).filter(models.User.email == body.email).first()
        if existing:
            raise HTTPException(status_code=409, detail="That email is already in use by another account.")
        current_user.email = body.email

    db.commit()
    db.refresh(current_user)
    return current_user


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/change-password", response_model=schemas.UserOut)
def change_password(
    request: Request,
    body: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if not auth.verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    auth.validate_password_strength(body.new_password)
    current_user.hashed_password = auth.hash_password(body.new_password)
    db.commit()
    db.refresh(current_user)

    log_action(db, current_user.id, "change_password", f"user:{current_user.id}", request.client.host)
    return current_user
