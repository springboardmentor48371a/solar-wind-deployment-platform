from fastapi import FastAPI, HTTPException, status, Depends, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import List
from jose import jwt
from passlib.context import CryptContext
import requests

import models
import schemas
from database import engine, get_db
from services.landcover_service import classify_satellite_image

# Create all tables on startup
models.Base.metadata.create_all(bind=engine)

SECRET_KEY = "solar-wind-secret-key-for-jwt-token"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
preview_cache = {}
PREVIEW_CACHE_TTL = timedelta(hours=24)

app = FastAPI(title="Solar & Wind Deployment Intelligence API")

# Allow local frontend ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
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

@app.get("/api/sites/preview", response_model=schemas.SitePreview)
def preview_site(
    lat: float = Query(..., ge=-90, le=90),
    long: float = Query(..., ge=-180, le=180),
):
    cache_key = (round(lat, 5), round(long, 5))
    cached = preview_cache.get(cache_key)
    if cached and datetime.now(timezone.utc) - cached["cached_at"] < PREVIEW_CACHE_TTL:
        return cached["data"]

    headers = {"User-Agent": "solar-wind-deployment-platform/1.0"}
    try:
        geocode_response = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"format": "json", "lat": lat, "lon": long, "accept-language": "en"},
            headers=headers,
            timeout=8,
        )
        geocode_response.raise_for_status()
        geocode = geocode_response.json()

        elevation_response = requests.get(
            "https://api.opentopodata.org/v1/srtm30m",
            params={"locations": f"{lat},{long}"},
            timeout=8,
        )
        elevation_response.raise_for_status()
        elevation_results = elevation_response.json().get("results", [])
    except requests.RequestException as error:
        raise HTTPException(status_code=502, detail="Location data provider is unavailable.") from error

    address = geocode.get("address", {})
    fallback_name = f"Zone ({lat:.2f}, {long:.2f})"
    name = geocode.get("name") or address.get("city") or address.get("town") or address.get("village") or fallback_name
    region = ", ".join(
        value for value in (
            address.get("city") or address.get("town") or address.get("county"),
            address.get("state"),
            address.get("country"),
        ) if value
    ) or f"Coordinates: {lat:.4f}, {long:.4f}"
    elevation = elevation_results[0].get("elevation") if elevation_results else None
    data = {
        "name": name,
        "region": region,
        "elevation": f"{elevation} m" if elevation is not None else "Unavailable",
        "lat": lat,
        "long": long,
    }
    preview_cache[cache_key] = {"cached_at": datetime.now(timezone.utc), "data": data}
    return data

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

@app.delete("/api/sites/{site_id}")
def delete_site(site_id: int, db: Session = Depends(get_db)):
    site = db.query(models.Site).filter(models.Site.id == site_id).first()
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Site not found"
        )
    db.delete(site)
    db.commit()
    return {"message": "Site deleted successfully", "id": site_id}

# ----------------- GEOGRAPHIC INTELLIGENCE (EUROSAT) -----------------

@app.post("/api/gis/land-cover/classify")
async def analyze_land_cover(file: UploadFile = File(...)):
    """
    Module 4 & 7: Sentinel-2 Land Cover & Exclusion Zone Classifier.
    Analyzes uploaded satellite image tiles for land classification and suitability penalties.
    """
    image_bytes = await file.read()
    return classify_satellite_image(image_bytes)

# ----------------- APPLICATION ENTRY POINT -----------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)