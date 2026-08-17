from pydantic import BaseModel, EmailStr
from typing import Optional

class RegisterIn(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "Renewable Energy Planner"

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class SiteIn(BaseModel):
    name: str
    region: Optional[str] = ""
    latitude: float
    longitude: float
    land_area: float = 1
    elevation: float = 0
    infrastructure: Optional[str] = "Unknown"

class SiteOut(SiteIn):
    id: int
    class Config:
        from_attributes = True

class Coordinates(BaseModel):
    latitude: float
    longitude: float
    land_area: float = 1
    elevation: float = 0
