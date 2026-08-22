from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class SiteCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, example="Kurnool Solar Site")
    latitude: float = Field(..., ge=-90.0, le=90.0, example=15.8281)
    longitude: float = Field(..., ge=-180.0, le=180.0, example=78.0373)
    region: str = Field(..., min_length=2, max_length=100, example="Andhra Pradesh")
    land_area: float = Field(..., gt=0.0, example=50000.0) # in square meters
    land_ownership: str = Field(..., min_length=2, max_length=100, example="Government Lease")

class SiteResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    latitude: float
    longitude: float
    region: str
    land_area: float
    land_ownership: str

    # Predictions
    predicted_irradiance: float
    predicted_wind_speed: float
    predicted_temp: float
    predicted_cloud_cover: float
    predicted_elevation: float
    predicted_slope: float

    # Suitability Scores
    resource_score: float
    geographic_score: float
    infrastructure_score: float
    environmental_score: float
    economic_score: float
    overall_score: float
    suitability_class: str
    created_at: datetime

    class Config:
        from_attributes = True
