from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional

class SiteBase(BaseModel):
    site_name: str = Field(..., min_length=1, max_length=255)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    region: Optional[str] = None
    land_area: Optional[float] = Field(None, ge=0)
    elevation: Optional[float] = Field(None, ge=-500)
    land_ownership: Optional[str] = None
    existing_infrastructure: Optional[str] = None

class SiteCreate(SiteBase):
    project_id: int

class SiteUpdate(BaseModel):
    site_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    region: Optional[str] = None
    land_area: Optional[float] = None
    elevation: Optional[float] = None
    land_ownership: Optional[str] = None
    existing_infrastructure: Optional[str] = None

class SiteResponse(SiteBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True