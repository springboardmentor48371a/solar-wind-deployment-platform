from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any

# ----------------- JWT & Auth Schemas -----------------

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    user_id: UUID
    full_name: str

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[UUID] = None
    role: Optional[str] = None

# ----------------- Role Schemas -----------------

class RoleBase(BaseModel):
    role_name: str
    description: Optional[str] = None

class RoleResponse(RoleBase):
    role_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

# ----------------- User Schemas -----------------

class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    phone_number: Optional[str] = None
    organization: Optional[str] = None
    role_name: str = Field("Planner") # Planner, GIS Analyst, Project Manager, Admin

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    user_id: UUID
    full_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    organization: Optional[str] = None
    role_id: UUID
    role: Optional[RoleBase] = None
    account_status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ----------------- Project Schemas -----------------

class ProjectCreate(BaseModel):
    project_name: str = Field(..., min_length=2, max_length=150)
    description: Optional[str] = None
    region: str = Field(..., min_length=2, max_length=100) # Region, e.g. "Gujarat"

class ProjectResponse(BaseModel):
    project_id: UUID
    project_name: str
    description: Optional[str] = None
    region: str
    project_status: str
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ----------------- Environmental Data Schemas -----------------

class EnvironmentalDataCreate(BaseModel):
    solar_irradiance: float # kWh/m²/day
    wind_speed: float # m/s
    wind_direction: float # Degrees
    temperature: float # °C
    rainfall: float # mm
    humidity: float # %
    cloud_cover: float # %
    terrain_slope: float # Degrees
    vegetation_index: float # NDVI
    nearest_substation_distance: float # km
    road_distance: float # km
    protected_area: bool

class EnvironmentalDataResponse(EnvironmentalDataCreate):
    environment_id: UUID
    site_id: UUID
    collected_at: datetime

    class Config:
        from_attributes = True

# ----------------- Site Assessment Schemas -----------------

class SiteAssessmentResponse(BaseModel):
    assessment_id: UUID
    site_id: UUID
    solar_energy_prediction: float
    wind_energy_prediction: float
    solar_capacity_factor: float
    wind_capacity_factor: float
    suitability_score: float
    suitability_category: str # Excellent / High / Moderate / Low / Unsuitable
    energy_forecast: float
    revenue_estimate: float
    deployment_type: str # Solar / Wind / Hybrid
    recommendation: Optional[str] = None
    analysis_status: str
    analyzed_at: datetime
    is_synthetic: bool = True # Demo indicator

    class Config:
        from_attributes = True

# ----------------- Site Schemas -----------------

class SiteCreate(BaseModel):
    project_id: UUID
    site_name: str = Field(..., min_length=2, max_length=150)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    land_area: float # Area in Acres/Hectares
    land_type: Optional[str] = "Plain" # Desert / Agriculture / Plain etc.
    ownership: Optional[str] = "Government" # Private / Government
    
    # Optional manual environmental override values.
    # If not provided, backend will auto-generate/extract them using GIS
    environmental_data: Optional[EnvironmentalDataCreate] = None

class SiteResponse(BaseModel):
    site_id: UUID
    project_id: UUID
    site_name: str
    latitude: float
    longitude: float
    region: str
    land_area: float
    elevation: float
    land_type: Optional[str]
    ownership: Optional[str]
    created_at: datetime
    environmental_data: Optional[EnvironmentalDataResponse] = None
    assessments: List[SiteAssessmentResponse] = []

    class Config:
        from_attributes = True

# ----------------- Weights Overrides Schema -----------------

class RecalculateWeightsRequest(BaseModel):
    weight_resource: float = Field(0.35, ge=0.0, le=1.0)
    weight_geographic: float = Field(0.25, ge=0.0, le=1.0)
    weight_infrastructure: float = Field(0.15, ge=0.0, le=1.0)
    weight_environment: float = Field(0.15, ge=0.0, le=1.0)
    weight_economic: float = Field(0.10, ge=0.0, le=1.0)

# ----------------- Report Schemas -----------------

class ReportCreate(BaseModel):
    project_id: UUID
    report_type: str # Site Report / Investment Report

class ReportResponse(BaseModel):
    report_id: UUID
    project_id: UUID
    report_type: str
    generated_by: UUID
    report_url: str
    generated_at: datetime

    class Config:
        from_attributes = True

# ----------------- Notification Schemas -----------------

class NotificationResponse(BaseModel):
    notification_id: UUID
    user_id: UUID
    title: str
    message: str
    notification_type: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
