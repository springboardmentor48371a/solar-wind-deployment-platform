import uuid
import requests
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from sqlalchemy import (
    create_engine, 
    Column, 
    String, 
    Float, 
    Integer, 
    Text, 
    DateTime, 
    ForeignKey
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship

# Environmental data extraction & AHP scoring + ML inference imports
from services.environmental_service import fetch_realtime_environmental_factors
from services.scoring_service import compute_site_suitability

# =====================================================================
# 1. DATABASE CONFIGURATION & SESSIONS
# =====================================================================

DATABASE_URL = "sqlite:///./solar_wind.db"

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =====================================================================
# 2. ORM DATABASE MODELS
# =====================================================================

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="Renewable Energy Planner")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    projects = relationship("Project", back_populates="creator")

class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="Planning")  # Planning, Active, Completed
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    creator = relationship("User", back_populates="projects")
    sites = relationship("Site", back_populates="project", cascade="all, delete-orphan")

class Site(Base):
    __tablename__ = "sites"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    name = Column(String(150), nullable=False)
    lat = Column(Float, nullable=False)
    long = Column(Float, nullable=False)
    region = Column(String(100), default="Candidate Region")
    site_type = Column(String(50), default="Solar")

    # Environmental Factors + Elevation + Window Days
    solar_irradiance = Column(Float, default=5.69)
    peak_sun_hours = Column(Float, default=5.69)
    temperature_avg = Column(Float, default=29.34)
    rainfall = Column(Float, default=133.8)
    cloud_cover = Column(Float, default=70.2)
    elevation = Column(Float, default=12.0)
    days_recorded = Column(Integer, default=30)

    # 0 - 10 Overall Suitability & Yield Predictions
    suitability_score = Column(Float, default=8.6)
    suitability_category = Column(String(50), default="Excellent")
    capacity_factor = Column(Float, default=46.4)
    est_yield = Column(Float, default=1618.5)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    project = relationship("Project", back_populates="sites")

Base.metadata.create_all(bind=engine)

# =====================================================================
# 3. FASTAPI APP & CORS
# =====================================================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
app = FastAPI(title="Solar & Wind Intelligence Platform API", version="2.0.0")

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

# =====================================================================
# 4. PYDANTIC SCHEMAS
# =====================================================================

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    confirm_password: str
    role: str = "Renewable Energy Planner"

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    role: str = "Renewable Energy Planner"

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    status: Optional[str] = "Planning"

class ProjectStatusUpdate(BaseModel):
    status: str

class SiteCreate(BaseModel):
    project_id: str
    name: str
    lat: float
    long: float
    region: Optional[str] = "Selected Region"
    elevation: Optional[float] = 12.0
    site_type: Optional[str] = "Solar"

# =====================================================================
# 5. AUTHENTICATION ROUTES
# =====================================================================

@app.post("/api/auth/register")
def register(user: UserRegister, db: Session = Depends(get_db)):
    email_clean = user.email.strip().lower()
    if db.query(User).filter(User.email == email_clean).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="An account with this email address already exists. Please sign in."
        )
    if user.password != user.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Passwords do not match."
        )
    if len(user.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Password must be at least 6 characters long."
        )

    hashed = pwd_context.hash(user.password[:72])
    db_user = User(
        name=user.name.strip(), 
        email=email_clean, 
        hashed_password=hashed, 
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {
        "id": db_user.id,
        "name": db_user.name, 
        "email": db_user.email, 
        "role": db_user.role, 
        "access_token": "token"
    }

@app.post("/api/auth/login")
def login(creds: UserLogin, db: Session = Depends(get_db)):
    email_clean = creds.email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not registered. Please register first to continue."
        )
    if not pwd_context.verify(creds.password[:72], user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid password. Please verify credentials."
        )
    return {
        "id": user.id,
        "name": user.name, 
        "email": user.email, 
        "role": user.role, 
        "access_token": "token"
    }

# =====================================================================
# 6. PROJECT MANAGEMENT ROUTES
# =====================================================================

@app.get("/api/projects")
def get_projects(db: Session = Depends(get_db)):
    return db.query(Project).order_by(Project.created_at.desc()).all()

@app.post("/api/projects")
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    default_user = db.query(User).first()
    creator_id = default_user.id if default_user else None

    proj = Project(
        name=data.name.strip(), 
        description=data.description.strip() if data.description else "", 
        status=data.status if data.status in ["Planning", "Active", "Completed"] else "Planning",
        created_by=creator_id
    )
    db.add(proj)
    db.commit()
    db.refresh(proj)
    return proj

@app.patch("/api/projects/{project_id}/status")
def update_project_status(project_id: str, payload: ProjectStatusUpdate, db: Session = Depends(get_db)):
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    if payload.status not in ["Planning", "Active", "Completed"]:
        raise HTTPException(status_code=400, detail="Invalid status option")
    
    proj.status = payload.status
    db.commit()
    db.refresh(proj)
    return proj

@app.delete("/api/projects/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db)):
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(proj)
    db.commit()
    return {"message": "Project deleted successfully", "id": project_id}

# =====================================================================
# 7. SITE MANAGEMENT ROUTES (LIVE HARVESTING + SCORING + ML INFERENCE)
# =====================================================================

@app.get("/api/sites")
def get_sites(project_id: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Site)
    if project_id:
        q = q.filter(Site.project_id == project_id)
    return q.order_by(Site.created_at.desc()).all()

@app.post("/api/sites")
def create_site(data: SiteCreate, db: Session = Depends(get_db)):
    """
    Creates a candidate site under the active project, fetches live 30-day 
    environmental telemetry from Open-Meteo, calculates suitability score,
    and runs XGBoost inference for energy yield prediction.
    """
    proj = db.query(Project).filter(Project.id == data.project_id).first()
    if not proj:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Parent project does not exist. Create a project first."
        )

    # 1. Fetch real-time environmental metrics for candidate coordinates
    env_factors = fetch_realtime_environmental_factors(
        lat=data.lat, 
        lon=data.long, 
        days=30
    )

    # 2. Calculate suitability and run solar XGBoost model inference
    scoring_data = compute_site_suitability(env_factors)

    # 3. Create and persist the complete record in the database
    site = Site(
        project_id=data.project_id,
        name=data.name.strip(),
        lat=data.lat,
        long=data.long,
        region=data.region or "Selected Corridor",
        site_type=data.site_type or "Solar",
        solar_irradiance=env_factors.get("solar_irradiance", 5.69),
        peak_sun_hours=env_factors.get("peak_sun_hours", 5.69),
        temperature_avg=env_factors.get("temperature_avg", 29.34),
        rainfall=env_factors.get("total_rainfall", 133.8),
        cloud_cover=env_factors.get("cloud_cover", 70.2),
        elevation=env_factors.get("elevation", data.elevation or 12.0),
        days_recorded=env_factors.get("days_recorded", 30),
        suitability_score=scoring_data.get("suitability_score", 8.6),
        suitability_category=scoring_data.get("suitability_category", "Excellent"),
        capacity_factor=scoring_data.get("capacity_factor", 46.4),
        est_yield=scoring_data.get("est_yield", 1618.5)
    )

    db.add(site)
    db.commit()
    db.refresh(site)

    return site

@app.delete("/api/sites/{site_id}")
def delete_site(site_id: str, db: Session = Depends(get_db)):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    db.delete(site)
    db.commit()
    return {"message": "Site deleted successfully", "id": site_id}

# =====================================================================
# 8. SERVER ENTRY POINT
# =====================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)