"""
Solar & Wind Deployment Intelligence Platform — API entrypoint.

Run locally:
    pip install -r requirements.txt
    uvicorn app.main:app --reload --port 8000

Docs: http://localhost:8000/docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base, SessionLocal
from . import models
from .auth import hash_password
from .routers import auth, projects, sites, reports, admin

Base.metadata.create_all(bind=engine)


def seed_default_users():
    db = SessionLocal()
    try:
        admin_user = db.query(models.User).filter(models.User.email == "admin@example.com").first()
        if not admin_user:
            admin_user = models.User(
                full_name="System Administrator",
                email="admin@example.com",
                hashed_password=hash_password("admin123"),
                role=models.RoleEnum.admin,
                organization="Deployment Intelligence Admin",
            )
            db.add(admin_user)
        else:
            admin_user.hashed_password = hash_password("admin123")

        planner_user = db.query(models.User).filter(models.User.email == "planner@example.com").first()
        if not planner_user:
            planner_user = models.User(
                full_name="Energy Planner",
                email="planner@example.com",
                hashed_password=hash_password("planner123"),
                role=models.RoleEnum.planner,
                organization="Renewable Corp",
            )
            db.add(planner_user)
        else:
            planner_user.hashed_password = hash_password("planner123")

        db.commit()
    except Exception as e:
        db.rollback()
    finally:
        db.close()


seed_default_users()

app = FastAPI(
    title="Solar & Wind Deployment Intelligence Platform API",
    description="AI-powered platform for identifying optimal renewable energy deployment sites.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(sites.router)
app.include_router(sites.standalone_router)
app.include_router(reports.router)
app.include_router(admin.router)


@app.get("/api/health", tags=["System"])
def health_check():
    return {"status": "ok", "service": "solar-wind-deployment-intelligence"}
