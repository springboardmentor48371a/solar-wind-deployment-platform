from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from ..models.project import TechnologyType, ProjectStatus

class ProjectBase(BaseModel):
    project_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    technology: TechnologyType
    budget: Optional[float] = 0.0

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    description: Optional[str] = None
    technology: Optional[TechnologyType] = None
    budget: Optional[float] = None
    status: Optional[ProjectStatus] = None

class ProjectResponse(ProjectBase):
    id: int
    status: ProjectStatus
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True