from pydantic import BaseModel, EmailStr
from datetime import datetime


class GoogleAuthRequest(BaseModel):
    credential: str


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    phone_number: str | None = None
    role: str = "Renewable Energy Planner"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ProjectCreate(BaseModel):
    project_name: str
    description: str | None = None
    region: str


class SiteCreate(BaseModel):
    project_id: str
    site_name: str
    latitude: float
    longitude: float
    area_acres: float | None = None
    elevation: float | None = None
    existing_infrastructure: str | None = None
    land_ownership: str | None = None
    address: str | None = None
    site_status: str = "Draft"
    notes: str | None = None


class EnvironmentalDataCreate(BaseModel):
    solar_irradiance: float | None = None
    wind_speed: float | None = None
    wind_direction: float | None = None
    temperature: float | None = None
    rainfall: float | None = None
    humidity: float | None = None
    cloud_cover: float | None = None
    terrain_slope: float | None = None
    vegetation_index: float | None = None
    nearest_substation_distance: float | None = None
    road_distance: float | None = None
    protected_area: bool = False
    collected_at: datetime | None = None


class SiteAssessmentCreate(BaseModel):
    solar_energy_prediction: float | None = None
    wind_energy_prediction: float | None = None
    solar_capacity_factor: float | None = None
    wind_capacity_factor: float | None = None
    suitability_score: float | None = None
    suitability_category: str | None = None
    energy_forecast: float | None = None
    revenue_estimate: float | None = None
    deployment_type: str | None = None
    recommendation: str | None = None
    analysis_status: str = "Pending"
    analyzed_at: datetime | None = None


class ReportCreate(BaseModel):
    report_type: str
    report_url: str | None = None


class NotificationCreate(BaseModel):
    title: str
    message: str
    notification_type: str | None = None


class NotificationReadUpdate(BaseModel):
    is_read: bool = True
