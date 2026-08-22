from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import models, schemas
from database import engine, get_db

# Create tables in SQLite
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# CRITICAL: Allow your frontend on port 5173!
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- PROJECT ENDPOINTS ---
@app.get("/api/projects")
def get_projects(db: Session = Depends(get_db)):
    return db.query(models.Project).all()

@app.post("/api/projects", status_code=201)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    db_project = models.Project(project_name=project.project_name, description=project.description)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

# --- SITE ENDPOINTS ---
@app.get("/api/sites")
def get_sites(db: Session = Depends(get_db)):
    return db.query(models.Site).all()

@app.post("/api/sites", status_code=201)
def create_site(site: schemas.SiteCreate, db: Session = Depends(get_db)):
    # Auto-fill elevation if missing (Open-Meteo API, no key needed)
    if site.elevation is None or site.elevation == 0:
        import requests
        try:
            response = requests.get(f"https://api.open-meteo.com/v1/elevation?latitude={site.latitude}&longitude={site.longitude}")
            site.elevation = float(response.json()['elevation'][0])
        except:
            site.elevation = 0.0

    db_site = models.Site(
        project_id=site.project_id,
        site_name=site.site_name,
        latitude=site.latitude,
        longitude=site.longitude,
        elevation=site.elevation,
        land_area=site.land_area,
        land_ownership=site.land_ownership,
        existing_infrastructure=site.existing_infrastructure,
        region=site.region
    )
    db.add(db_site)
    db.commit()
    db.refresh(db_site)
    return db_site