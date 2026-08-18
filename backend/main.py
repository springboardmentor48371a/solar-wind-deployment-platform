import uuid
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from passlib.context import CryptContext
from passlib.exc import UnknownHashError
from sqlalchemy.orm import Session

try:
    from .database import engine, Base, SessionLocal, ensure_user_columns, ensure_default_roles
    from . import models
    from .schemas import (
        UserCreate,
        UserLogin,
        ProjectCreate,
        SiteCreate,
        EnvironmentalDataCreate,
        SiteAssessmentCreate,
        ReportCreate,
        NotificationCreate,
        NotificationReadUpdate,
    )
except ImportError:
    from database import engine, Base, SessionLocal, ensure_user_columns, ensure_default_roles
    import models
    from schemas import (
        UserCreate,
        UserLogin,
        ProjectCreate,
        SiteCreate,
        EnvironmentalDataCreate,
        SiteAssessmentCreate,
        ReportCreate,
        NotificationCreate,
        NotificationReadUpdate,
    )

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
Base.metadata.create_all(bind=engine)
ensure_user_columns()
ensure_default_roles()

# Password hashing
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

SECRET_KEY = "solarwind-secret-key-change-later"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
security = HTTPBearer()


# Database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("user_id")

        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

        return user_id

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

@app.get("/")
def home():
    return {"message": "SolarWind Platform Backend is running!"}


@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):

    # Check whether email already exists
    existing_user = db.query(models.User).filter(
        models.User.email == user.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Hash password
    hashed_password = pwd_context.hash(user.password)

    # Create user
    selected_role = user.role if user.role in {
        "Renewable Energy Planner",
        "GIS Analyst",
        "Project Manager",
        "Administrator"
    } else "Renewable Energy Planner"

    role_row = db.query(models.Role).filter(
        models.Role.role_name == selected_role
    ).first()

    new_user = models.User(
        full_name=user.full_name,
        email=user.email,
        password_hash=hashed_password,
        phone_number=user.phone_number,
        role=selected_role,
        role_id=role_row.role_id if role_row else None,
    )

    # Save user
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "user_id": str(new_user.user_id),
        "email": new_user.email
    }

@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):

    # Find user by email
    existing_user = db.query(models.User).filter(
        models.User.email == user.email
    ).first()

    if not existing_user:
        raise HTTPException(
            status_code=401,
            detail="This email is not registered. Please create an account first."
        )

    # Verify password. Some older rows may still contain plaintext passwords;
    # allow a one-time upgrade to a proper hash after successful comparison.
    password_correct = False
    stored_password = existing_user.password_hash or ""

    try:
        password_correct = pwd_context.verify(
            user.password,
            stored_password
        )
    except UnknownHashError:
        if stored_password == user.password:
            existing_user.password_hash = pwd_context.hash(user.password)
            db.add(existing_user)
            db.commit()
            password_correct = True

    if not password_correct:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Create JWT token
    token_data = {
        "user_id": str(existing_user.user_id),
        "email": existing_user.email,
        "role": existing_user.role
    }

    access_token = jwt.encode(
        token_data,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer"
    }


@app.post("/projects")
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    new_project = models.Project(
        project_name=project.project_name,
        description=project.description,
        region=project.region,
        created_by=current_user
    )

    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    return {
        "message": "Project created successfully",
        "project_id": str(new_project.project_id),
        "project_name": new_project.project_name,
        "region": new_project.region
    }


