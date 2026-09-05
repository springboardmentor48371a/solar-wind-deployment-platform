from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date

class PredictRequest(BaseModel):
    site_id: int
    latitude: float
    longitude: float
    elevation: Optional[float] = None
    energy_type: str
    land_ownership: Optional[str] = None
    slope_deg: Optional[float] = None
    aspect_deg: Optional[float] = None
    infrastructure_score: Optional[float] = None

class SitePredictionResponse(BaseModel):
    site_id: int
    solar_yield_kwh: Optional[float]
    solar_capacity_factor: Optional[float]
    solar_score: Optional[float]
    wind_power_kw: Optional[float]
    wind_capacity_factor: Optional[float]
    wind_score: Optional[float]
    land_cover_class: Optional[str]
    vegetation_index: Optional[float]
    land_slope: Optional[float]
    land_cover_score: Optional[float]
    suitability_score: Optional[float]
    suitability_category: Optional[str]
    resource_score: Optional[float]
    geographic_score: Optional[float]
    infrastructure_score: Optional[float]
    environmental_score: Optional[float]
    economic_score: Optional[float]
    predicted_at: Optional[datetime]
    model_config = {"from_attributes": True}

class EnergyForecastResponse(BaseModel):
    site_id: int
    forecast_date: date
    predicted_solar_kwh: Optional[float]
    predicted_wind_kwh: Optional[float]
    predicted_total_kwh: Optional[float]
    confidence: Optional[float]
    model_config = {"from_attributes": True}

class LandCoverResponse(BaseModel):
    site_id: int
    cover_class: Optional[str]
    vegetation_pct: Optional[float]
    urban_pct: Optional[float]
    water_pct: Optional[float]
    barren_pct: Optional[float]
    ndvi: Optional[float]
    slope_deg: Optional[float]
    aspect_deg: Optional[float]
    model_config = {"from_attributes": True}
