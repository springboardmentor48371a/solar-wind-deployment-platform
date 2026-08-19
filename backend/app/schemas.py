import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models import RoleEnum, AlertSeverity, IntegrationTypeEnum


# ---------- Auth / Users ----------

class UserCreate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: RoleEnum = RoleEnum.planner
    # No longer required by the backend (the staff-PIN gate was removed —
    # see auth.py's register()). Left in the schema as an accepted-but-
    # ignored optional field so nothing breaks if older frontend code
    # still sends it.
    pin: Optional[str] = Field(None, max_length=32)


class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: RoleEnum
    is_active: int
    # Set only on /auth/me, only when the current session is an
    # Administrator "viewing as" this user — see auth.get_current_user.
    impersonated_by: Optional[int] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ---------- Projects ----------

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    objective: Optional[str] = Field(None, max_length=2000)
    # Legacy free-text label. Prefer region_id where the region is a
    # known, managed Region row.
    region: Optional[str] = Field(None, max_length=200)
    region_id: Optional[int] = None


class ProjectOut(BaseModel):
    id: int
    name: str
    objective: Optional[str]
    region: Optional[str]
    region_id: Optional[int]
    owner_id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# ---------- Regions ----------

class RegionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    country: Optional[str] = Field(None, max_length=100)
    admin_area: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=2000)
    min_latitude: Optional[float] = Field(None, ge=-90, le=90)
    max_latitude: Optional[float] = Field(None, ge=-90, le=90)
    min_longitude: Optional[float] = Field(None, ge=-180, le=180)
    max_longitude: Optional[float] = Field(None, ge=-180, le=180)

    @field_validator("max_latitude")
    @classmethod
    def _lat_order(cls, v, info):
        min_lat = info.data.get("min_latitude")
        if v is not None and min_lat is not None and v < min_lat:
            raise ValueError("max_latitude must be >= min_latitude")
        return v

    @field_validator("max_longitude")
    @classmethod
    def _lon_order(cls, v, info):
        min_lon = info.data.get("min_longitude")
        if v is not None and min_lon is not None and v < min_lon:
            raise ValueError("max_longitude must be >= min_longitude")
        return v


class RegionUpdate(RegionCreate):
    name: Optional[str] = Field(None, min_length=1, max_length=200)


class RegionOut(BaseModel):
    id: int
    name: str
    country: Optional[str]
    admin_area: Optional[str]
    description: Optional[str]
    min_latitude: Optional[float]
    max_latitude: Optional[float]
    min_longitude: Optional[float]
    max_longitude: Optional[float]
    created_by_id: Optional[int]
    created_at: datetime.datetime
    project_count: int = 0

    class Config:
        from_attributes = True


# ---------- Sites ----------

class SiteCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    land_area_hectares: Optional[float] = Field(None, ge=0, le=1_000_000)
    elevation_m: Optional[float] = Field(None, ge=-500, le=9000)
    land_slope_pct: Optional[float] = Field(None, ge=0, le=100)
    distance_to_substation_km: Optional[float] = Field(None, ge=0, le=10000)
    existing_infrastructure: Optional[str] = Field(None, max_length=1000)
    land_ownership: Optional[str] = Field(None, max_length=200)


class SiteOut(BaseModel):
    id: int
    project_id: int
    name: str
    latitude: float
    longitude: float
    land_area_hectares: Optional[float]
    elevation_m: Optional[float]
    land_slope_pct: Optional[float]
    distance_to_substation_km: Optional[float]
    existing_infrastructure: Optional[str]
    land_ownership: Optional[str]
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# ---------- Weather / Environmental ----------

class WeatherReadingOut(BaseModel):
    id: int
    site_id: int
    reading_date: datetime.datetime
    solar_irradiance: Optional[float]
    wind_speed: Optional[float]
    wind_speed_50m: Optional[float]
    temperature: Optional[float]
    rainfall: Optional[float]
    cloud_cover_pct: Optional[float]

    class Config:
        from_attributes = True


class SupplementalWeatherReadingOut(BaseModel):
    id: int
    site_id: int
    source: str
    fetched_at: datetime.datetime
    temperature_c: Optional[float]
    wind_speed_ms: Optional[float]
    cloud_cover_pct: Optional[float]
    condition_text: Optional[str]
    forecast_period: Optional[str]

    class Config:
        from_attributes = True


# ---------- Infrastructure ----------

