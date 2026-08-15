from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str

from pydantic import BaseModel


class SolarAnalysisRequest(BaseModel):
    location: str
    land_area: float
    irradiance: float
    temperature: float
    cloud_cover: float