from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from ..models.project import ProjectStatus

class RegionCreate(BaseModel):
    name: str
    country: str
    state: Optional[str] = None
    description: Optional[str] = None

class RegionResponse(BaseModel):
    id: int
    name: str
    country: str
    state: Optional[str]
    description: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    region_id: int

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None

class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: ProjectStatus
    region_id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