def get_owned_project(project_id: str, current_user: str, db: Session):
    try:
        project_uuid = uuid.UUID(project_id)
        user_uuid = uuid.UUID(current_user)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project or user ID")

    project = db.query(models.Project).filter(
        models.Project.project_id == project_uuid,
        models.Project.created_by == user_uuid
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project


def get_owned_site(site_id: str, current_user: str, db: Session):
    try:
        site_uuid = uuid.UUID(site_id)
        user_uuid = uuid.UUID(current_user)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid site or user ID")

    site = db.query(models.Site).join(
        models.Project,
        models.Site.project_id == models.Project.project_id
    ).filter(
        models.Site.site_id == site_uuid,
        models.Project.created_by == user_uuid
    ).first()

    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    return site


@app.get("/projects")
def list_projects(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    try:
        user_uuid = uuid.UUID(current_user)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid user")

    projects = db.query(models.Project).filter(
        models.Project.created_by == user_uuid
    ).order_by(models.Project.created_at.desc()).all()

    return {
        "projects": [
            {
                "project_id": str(project.project_id),
                "project_name": project.project_name,
                "region": project.region,
                "project_status": project.project_status,
            }
            for project in projects
        ]
    }


@app.get("/projects/{project_id}/sites")
def list_sites(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    project = get_owned_project(project_id, current_user, db)
    sites = db.query(models.Site).filter(
        models.Site.project_id == project.project_id
    ).order_by(models.Site.created_at.desc()).all()

    return {
        "sites": [
            {
                "site_id": str(site.site_id),
                "site_name": site.site_name,
                "latitude": site.latitude,
                "longitude": site.longitude,
                "area_acres": site.area_acres,
                "elevation": site.elevation,
                "existing_infrastructure": site.existing_infrastructure,
                "land_ownership": site.land_ownership,
                "address": site.address,
                "site_status": site.site_status,
                "notes": site.notes,
            }
            for site in sites
        ]
    }


@app.post("/sites")
def create_site(
    site: SiteCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    project = get_owned_project(site.project_id, current_user, db)
    new_site = models.Site(
        project_id=project.project_id,
        site_name=site.site_name,
        latitude=site.latitude,
        longitude=site.longitude,
        area_acres=site.area_acres,
        elevation=site.elevation,
        existing_infrastructure=site.existing_infrastructure,
        land_ownership=site.land_ownership,
        address=site.address,
        site_status=site.site_status,
        notes=site.notes,
    )

    db.add(new_site)
    db.commit()
    db.refresh(new_site)

    return {
        "message": "Site created successfully",
        "site_id": str(new_site.site_id),
        "site_name": new_site.site_name,
    }


@app.delete("/sites/{site_id}")
def delete_site(
    site_id: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    try:
        site_uuid = uuid.UUID(site_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid site ID")

    site = db.query(models.Site).filter(models.Site.site_id == site_uuid).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    get_owned_project(str(site.project_id), current_user, db)
    db.delete(site)
    db.commit()

    return {"message": "Site deleted successfully"}


@app.post("/sites/{site_id}/environmental-data")
def create_environmental_data(
    site_id: str,
    payload: EnvironmentalDataCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    site = get_owned_site(site_id, current_user, db)
    record = models.EnvironmentalData(
        site_id=site.site_id,
        solar_irradiance=payload.solar_irradiance,
        wind_speed=payload.wind_speed,
        wind_direction=payload.wind_direction,
        temperature=payload.temperature,
        rainfall=payload.rainfall,
        humidity=payload.humidity,
        cloud_cover=payload.cloud_cover,
        terrain_slope=payload.terrain_slope,
        vegetation_index=payload.vegetation_index,
        nearest_substation_distance=payload.nearest_substation_distance,
        road_distance=payload.road_distance,
        protected_area=payload.protected_area,
        collected_at=payload.collected_at or datetime.utcnow(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "message": "Environmental data saved",
        "environment_id": str(record.environment_id),
        "site_id": str(record.site_id),
    }


@app.get("/sites/{site_id}/environmental-data")
def list_environmental_data(
    site_id: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    site = get_owned_site(site_id, current_user, db)
    rows = db.query(models.EnvironmentalData).filter(
        models.EnvironmentalData.site_id == site.site_id
    ).order_by(models.EnvironmentalData.collected_at.desc()).all()

    return {
        "environmental_data": [
            {
                "environment_id": str(row.environment_id),
                "site_id": str(row.site_id),
                "solar_irradiance": row.solar_irradiance,
                "wind_speed": row.wind_speed,
                "wind_direction": row.wind_direction,
                "temperature": row.temperature,
                "rainfall": row.rainfall,
                "humidity": row.humidity,
                "cloud_cover": row.cloud_cover,
                "terrain_slope": row.terrain_slope,
                "vegetation_index": row.vegetation_index,
                "nearest_substation_distance": row.nearest_substation_distance,
                "road_distance": row.road_distance,
                "protected_area": row.protected_area,
                "collected_at": row.collected_at,
            }
            for row in rows
        ]
    }


@app.post("/sites/{site_id}/assessments")
def create_site_assessment(
    site_id: str,
    payload: SiteAssessmentCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    site = get_owned_site(site_id, current_user, db)
    assessment = models.SiteAssessment(
        site_id=site.site_id,
        solar_energy_prediction=payload.solar_energy_prediction,
        wind_energy_prediction=payload.wind_energy_prediction,
        solar_capacity_factor=payload.solar_capacity_factor,
        wind_capacity_factor=payload.wind_capacity_factor,
        suitability_score=payload.suitability_score,
        suitability_category=payload.suitability_category,
        energy_forecast=payload.energy_forecast,
        revenue_estimate=payload.revenue_estimate,
        deployment_type=payload.deployment_type,
        recommendation=payload.recommendation,
        analysis_status=payload.analysis_status,
        analyzed_at=payload.analyzed_at,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    return {
        "message": "Site assessment saved",
        "assessment_id": str(assessment.assessment_id),
        "site_id": str(assessment.site_id),
    }


@app.get("/sites/{site_id}/assessments")
def list_site_assessments(
    site_id: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    site = get_owned_site(site_id, current_user, db)
    rows = db.query(models.SiteAssessment).filter(
        models.SiteAssessment.site_id == site.site_id
    ).order_by(models.SiteAssessment.analyzed_at.desc().nullslast()).all()

    return {
        "assessments": [
            {
                "assessment_id": str(row.assessment_id),
                "site_id": str(row.site_id),
                "solar_energy_prediction": row.solar_energy_prediction,
                "wind_energy_prediction": row.wind_energy_prediction,
                "solar_capacity_factor": row.solar_capacity_factor,
                "wind_capacity_factor": row.wind_capacity_factor,
                "suitability_score": row.suitability_score,
                "suitability_category": row.suitability_category,
                "energy_forecast": row.energy_forecast,
                "revenue_estimate": row.revenue_estimate,
                "deployment_type": row.deployment_type,
                "recommendation": row.recommendation,
                "analysis_status": row.analysis_status,
                "analyzed_at": row.analyzed_at,
            }
            for row in rows
        ]
    }


@app.post("/projects/{project_id}/reports")
def create_report(
    project_id: str,
    payload: ReportCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    project = get_owned_project(project_id, current_user, db)
    try:
        user_uuid = uuid.UUID(current_user)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid user")

    report = models.Report(
        project_id=project.project_id,
        report_type=payload.report_type,
        generated_by=user_uuid,
        report_url=payload.report_url,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return {
        "message": "Report created",
        "report_id": str(report.report_id),
        "project_id": str(report.project_id),
    }


@app.get("/projects/{project_id}/reports")
def list_reports(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    project = get_owned_project(project_id, current_user, db)
    rows = db.query(models.Report).filter(
        models.Report.project_id == project.project_id
    ).order_by(models.Report.generated_at.desc()).all()

    return {
        "reports": [
            {
                "report_id": str(row.report_id),
                "project_id": str(row.project_id),
                "report_type": row.report_type,
                "generated_by": str(row.generated_by),
                "report_url": row.report_url,
                "generated_at": row.generated_at,
            }
            for row in rows
        ]
    }


@app.post("/notifications")
def create_notification(
    payload: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    try:
        user_uuid = uuid.UUID(current_user)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid user")

    notification = models.Notification(
        user_id=user_uuid,
        title=payload.title,
        message=payload.message,
        notification_type=payload.notification_type,
        is_read=False,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)

    return {
        "message": "Notification created",
        "notification_id": str(notification.notification_id),
    }


@app.get("/notifications")
def list_notifications(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    try:
        user_uuid = uuid.UUID(current_user)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid user")

    rows = db.query(models.Notification).filter(
        models.Notification.user_id == user_uuid
    ).order_by(models.Notification.created_at.desc()).all()

    return {
        "notifications": [
            {
                "notification_id": str(row.notification_id),
                "user_id": str(row.user_id),
                "title": row.title,
                "message": row.message,
                "notification_type": row.notification_type,
                "is_read": row.is_read,
                "created_at": row.created_at,
            }
            for row in rows
        ]
    }


@app.patch("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: str,
    payload: NotificationReadUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    try:
        notification_uuid = uuid.UUID(notification_id)
        user_uuid = uuid.UUID(current_user)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid notification or user ID")

    row = db.query(models.Notification).filter(
        models.Notification.notification_id == notification_uuid,
        models.Notification.user_id == user_uuid
    ).first()

    if not row:
        raise HTTPException(status_code=404, detail="Notification not found")

    row.is_read = payload.is_read
    db.add(row)
    db.commit()

    return {
        "message": "Notification updated",
        "notification_id": str(row.notification_id),
        "is_read": row.is_read,
    }
