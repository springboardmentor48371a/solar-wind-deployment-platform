from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models.user import engine, Base
import app.models.project_site
from app.api.auth import router as auth_router
from app.api.projects import router as projects_router
from app.api.environmental import router as environmental_router
from app.api.gis import router as gis_router

# Ensure all database tables exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Solar & Wind Deployment Intelligence Platform API")

# Explicit CORS configuration to guarantee all headers and preflight (OPTIONS) requests pass
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex="http://(localhost|127\\.0\\.0\\.1)(:\\d+)?",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Register all modular routers
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(environmental_router)
app.include_router(gis_router)

@app.get("/")
def health_check():
    return {"status": "online", "message": "Solar & Wind Intelligence API Gateway"}