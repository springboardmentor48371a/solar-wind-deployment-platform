from pydantic import BaseModel, field_validator
from typing import Optional

# --- Project Schemas ---
class ProjectCreate(BaseModel):
    project_name: str
    description: Optional[str] = None

# --- Site Schemas (Matches your frontend exactly) ---
class SiteCreate(BaseModel):
    project_id: Optional[int] = None
    site_name: str
    latitude: float
    longitude: float
    region: Optional[str] = None
    land_area: Optional[float] = None
    elevation: Optional[float] = None
    land_ownership: Optional[str] = None
    existing_infrastructure: Optional[str] = None

    # This turns empty strings into None, preventing 422 errors
    @field_validator('land_area', 'elevation', 'project_id', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        if v == "" or v is None:
            return None
        return v