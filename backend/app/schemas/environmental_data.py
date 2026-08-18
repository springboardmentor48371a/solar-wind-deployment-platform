import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class EnvironmentalDataBase(BaseModel):
    solar_irradiance: float | None = Field(default=None, ge=0)
    wind_speed: float | None = Field(default=None, ge=0)
    wind_direction: float | None = Field(default=None, ge=0, le=360)
    temperature: float | None = None
    rainfall: float | None = None
    humidity: float | None = Field(default=None, ge=0, le=100)
    cloud_cover: float | None = Field(default=None, ge=0, le=100)
    terrain_slope: float | None = Field(default=None, ge=0)
    vegetation_index: float | None = Field(default=None, ge=-1, le=1)
    nearest_substation_distance: float | None = Field(default=None, ge=0)
    road_distance: float | None = Field(default=None, ge=0)
    protected_area: bool | None = None
    collected_at: datetime | None = None


class EnvironmentalDataCreate(EnvironmentalDataBase):
    pass


class EnvironmentalDataResponse(EnvironmentalDataBase):
    environment_id: uuid.UUID
    site_id: uuid.UUID
    collected_at: datetime


class EnvironmentalDataCollectResponse(EnvironmentalDataResponse):
    data_sources: dict[str, str]
