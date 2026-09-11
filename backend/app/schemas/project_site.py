from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class SiteCreate(BaseModel):
    project_id: int
    site_name: str
    latitude: float
    longitude: float
    elevation_m: float
    land_area_sqkm: float
    region: str
    land_ownership: Optional[str] = "Government Lease"
    existing_infrastructure: Optional[str] = "400kV line within 5km"

class SiteGisUpdate(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    elevation_m: Optional[float] = None
    slope_deg: Optional[float] = None
    vegetation_ndvi: Optional[float] = None
    solar_ghi: Optional[float] = None
    avg_temp: Optional[float] = None

class SiteApprovalUpdate(BaseModel):
    is_shortlisted: Optional[bool] = None
    is_approved: bool
    approval_notes: Optional[str] = None

class SiteResponse(BaseModel):
    id: int
    project_id: int
    site_name: str
    latitude: float
    longitude: float
    elevation_m: float
    land_area_sqkm: float
    region: str
    solar_ghi: float
    avg_temp: float
    rainfall_mm: float
    cloud_cover_pct: float
    slope_deg: float
    vegetation_ndvi: float
    suitability_score: float
    capacity_factor: float
    est_yield_gwh: float
    lcoe_usd_mwh: float
    is_shortlisted: bool
    is_approved: bool
    approval_notes: Optional[str] = None
    land_ownership: str
    existing_infrastructure: str
    created_at: datetime

    class Config:
        from_attributes = True

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    target_capacity_mw: float
    region: str
    status: Optional[str] = "Planning"
    timeline_cod: Optional[str] = "Q4 2027"

class ProjectResponse(ProjectCreate):
    id: int
    created_at: datetime
    owner_id: int
    sites: List[SiteResponse] = []

    class Config:
        from_attributes = True