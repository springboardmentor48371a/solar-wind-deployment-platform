from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum

class UserRole(str, Enum):
    PLANNER = "Renewable Energy Planner"
    GIS_ANALYST = "GIS Analyst"
    PROJECT_MANAGER = "Project Manager"
    ADMIN = "Administrator"

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: UserRole
    organization: Optional[str] = "National Renewable Energy Grid"
    department: Optional[str] = "Geospatial Planning Division"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    organization: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    organization: str
    department: str
    phone: Optional[str] = None
    bio: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse