import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import logger
from app.api import (
    auth, projects, sites, environment, solar, wind,
    suitability, forecasting, optimization, investment,
    reports, notifications, admin
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Solar & Wind Deployment Intelligence Platform backend...")
    # Trigger database check and automatic seed if empty
    try:
        from scripts.seed_database import seed_all
        seed_all()
    except Exception as e:
        logger.warning(f"Database auto-seed check encountered notice: {e}")
    yield
    logger.info("Shutting down Solar & Wind Deployment Intelligence Platform backend.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Production-grade AI platform for multi-factor renewable energy site assessment, forecasting, and deployment optimization.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers under API_V1_STR
api_v1 = settings.API_V1_STR
app.include_router(auth.router, prefix=api_v1)
app.include_router(projects.router, prefix=api_v1)
app.include_router(sites.router, prefix=api_v1)
app.include_router(environment.router, prefix=api_v1)
app.include_router(solar.router, prefix=api_v1)
app.include_router(wind.router, prefix=api_v1)
app.include_router(suitability.router, prefix=api_v1)
app.include_router(forecasting.router, prefix=api_v1)
app.include_router(optimization.router, prefix=api_v1)
app.include_router(investment.router, prefix=api_v1)
app.include_router(reports.router, prefix=api_v1)
app.include_router(notifications.router, prefix=api_v1)
app.include_router(admin.router, prefix=api_v1)


@app.get("/")
async def root():
    return {
        "platform": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs_url": "/docs",
        "api_v1": api_v1,
        "demo_mode": settings.DEMO_MODE
    }


@app.get("/health")
@app.get(f"{api_v1}/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": os.environ.get("SERVER_START_TIME", "operational")
    }
