"""
Solar & Wind Deployment Intelligence Platform — API entrypoint.

Run locally:
    pip install -r requirements.txt
    uvicorn app.main:app --reload --port 8000

Docs: http://localhost:8000/docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base
from .routers import auth, projects, sites, reports

Base.metadata.create_all(bind=engine)

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
app.include_router(reports.router)


@app.get("/api/health", tags=["System"])
def health_check():
    return {"status": "ok", "service": "solar-wind-deployment-intelligence"}
