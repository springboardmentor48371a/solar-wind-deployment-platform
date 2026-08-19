from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import List
from jose import jwt
from passlib.context import CryptContext

import models
import schemas
from database import engine, get_db

# Create all tables on startup
models.Base.metadata.create_all(bind=engine)

SECRET_KEY = "solar-wind-secret-key-for-jwt-token"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI(title="Solar & Wind Deployment Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ----------------- AUTHENTICATION ROUTES -----------------

@app.post("/api/auth/register")
def register(user_data: schemas.UserRegister, db: Session = Depends(get_db)):
    email_key = user_data.email.lower()
    
    existing_user = db.query(models.User).filter(models.User.email == email_key).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please sign in."
        )
    
    if user_data.password != user_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match."
        )
    
    if len(user_data.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long."
        )

    new_user = models.User(
        name=user_data.name,
        email=email_key,
        hashed_password=pwd_context.hash(user_data.password),
        role=user_data.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"sub": new_user.email, "name": new_user.name, "role": new_user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "name": new_user.name,
        "role": new_user.role,
        "email": new_user.email,
        "message": "Account registered and persisted successfully!"
    }

@app.post("/api/auth/login")
def login(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    email_key = credentials.email.lower()
    user = db.query(models.User).filter(models.User.email == email_key).first()

    if not user or not pwd_context.verify(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    token = create_access_token({"sub": user.email, "name": user.name, "role": credentials.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "name": user.name,
        "role": user.role,
        "email": user.email
    }

# ----------------- SITE PERSISTENCE ROUTES -----------------

@app.get("/api/sites", response_model=List[schemas.SiteResponse])
def get_sites(db: Session = Depends(get_db)):
    return db.query(models.Site).order_by(models.Site.created_at.desc()).all()

@app.post("/api/sites", response_model=schemas.SiteResponse)
def create_site(site: schemas.SiteCreate, db: Session = Depends(get_db)):
    db_site = models.Site(**site.model_dump())
    db.add(db_site)
    db.commit()
    db.refresh(db_site)
    return db_site