from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    confirm_password: str
    role: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    role: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str

    class Config:
        from_attributes = True

class SiteCreate(BaseModel):
    name: str
    region: str
    lat: float
    long: float
    site_type: Optional[str] = "Hybrid (Solar + Wind)"
    area: Optional[str] = "25.0 km²"
    solar_potential: Optional[str] = "5.5 kWh/m²/day"
    wind_speed: Optional[str] = "6.5 m/s"
    grid_proximity: Optional[str] = "2.0 km"
    elevation: Optional[str] = "300 m"
    suitability_score: Optional[int] = 90

class SiteResponse(SiteCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class SitePreview(BaseModel):
    name: str
    region: str
    elevation: str
    lat: float
    long: float