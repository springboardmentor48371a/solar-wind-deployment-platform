from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class EnvironmentalDataResponse(BaseModel):
    id: int
    site_id: int
    date: date
    solar_irradiance: Optional[float]
    peak_sun_hours: Optional[float]
    wind_speed: Optional[float]
    wind_speed_50m: Optional[float]
    wind_direction: Optional[float]
    temperature_max: Optional[float]
    temperature_min: Optional[float]
    temperature_avg: Optional[float]
    rainfall: Optional[float]
    cloud_cover: Optional[float]
    humidity: Optional[float]
    elevation: Optional[float]
    land_slope: Optional[float]
    vegetation_index: Optional[float]
    source: Optional[str]
    fetched_at: datetime

    model_config = {"from_attributes": True}

class EnvironmentalSummary(BaseModel):
    site_id: int
    total_days: int
    avg_solar_irradiance: Optional[float]
    avg_peak_sun_hours: Optional[float]
    avg_wind_speed: Optional[float]
    avg_wind_speed_50m: Optional[float]
    avg_temperature: Optional[float]
    total_rainfall: Optional[float]
    avg_cloud_cover: Optional[float]
    avg_humidity: Optional[float]
    elevation: Optional[float]