class InfrastructureFeatureOut(BaseModel):
    id: int
    site_id: int
    feature_type: str
    name: Optional[str]
    distance_km: float
    fetched_at: datetime.datetime

    class Config:
        from_attributes = True


# ---------- Suitability Scoring ----------

class SuitabilityScoreOut(BaseModel):
    id: int
    site_id: int
    resource_score: float
    geographic_score: float
    infrastructure_score: float
    environmental_score: float
    economic_score: float
    overall_score: float
    category: str
    computed_at: datetime.datetime

    class Config:
        from_attributes = True


class SiteComparisonOut(BaseModel):
    site_id: int
    site_name: str
    overall_score: Optional[float]
    category: str


# ---------- Alerts ----------

class AlertOut(BaseModel):
    id: int
    site_id: Optional[int]
    project_id: Optional[int]
    title: str
    message: str
    severity: AlertSeverity
    category: str
    is_read: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class AlertCreate(BaseModel):
    site_id: Optional[int] = None
    project_id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=2000)
    severity: AlertSeverity = AlertSeverity.info
    category: str = Field(..., max_length=50)


# ---------- Data Sources ----------

class DataSourceStatusOut(BaseModel):
    name: str
    status: str  # operational / degraded / down
    latency_ms: Optional[int] = None
    detail: Optional[str] = None


# ---------- Dashboard / Analytics ----------

class DashboardSummaryOut(BaseModel):
    portfolio_capacity_note: str
    active_projects: int
    total_sites: int
    average_suitability: Optional[float]
    sites_by_category: dict
    data_freshness_pct: float


# ---------- Data Ingestion Log ----------

class IngestionEventOut(BaseModel):
    collection: str
    source: Optional[str]
    fetched_at: Optional[datetime.datetime]


class IngestionLogOut(BaseModel):
    site_id: int
    weather_readings_count: int
    infrastructure_features_count: int
    latest_weather_reading_date: Optional[datetime.datetime]
    has_postgis_geometry: bool
    raw_payload_events: List[IngestionEventOut]
    data_lake_archival_enabled: bool


# ---------- Satellite Imagery ----------

class SiteImageOut(BaseModel):
    id: int
    site_id: int
    provider: str
    scene_date: Optional[datetime.datetime]
    cloud_cover_pct: Optional[float]
    ndvi_mean: Optional[float]
    land_cover_summary: Optional[str]
    thumbnail_url: Optional[str]
    source_status: str
    fetched_at: datetime.datetime

    class Config:
        from_attributes = True


# ---------- Environmental Constraints / Demographic & Land Data ----------

class EnvironmentalConstraintOut(BaseModel):
    id: int
    site_id: int
    protected_area_distance_km: Optional[float]
    water_body_distance_km: Optional[float]
    agricultural_land_nearby: int
    urban_area_distance_km: Optional[float]
    country_iso3: Optional[str]
    population_density_km2: Optional[float]
    gdp_per_capita_usd: Optional[float]
    data_source: Optional[str]
    fetched_at: datetime.datetime

    class Config:
        from_attributes = True


# ---------- Solar / Wind Potential ----------

class SolarPotentialOut(BaseModel):
    id: int
    site_id: int
    annual_irradiance_kwh_m2: Optional[float]
    peak_sun_hours: Optional[float]
    panel_efficiency_pct: Optional[float]
    shading_loss_pct: Optional[float]
    performance_ratio_pct: Optional[float]
    expected_energy_output_mwh_yr: Optional[float]
    capacity_factor_pct: Optional[float]
    computed_at: datetime.datetime

    class Config:
        from_attributes = True


class WindPotentialOut(BaseModel):
    id: int
    site_id: int
    average_wind_speed_ms: Optional[float]
    wind_power_density_w_m2: Optional[float]
    turbulence_intensity_pct: Optional[float]
    turbine_suitability_score: Optional[float]
    turbine_class: Optional[str]
    expected_aep_mwh_yr: Optional[float]
    capacity_factor_pct: Optional[float]
    computed_at: datetime.datetime

    class Config:
        from_attributes = True


# ---------- Financial / Investment Analytics ----------

class FinancialAnalysisCreate(BaseModel):
    technology: str = Field(..., pattern="^(solar|wind|hybrid)$")
    capacity_mw: float = Field(..., gt=0)
    capex_usd: float = Field(..., ge=0)
    opex_usd_per_yr: float = Field(..., ge=0)
    discount_rate_pct: float = Field(8.0, ge=0, le=50)
    project_lifetime_yrs: int = Field(25, ge=1, le=50)
    electricity_price_usd_per_mwh: float = Field(..., ge=0)
    # Optional override — if omitted, the endpoint uses the site's latest
    # SolarPotential/WindPotential expected output scaled by capacity_mw.
    annual_energy_mwh: Optional[float] = None


