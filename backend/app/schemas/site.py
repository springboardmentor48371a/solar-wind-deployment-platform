import uuid

from pydantic import BaseModel, Field


class SiteCreate(BaseModel):
    site_name: str = Field(..., min_length=1, max_length=150)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    region: str | None = Field(default=None, max_length=100)
    land_area: float | None = Field(default=None, ge=0)
    elevation: float | None = None
    land_type: str | None = Field(default=None, max_length=100)
    ownership: str | None = Field(default=None, max_length=100)


class SiteUpdate(BaseModel):
    site_name: str | None = Field(default=None, min_length=1, max_length=150)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    region: str | None = Field(default=None, max_length=100)
    land_area: float | None = Field(default=None, ge=0)
    elevation: float | None = None
    land_type: str | None = Field(default=None, max_length=100)
    ownership: str | None = Field(default=None, max_length=100)


class SiteResponse(BaseModel):
    site_id: uuid.UUID
    project_id: uuid.UUID
    site_name: str
    latitude: float
    longitude: float
    region: str | None
    land_area: float | None
    elevation: float | None
    land_type: str | None
    ownership: str | None
