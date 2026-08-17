"""Pydantic request/response schemas."""
import datetime as dt
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict
from .models import RoleEnum, SiteTypeEnum, SuitabilityCategory


# ---------- Auth / Users ----------
class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: RoleEnum = RoleEnum.planner
    organization: Optional[str] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    email: EmailStr
    role: RoleEnum
    organization: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ---------- Projects ----------
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    objective: Optional[str] = None
    region: Optional[str] = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: Optional[str]
    objective: Optional[str]
    region: Optional[str]
    created_at: dt.datetime
    site_count: int = 0


# ---------- Sites ----------
class SiteCreate(BaseModel):
    name: str
    latitude: float
    longitude: float
    region: Optional[str] = None
    land_area_hectares: Optional[float] = None
    elevation_m: Optional[float] = None
    existing_infrastructure: Optional[str] = None
    land_ownership: Optional[str] = None
    site_type: SiteTypeEnum = SiteTypeEnum.hybrid


class SiteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_id: int
    name: str
    latitude: float
    longitude: float
    region: Optional[str]
    land_area_hectares: Optional[float]
    elevation_m: Optional[float]
    site_type: SiteTypeEnum
    created_at: dt.datetime


# ---------- Environmental ----------
class EnvironmentalDataOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    solar_irradiance_kwh_m2_day: float
    wind_speed_avg_ms: float
    wind_direction_deg: float
    temperature_avg_c: float
    rainfall_mm_year: float
    cloud_cover_pct: float
    land_slope_pct: float
    vegetation_index_ndvi: float
    distance_to_road_km: float
    distance_to_transmission_km: float
    distance_to_substation_km: float
    distance_to_urban_km: float
    distance_to_water_km: float
    in_protected_zone: bool


# ---------- Solar / Wind ----------
class SolarPredictionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    annual_irradiance_kwh_m2: float
    peak_sun_hours: float
    panel_efficiency_pct: float
    performance_ratio: float
    capacity_factor_pct: float
    expected_energy_output_mwh_year: float
    shading_loss_pct: float


class WindPredictionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    avg_wind_speed_ms: float
    wind_power_density_w_m2: float
    turbulence_intensity_pct: float
    turbine_suitability: str
    capacity_factor_pct: float
    expected_annual_energy_mwh: float


# ---------- Scoring ----------
class SiteScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    resource_score: float
    geographic_score: float
    infrastructure_score: float
    environmental_score: float
    economic_score: float
    overall_score: float
    category: SuitabilityCategory
    recommended_technology: SiteTypeEnum


# ---------- Forecast ----------
class EnergyForecastOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    year1_mwh: float
    year5_mwh: float
    year10_mwh: float
    year25_mwh: float
    estimated_capex_usd: float
    estimated_annual_revenue_usd: float
    payback_period_years: float


# ---------- Composite site detail ----------
class SiteDetailOut(BaseModel):
    site: SiteOut
    environmental: Optional[EnvironmentalDataOut] = None
    solar: Optional[SolarPredictionOut] = None
    wind: Optional[WindPredictionOut] = None
    score: Optional[SiteScoreOut] = None
    forecast: Optional[EnergyForecastOut] = None


class RankedSite(BaseModel):
    site_id: int
    site_name: str
    overall_score: float
    category: SuitabilityCategory
    recommended_technology: SiteTypeEnum
