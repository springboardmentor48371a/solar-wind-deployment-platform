from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.database import engine, Base
from .routers import auth, users, projects, sites, environmental, solar, wind, suitability

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Solar & Wind Deployment Intelligence Platform",
    description="AI-powered renewable energy site selection platform",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Solar & Wind Deployment Intelligence Platform API", "version": "1.0.0"}

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(sites.router, prefix="/api/sites", tags=["Sites"])
app.include_router(environmental.router, prefix="/api/environmental", tags=["Environmental"])
app.include_router(solar.router, prefix="/api/solar", tags=["Solar"])
app.include_router(wind.router, prefix="/api/wind", tags=["Wind"])
app.include_router(suitability.router, prefix="/api/suitability", tags=["Suitability"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)