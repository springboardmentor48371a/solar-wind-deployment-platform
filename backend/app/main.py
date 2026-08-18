from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import auth, environmental_data, projects, sites

settings = get_settings()

app = FastAPI(
    title="Solar & Wind Deployment Intelligence API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(sites.router)
app.include_router(environmental_data.router)


@app.get("/")
def read_root():
    return {"message": "Solar & Wind Deployment Intelligence API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
