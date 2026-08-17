from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base

# import models so SQLAlchemy registers them before create_all
from .models import user, project, site, environmental

from .routers import auth, users, projects, sites, environmental

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Solar & Wind Deployment Intelligence Platform", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(projects.region_router)
app.include_router(sites.router)
app.include_router(environmental.router)

@app.get("/health")
def health():
    return {"status": "ok"}
