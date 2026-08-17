from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from ..models.site import EnergyType, SiteStatus, LandOwnership

class SiteCreate(BaseModel):
    name: str
    project_id: int
    latitude: float
    longitude: float
    elevation: Optional[float] = None
    land_area: Optional[float] = None
    energy_type: EnergyType
    land_ownership: LandOwnership = LandOwnership.unknown
    existing_infrastructure: Optional[str] = None
    notes: Optional[str] = None

class SiteUpdate(BaseModel):
    name: Optional[str] = None
    elevation: Optional[float] = None
    land_area: Optional[float] = None
    land_ownership: Optional[LandOwnership] = None
    existing_infrastructure: Optional[str] = None
    notes: Optional[str] = None

class SiteStatusUpdate(BaseModel):
    status: SiteStatus
    notes: Optional[str] = None

class DeploymentHistoryResponse(BaseModel):
    id: int
    previous_status: Optional[SiteStatus]
    new_status: SiteStatus
    notes: Optional[str]
    changed_by: int
    changed_at: datetime
    model_config = {"from_attributes": True}

class SiteResponse(BaseModel):
    id: int
    name: str
    project_id: int
    latitude: float
    longitude: float
    elevation: Optional[float]
    land_area: Optional[float]
    energy_type: EnergyType
    status: SiteStatus
    land_ownership: LandOwnership
    existing_infrastructure: Optional[str]
    notes: Optional[str]
    created_by: int
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}

class SiteCompareResponse(BaseModel):
    sites: List[SiteResponse]
