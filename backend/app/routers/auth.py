from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError
import httpx

from ..database import get_db
from ..models.user import User
from ..schemas.user import UserRegister, TokenResponse, RefreshRequest, OAuthCallback
from ..core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from ..core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        full_name=payload.full_name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenResponse(
        access_token=create_access_token(user.id, user.role),
        refresh_token=create_refresh_token(user.id),
    )

@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username, User.is_active == True).first()
    if not user or not user.hashed_password or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(
        access_token=create_access_token(user.id, user.role),
        refresh_token=create_refresh_token(user.id),
    )

@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    try:
        data = decode_token(payload.refresh_token)
        if data.get("type") != "refresh":
            raise ValueError
        user_id = int(data["sub"])
    except (JWTError, ValueError, KeyError):
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return TokenResponse(
        access_token=create_access_token(user.id, user.role),
        refresh_token=create_refresh_token(user.id),
    )

@router.get("/google/login")
def google_login():
    params = (
        f"client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri=http://localhost:8000/auth/google/callback"
        f"&response_type=code&scope=openid email profile"
    )
    return {"url": f"https://accounts.google.com/o/oauth2/v2/auth?{params}"}

@router.get("/google/callback")
async def google_callback(code: str, db: Session = Depends(get_db)):
    from fastapi.responses import RedirectResponse
    async with httpx.AsyncClient() as client:
        token_res = await client.post("https://oauth2.googleapis.com/token", data={
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": "http://localhost:8000/auth/google/callback",
            "grant_type": "authorization_code",
        })
        if token_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Google token exchange failed")
        userinfo_res = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {token_res.json()['access_token']}"}
        )
    info = userinfo_res.json()
    user = db.query(User).filter(User.oauth_sub == info["sub"], User.oauth_provider == "google").first()
    if not user:
        user = db.query(User).filter(User.email == info["email"]).first()
        if user:
            user.oauth_provider = "google"
            user.oauth_sub = info["sub"]
        else:
            user = User(
                full_name=info.get("name", ""),
                email=info["email"],
                oauth_provider="google",
                oauth_sub=info["sub"],
                profile_picture=info.get("picture"),
                is_verified=True,
            )
            db.add(user)
        db.commit()
        db.refresh(user)
    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id)
    return RedirectResponse(f"http://localhost:5173?access_token={access_token}&refresh_token={refresh_token}")
