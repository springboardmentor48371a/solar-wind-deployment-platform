import json
import secrets
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.roles import RoleName
from app.core.security import (
    create_access_token,
    get_jwt_secret_key,
    hash_password,
    verify_password,
)
from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.authorization import require_roles
from app.models.role import Role
from app.models.user import User
from app.schemas.user import (
    TokenResponse,
    UserRegisterRequest,
    UserRegisterResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


@router.post(
    "/register",
    response_model=UserRegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(user_data: UserRegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    selected_role = db.query(Role).filter(Role.role_name == user_data.role).first()
    if selected_role is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected role is not configured.",
        )

    new_user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        phone_number=user_data.phone_number,
        organization=user_data.organization,
        role_id=selected_role.role_id,
    )

    db.add(new_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    db.refresh(new_user)

    return UserRegisterResponse(
        user_id=new_user.user_id,
        full_name=new_user.full_name,
        email=new_user.email,
        role=selected_role.role_name,
        account_status=new_user.account_status,
    )


@router.post("/login", response_model=TokenResponse)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    invalid_credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user = db.query(User).filter(User.email == form_data.username).first()
    if user is None:
        raise invalid_credentials_exception

    if not verify_password(form_data.password, user.password_hash):
        raise invalid_credentials_exception

    if user.account_status != "active":
        raise invalid_credentials_exception

    access_token = create_access_token(subject=str(user.user_id))
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)):
    return UserResponse(
        user_id=current_user.user_id,
        full_name=current_user.full_name,
        email=current_user.email,
        role=current_user.role.role_name,
        account_status=current_user.account_status,
    )


def create_google_oauth_state() -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    return jwt.encode(
        {
            "purpose": "google_oauth_state",
            "nonce": secrets.token_urlsafe(24),
            "exp": expires_at,
        },
        get_jwt_secret_key(),
        algorithm=get_settings().jwt_algorithm,
    )


def validate_google_oauth_state(state: str) -> None:
    try:
        payload = jwt.decode(
            state,
            get_jwt_secret_key(),
            algorithms=[get_settings().jwt_algorithm],
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Google OAuth state.",
        )

    if payload.get("purpose") != "google_oauth_state":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Google OAuth state.",
        )


def require_google_settings():
    settings = get_settings()
    if (
        not settings.google_client_id
        or settings.google_client_secret is None
        or not settings.google_redirect_uri
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured.",
        )
    return settings


def exchange_google_code_for_token(code: str) -> str:
    settings = require_google_settings()
    form_data = urllib.parse.urlencode(
        {
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret.get_secret_value(),
            "redirect_uri": settings.google_redirect_uri,
            "grant_type": "authorization_code",
        },
    ).encode("utf-8")

    request = urllib.request.Request(
        GOOGLE_TOKEN_URL,
        data=form_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to complete Google token exchange.",
        )

    access_token = payload.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Google token response did not include an access token.",
        )

    return access_token


def fetch_google_userinfo(access_token: str) -> dict:
    request = urllib.request.Request(
        GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to fetch Google user information.",
        )


def get_or_create_google_user(userinfo: dict, db: Session) -> User:
    email = userinfo.get("email")
    email_verified = userinfo.get("email_verified")
    full_name = userinfo.get("name") or email

    if not email or email_verified is not True:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account email is unavailable or unverified.",
        )

    user = db.query(User).filter(User.email == email).first()
    if user is not None:
        return user

    default_role = db.query(Role).filter(Role.role_name == RoleName.PLANNER).first()
    if default_role is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Default role 'Planner' is not configured.",
        )

    password_hash = hash_password(secrets.token_urlsafe(32))
    user = User(
        full_name=full_name[:100],
        email=email,
        password_hash=password_hash,
        role_id=default_role.role_id,
    )

    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise

    db.refresh(user)
    return user


@router.get("/google/login")
def google_login():
    settings = require_google_settings()
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": create_google_oauth_state(),
        "access_type": "offline",
        "prompt": "select_account",
    }
    return RedirectResponse(f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}")


@router.get("/google/callback")
def google_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    settings = require_google_settings()

    if error:
        return RedirectResponse(
            f"{settings.frontend_origin}/login?oauth_error={urllib.parse.quote(error)}",
        )

    if not code or not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google OAuth callback is missing code or state.",
        )

    validate_google_oauth_state(state)
    google_access_token = exchange_google_code_for_token(code)
    userinfo = fetch_google_userinfo(google_access_token)
    user = get_or_create_google_user(userinfo, db)
    access_token = create_access_token(subject=str(user.user_id))

    return RedirectResponse(
        f"{settings.frontend_origin}/auth/google/callback#access_token={access_token}",
    )


@router.get("/planner-test")
def planner_test(
    current_user: User = Depends(require_roles(RoleName.PLANNER)),
):
    return {"message": "Planner access granted"}


@router.get("/gis-test")
def gis_test(
    current_user: User = Depends(require_roles(RoleName.GIS_ANALYST)),
):
    return {"message": "GIS Analyst access granted"}


@router.get("/project-manager-test")
def project_manager_test(
    current_user: User = Depends(require_roles(RoleName.PROJECT_MANAGER)),
):
    return {"message": "Project Manager access granted"}


@router.get("/admin-test")
def admin_test(
    current_user: User = Depends(require_roles(RoleName.ADMIN)),
):
    return {"message": "Admin access granted"}
