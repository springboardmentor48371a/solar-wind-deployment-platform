from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import Base, engine, get_db
from models import User, Site
from schemas import RegisterIn, LoginIn, Token, SiteIn, SiteOut, Coordinates
from auth import hash_password, verify_password, create_token, current_user
from services import environmental_analysis, solar_prediction, wind_prediction, assessment

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Solar & Wind Deployment Intelligence API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Solar & Wind Deployment Intelligence API is running"}

@app.post("/auth/register", response_model=Token)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(400, "Email already registered")
    user = User(name=data.name, email=data.email, password_hash=hash_password(data.password), role=data.role)
    db.add(user); db.commit(); db.refresh(user)
    return {"access_token": create_token(user), "token_type": "bearer",
            "user": {"id": user.id, "name": user.name, "email": user.email, "role": user.role}}

@app.post("/auth/login", response_model=Token)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return {"access_token": create_token(user), "token_type": "bearer",
            "user": {"id": user.id, "name": user.name, "email": user.email, "role": user.role}}

@app.get("/sites", response_model=list[SiteOut])
def get_sites(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return db.query(Site).filter(Site.owner_id == user.id).all()

@app.post("/sites", response_model=SiteOut)
def create_site(data: SiteIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    site = Site(**data.model_dump(), owner_id=user.id)
    db.add(site); db.commit(); db.refresh(site)
    return site

@app.delete("/sites/{site_id}")
def delete_site(site_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    site = db.query(Site).filter(Site.id == site_id, Site.owner_id == user.id).first()
    if not site: raise HTTPException(404, "Site not found")
    db.delete(site); db.commit()
    return {"message": "Site deleted"}

@app.post("/environment/analyze")
def analyze_environment(data: Coordinates, user: User = Depends(current_user)):
    return environmental_analysis(data)

@app.post("/solar/predict")
def predict_solar(data: Coordinates, user: User = Depends(current_user)):
    return solar_prediction(data)

@app.post("/wind/predict")
def predict_wind(data: Coordinates, user: User = Depends(current_user)):
    return wind_prediction(data)

@app.post("/assessment")
def resource_assessment(data: Coordinates, user: User = Depends(current_user)):
    return assessment(data)