class FinancialAnalysisOut(BaseModel):
    id: int
    site_id: int
    technology: str
    capacity_mw: float
    capex_usd: float
    opex_usd_per_yr: float
    discount_rate_pct: float
    project_lifetime_yrs: int
    electricity_price_usd_per_mwh: float
    annual_energy_mwh: Optional[float]
    npv_usd: Optional[float]
    irr_pct: Optional[float]
    lcoe_usd_per_mwh: Optional[float]
    payback_years: Optional[float]
    computed_at: datetime.datetime

    class Config:
        from_attributes = True


# ---------- Report Builder ----------

REPORT_SECTION_KEYS = {
    "summary", "suitability", "solar", "wind", "financial",
    "environmental", "infrastructure", "weather", "satellite",
}


class ReportTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    sections: List[str] = Field(..., min_length=1)
    is_executive_summary: bool = False

    @field_validator("sections")
    @classmethod
    def _valid_sections(cls, v):
        invalid = set(v) - REPORT_SECTION_KEYS
        if invalid:
            raise ValueError(f"Unknown report sections: {sorted(invalid)}. Valid: {sorted(REPORT_SECTION_KEYS)}")
        return v


class ReportTemplateOut(BaseModel):
    id: int
    owner_id: int
    name: str
    description: Optional[str]
    sections: List[str]
    is_executive_summary: bool
    created_at: datetime.datetime

    class Config:
        from_attributes = True

    @field_validator("sections", mode="before")
    @classmethod
    def _split_sections(cls, v):
        return v.split(",") if isinstance(v, str) else v


# ---------- Integrations ----------

class IntegrationConnectionCreate(BaseModel):
    project_id: Optional[int] = None
    integration_type: IntegrationTypeEnum
    name: str = Field(..., min_length=1, max_length=150)
    endpoint_url: str = Field(..., min_length=1, max_length=500)
    auth_header_name: Optional[str] = Field(None, max_length=100)
    auth_header_value: Optional[str] = Field(None, max_length=500)


class IntegrationConnectionOut(BaseModel):
    id: int
    project_id: Optional[int]
    integration_type: IntegrationTypeEnum
    name: str
    endpoint_url: str
    auth_header_name: Optional[str]
    is_active: int
    last_status: Optional[str]
    last_used_at: Optional[datetime.datetime]
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class TelemetryIngestIn(BaseModel):
    metric_name: str = Field(..., min_length=1, max_length=100)
    value: float
    unit: Optional[str] = Field(None, max_length=30)
    recorded_at: Optional[datetime.datetime] = None


class TelemetryReadingOut(BaseModel):
    id: int
    site_id: int
    metric_name: str
    value: float
    unit: Optional[str]
    recorded_at: datetime.datetime

    class Config:
        from_attributes = True


class SiteRollupOut(BaseModel):
    site_id: int
    project_id: int
    site_name: str
    region_name: Optional[str]
    overall_suitability_score: Optional[float]
    suitability_category: Optional[str]
    solar_expected_output_mwh_yr: Optional[float]
    solar_capacity_factor_pct: Optional[float]
    wind_expected_aep_mwh_yr: Optional[float]
    wind_capacity_factor_pct: Optional[float]
    financial_npv_usd: Optional[float]
    financial_irr_pct: Optional[float]
    financial_lcoe_usd_per_mwh: Optional[float]
    protected_area_distance_km: Optional[float]
    substation_distance_km: Optional[float]
    refreshed_at: datetime.datetime

    class Config:
        from_attributes = True


class WarehouseRefreshOut(BaseModel):
    rows_refreshed: int
    refreshed_at: datetime.datetime
    parquet_export_enabled: bool


class PowerSimulationRequest(BaseModel):
    technology: str = Field(..., pattern="^(solar|wind)$")
    capacity_mw: float = Field(..., gt=0)
    hours: int = Field(24, ge=1, le=168)


class PowerSimulationHourOut(BaseModel):
    hour: int
    output_kw: float


class PowerSimulationOut(BaseModel):
    site_id: int
    technology: str
    capacity_mw: float
    series: List[PowerSimulationHourOut]
