from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
import models
from database import engine, get_db , SessionLocal

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Solar & Wind Deployment Intelligence API")

# --- AUTOMATIC ROLE SEEDER FROM PREVIOUS PROJECT ---
@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        default_roles = [
            "Renewable Energy Planner", 
            "GIS Analyst", 
            "Project Manager", 
            "Administrator"
        ]
        for role_name in default_roles:
            existing_role = db.query(models.Role).filter(models.Role.role_name == role_name).first()
            if not existing_role:
                new_role = models.Role(role_name=role_name, description=f"Default role for {role_name}")
                db.add(new_role)
        db.commit()
    finally:
        db.close()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- PYDANTIC SCHEMAS ---
class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role_name: str  

class LoginRequest(BaseModel):
    email: str
    password: str

class ProjectCreate(BaseModel):
    name: str
    description: str

class SiteCreate(BaseModel):
    name: str
    latitude: float
    longitude: float
    region: str
    land_area: float
    elevation: float
    existing_infrastructure: str = None
    land_ownership: str = None

# --- API ENDPOINTS ---

@app.post("/register/")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    role = db.query(models.Role).filter(models.Role.role_name == user.role_name).first()
    if not role:
        raise HTTPException(status_code=400, detail="Invalid role")
        
    new_user = models.User(
        full_name=user.full_name,
        email=user.email,
        password_hash=pwd_context.hash(user.password),
        role_id=role.role_id
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created", "full_name": new_user.full_name}

@app.post("/login/")
def login_user(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if not user or not pwd_context.verify(request.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")
        
    # NEW: Fetch the actual role name from the database to send to React
    role = db.query(models.Role).filter(models.Role.role_id == user.role_id).first()
    role_name = role.role_name if role else "Unknown"

    return {
        "message": "Login successful", 
        "user_id": str(user.user_id), 
        "full_name": user.full_name,
        "role": role_name  # We now pass the role to the frontend!
    }

@app.post("/projects/")
def create_project(project: ProjectCreate, user_id: str, db: Session = Depends(get_db)):
    db_project = models.Project(project_name=project.name, description=project.description, created_by=user_id)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return {"message": "Project created", "project_id": str(db_project.project_id)}

@app.post("/projects/{project_id}/sites/")
def register_site(project_id: str, site: SiteCreate, db: Session = Depends(get_db)):
    db_site = models.Site(
        project_id=project_id, 
        site_name=site.name, 
        latitude=site.latitude, 
        longitude=site.longitude,
        region=site.region, 
        land_area=site.land_area, 
        elevation=site.elevation,
        land_type=site.existing_infrastructure, 
        ownership=site.land_ownership
    )
    db.add(db_site)
    db.commit()
    return {"message": "Site registered"}

@app.get("/users/{user_id}/projects/")
def get_user_projects(user_id: str, db: Session = Depends(get_db)):
    projects = db.query(models.Project).filter(models.Project.created_by == user_id).all()
    return [{"id": str(p.project_id), "name": p.project_name, "desc": p.description, "status": p.project_status} for p in projects]

@app.get("/projects/{project_id}/sites/")
def get_project_sites(project_id: str, db: Session = Depends(get_db)):
    sites = db.query(models.Site).filter(models.Site.project_id == project_id).all()
    return [{"id": str(s.site_id), "name": s.site_name, "lat": s.latitude, "lon": s.longitude, "region": s.region, "area": s.land_area} for s in sites]

# --- ADMIN ENDPOINTS ---
@app.get("/users/")
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    user_list = []
    
    for u in users:
        # Fetch the human-readable role name for each user
        role = db.query(models.Role).filter(models.Role.role_id == u.role_id).first()
        user_list.append({
            "id": str(u.user_id),
            "name": u.full_name,
            "email": u.email,
            "role": role.role_name if role else "Unassigned",
            "status": u.account_status
        })
        
    return user_list

import random

# --- ANALYTICS ENDPOINTS ---
@app.get("/projects/{project_id}/analytics/")
def get_project_analytics(project_id: str, db: Session = Depends(get_db)):
    # In a production environment, this is where Pandas and Machine Learning 
    # models would process the environmental data. For now, we simulate the AI output.
    sites = db.query(models.Site).filter(models.Site.project_id == project_id).all()
    
    analytics_data = []
    for site in sites:
        suitability = random.uniform(60.0, 98.5)
        analytics_data.append({
            "site_name": site.site_name,
            "suitability_score": round(suitability, 1),
            "solar_forecast_mw": round(random.uniform(10, 50), 1),
            "wind_forecast_mw": round(random.uniform(5, 40), 1),
            "est_revenue_usd": round(suitability * 12500, 2)
        })
        
    return analytics_data