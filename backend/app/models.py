import enum
import datetime

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text
)
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

from app.database import Base


class RoleEnum(str, enum.Enum):
    planner = "Renewable Energy Planner"
    gis_analyst = "GIS Analyst"
    project_manager = "Project Manager"
    investor_developer = "Investor / Developer"
    government_regulator = "Government / Regulator"
    admin = "Administrator"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), nullable=False, default=RoleEnum.planner)
    is_active = Column(Integer, default=1)  # 1=active, 0=disabled
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    projects = relationship("Project", back_populates="owner")

    # Transient, not a mapped column / never written to the database.
    # Defaults every User instance (however it was loaded — a fresh
    # query, a relationship, whatever) to a real attribute instead of
    # relying on Pydantic's from_attributes to paper over a missing one.
    # auth.get_current_user overwrites this per-request from the JWT's
    # "impersonated_by" claim; every other User instance in the app just
    # keeps this default of None.
    impersonated_by = None


class Region(Base):
    """
    A real, manageable entity per PDF item "Region management" — previously
    just a free-text label on Project. Projects may still be created with
    only the legacy text field (region_id is optional) so existing data
    and any client not yet updated keep working, but the platform now has
    a proper Regions collection: bounding box for map framing, a country/
    admin-area label, and notes, all editable independent of any one
    project.
    """
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)
    country = Column(String, nullable=True)
    admin_area = Column(String, nullable=True)  # state/province, e.g. "Andhra Pradesh"
    description = Column(Text, nullable=True)

    # Bounding box, used by the frontend to frame the map when a region
    # is selected. All optional — a region can exist as a pure label
    # before anyone has pinned down its extent.
    min_latitude = Column(Float, nullable=True)
    max_latitude = Column(Float, nullable=True)
    min_longitude = Column(Float, nullable=True)
    max_longitude = Column(Float, nullable=True)

    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    projects = relationship("Project", back_populates="region_ref")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    objective = Column(Text, nullable=True)
    # Legacy free-text region label — kept for backward compatibility with
    # existing rows and any client still sending a plain string. New
    # clients should prefer region_id, which points at a real Region row.
    region = Column(String, nullable=True)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    owner = relationship("User", back_populates="projects")
    sites = relationship("Site", back_populates="project", cascade="all, delete-orphan")
    region_ref = relationship("Region", back_populates="projects")
    # Alerts and integrations can exist at project level with no site_id
    # (site_id is nullable on Alert) — without these, deleting a project
    # that has either would fail with a foreign-key violation, same bug
    # class as the missing Site-level cascades below.
    alerts = relationship("Alert", cascade="all, delete-orphan")
    integration_connections = relationship("IntegrationConnection", cascade="all, delete-orphan")


class Site(Base):
    """Maps to Site_Static_Attributes in the data flow workflow."""
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String, nullable=False)

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    # PostGIS point geometry, kept in sync with latitude/longitude on write.
    # SRID 4326 = WGS84, the standard lat/long coordinate system used by
    # every data source this platform talks to (NASA POWER, OSM, etc).
    # nullable so this model still works unmodified against the SQLite dev
    # database, which has no geometry type — GeoAlchemy2 only activates
    # this column against a real PostGIS-enabled Postgres connection.
    geom = Column(Geometry(geometry_type="POINT", srid=4326), nullable=True)

    land_area_hectares = Column(Float, nullable=True)
    elevation_m = Column(Float, nullable=True)
    land_slope_pct = Column(Float, nullable=True)
    distance_to_substation_km = Column(Float, nullable=True)
    existing_infrastructure = Column(Text, nullable=True)
    land_ownership = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    project = relationship("Project", back_populates="sites")
    weather_readings = relationship(
        "WeatherReading", back_populates="site", cascade="all, delete-orphan"
    )
    infrastructure_features = relationship(
        "InfrastructureFeature", back_populates="site", cascade="all, delete-orphan"
    )
    suitability_scores = relationship(
        "SuitabilityScore", back_populates="site", cascade="all, delete-orphan"
    )
    # These 9 were missing cascade-delete entirely — every one of them is
    # populated automatically for every registered site (the intelligence
    # pipeline creates a SolarPotential + WindPotential row on every
    # registration, for example), so in practice almost any real site
    # had at least one of these, and the database's default foreign-key
    # behavior (RESTRICT) blocked deleting the Site — and therefore
    # blocked deleting its parent Project too, surfacing as a generic
    # "Could not delete project" error with no indication of why.
    supplemental_weather_readings = relationship("SupplementalWeatherReading", back_populates="site", cascade="all, delete-orphan")
    alerts = relationship("Alert", cascade="all, delete-orphan")
    images = relationship("SiteImage", back_populates="site", cascade="all, delete-orphan")
    environmental_constraints = relationship("EnvironmentalConstraint", back_populates="site", cascade="all, delete-orphan")
    solar_potentials = relationship("SolarPotential", back_populates="site", cascade="all, delete-orphan")
    wind_potentials = relationship("WindPotential", back_populates="site", cascade="all, delete-orphan")
    financial_analyses = relationship("FinancialAnalysis", back_populates="site", cascade="all, delete-orphan")
    telemetry_readings = relationship("TelemetryReading", back_populates="site", cascade="all, delete-orphan")
    rollup = relationship("SiteRollup", cascade="all, delete-orphan")


class WeatherReading(Base):
    """Growing time-series table, per the Data Flow Workflow (Step 2)."""
    __tablename__ = "weather_readings"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)
    reading_date = Column(DateTime, nullable=False)

    solar_irradiance = Column(Float, nullable=True)  # kWh/m^2/day
    wind_speed = Column(Float, nullable=True)         # m/s at 10m (surface)
    wind_speed_50m = Column(Float, nullable=True)      # m/s at 50m — closer to real turbine hub height
    temperature = Column(Float, nullable=True)         # deg C
    rainfall = Column(Float, nullable=True)             # mm
    cloud_cover_pct = Column(Float, nullable=True)

    site = relationship("Site", back_populates="weather_readings")


class SupplementalWeatherReading(Base):
    """
    Cross-check / real-time weather from OpenWeather (current conditions,
    global) and NOAA (short-range forecast, US only) — the two additional
    "Weather & Climate APIs" the architecture diagram lists alongside NASA
    POWER. Kept deliberately separate from WeatherReading/the suitability
    scoring pool: NASA POWER's daily historical averages are what the
    35%-weighted Resource Availability sub-score is calibrated against,
    and mixing in single-point live snapshots would silently skew that
    score. This table exists for live cross-validation and display, not
    as scoring input.
    """
    __tablename__ = "supplemental_weather_readings"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)
    source = Column(String, nullable=False)  # "OPENWEATHER" | "NOAA_FORECAST"
    fetched_at = Column(DateTime, default=datetime.datetime.utcnow)

    temperature_c = Column(Float, nullable=True)
    wind_speed_ms = Column(Float, nullable=True)
    cloud_cover_pct = Column(Float, nullable=True)
    condition_text = Column(String, nullable=True)
    forecast_period = Column(String, nullable=True)  # NOAA only, e.g. "Tonight", "Wednesday"

    site = relationship("Site", back_populates="supplemental_weather_readings")


class InfrastructureFeature(Base):
    """
    Roads/substations/urban areas near a site, pulled from OpenStreetMap.
    Supports the Geographic Intelligence Engine (proximity analysis).
    """
    __tablename__ = "infrastructure_features"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)
    feature_type = Column(String, nullable=False)  # road, substation, transmission_line, urban_area, water_body
    name = Column(String, nullable=True)
    distance_km = Column(Float, nullable=False)
    fetched_at = Column(DateTime, default=datetime.datetime.utcnow)

    site = relationship("Site", back_populates="infrastructure_features")


class SuitabilityScore(Base):
    """
    Output of the rule-based Site Suitability Scoring Engine.
    Weighted formula per project spec: Resource 35%, Geographic 25%,
    Infrastructure 15%, Environmental 15%, Economic 10%.
    This is NOT the AI/ML prediction layer (that's next week's work) —
    it is a deterministic scoring pass over data already collected.
    """
    __tablename__ = "suitability_scores"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)

    resource_score = Column(Float, nullable=False)
    geographic_score = Column(Float, nullable=False)
    infrastructure_score = Column(Float, nullable=False)
    environmental_score = Column(Float, nullable=False)
    economic_score = Column(Float, nullable=False)

    overall_score = Column(Float, nullable=False)
    category = Column(String, nullable=False)  # Excellent / Highly Suitable / Moderately Suitable / Low Suitability / Unsuitable

    computed_at = Column(DateTime, default=datetime.datetime.utcnow)

    site = relationship("Site", back_populates="suitability_scores")


class AlertSeverity(str, enum.Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)

    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(Enum(AlertSeverity), default=AlertSeverity.info)
    category = Column(String, nullable=False)  # weather / suitability / data_source / system

    is_read = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class SiteImage(Base):
    """
    Satellite imagery/metadata for a site — Copernicus Sentinel Hub (or
    compatible Copernicus Data Space) per the "Satellite image processing"
    module. Full scene metadata/raw response is archived to MongoDB; this
    row holds the structured summary the rest of the app queries against.
    """
    __tablename__ = "site_images"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)
    provider = Column(String, nullable=False, default="copernicus_sentinel_hub")
    scene_date = Column(DateTime, nullable=True)
    cloud_cover_pct = Column(Float, nullable=True)
    ndvi_mean = Column(Float, nullable=True)  # vegetation index, feeds land-cover/environmental scoring
    land_cover_summary = Column(String, nullable=True)  # e.g. "bare_soil", "cropland", "urban"
    thumbnail_url = Column(String, nullable=True)
    source_status = Column(String, nullable=False, default="live")  # "live" or "unavailable_no_credentials"
    fetched_at = Column(DateTime, default=datetime.datetime.utcnow)

    site = relationship("Site", back_populates="images")


class EnvironmentalConstraint(Base):
    """
    Land-use/demographic/protected-area context per "Environmental
    databases" and "Demographic & land data" modules. Protected-area and
    water-body proximity come from OpenStreetMap; population/GDP context
    comes from the World Bank API at the country level.
    """
    __tablename__ = "environmental_constraints"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)

    protected_area_distance_km = Column(Float, nullable=True)
    water_body_distance_km = Column(Float, nullable=True)
    agricultural_land_nearby = Column(Integer, default=0)  # 1/0
    urban_area_distance_km = Column(Float, nullable=True)

    country_iso3 = Column(String, nullable=True)
    population_density_km2 = Column(Float, nullable=True)  # World Bank, country-level proxy
    gdp_per_capita_usd = Column(Float, nullable=True)
    electricity_consumption_kwh_per_capita = Column(Float, nullable=True)  # World Bank EG.USE.ELEC.KH.PC — feeds Grid Contribution Forecasting
    data_source = Column(String, nullable=True)

    fetched_at = Column(DateTime, default=datetime.datetime.utcnow)

    site = relationship("Site", back_populates="environmental_constraints")


class SolarPotential(Base):
    """Solar Potential Prediction Engine output — deterministic physics/derating model, not ML."""
    __tablename__ = "solar_potentials"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)

    annual_irradiance_kwh_m2 = Column(Float, nullable=True)
    peak_sun_hours = Column(Float, nullable=True)
    panel_efficiency_pct = Column(Float, nullable=True)      # temperature-derated STC efficiency
    shading_loss_pct = Column(Float, nullable=True)          # terrain/horizon obstruction estimate
    performance_ratio_pct = Column(Float, nullable=True)
    expected_energy_output_mwh_yr = Column(Float, nullable=True)  # per installed MWp
    capacity_factor_pct = Column(Float, nullable=True)

    # ML-Assisted Prediction (Beta) — see app/services/ml_solar_predictor.py.
    # Trained on real measured plant data (not the same physics formula
    # above), null until a model has actually been trained and the file
    # exists. Always shown alongside, never in place of, the physics
    # numbers above — the physics engine is the validated baseline.
    ml_performance_ratio_pct = Column(Float, nullable=True)
    ml_expected_energy_output_mwh_yr = Column(Float, nullable=True)
    ml_model_version = Column(String, nullable=True)  # e.g. "rf_v1_2026-08-21" — which trained model produced this

    computed_at = Column(DateTime, default=datetime.datetime.utcnow)

    site = relationship("Site", back_populates="solar_potentials")


class WindPotential(Base):
    """Wind Potential Prediction Engine output — wind-shear/Rayleigh deterministic model, not ML."""
    __tablename__ = "wind_potentials"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)

    average_wind_speed_ms = Column(Float, nullable=True)      # extrapolated to hub height
    wind_power_density_w_m2 = Column(Float, nullable=True)
    turbulence_intensity_pct = Column(Float, nullable=True)
    turbine_suitability_score = Column(Float, nullable=True)  # 0-100
    turbine_class = Column(String, nullable=True)             # IEC I/II/III/IV proxy
    expected_aep_mwh_yr = Column(Float, nullable=True)        # per installed MW
    capacity_factor_pct = Column(Float, nullable=True)

    # ML-Assisted Prediction — see app/services/ml_wind_predictor.py.
    # Always shown alongside, never in place of, the physics numbers above.
    ml_capacity_factor_pct = Column(Float, nullable=True)
    ml_expected_aep_mwh_yr = Column(Float, nullable=True)
    ml_model_version = Column(String, nullable=True)

    computed_at = Column(DateTime, default=datetime.datetime.utcnow)

    site = relationship("Site", back_populates="wind_potentials")


class FinancialAnalysis(Base):
    """Investment Analytics — deterministic NPV/IRR/LCOE/payback math, not ML."""
    __tablename__ = "financial_analyses"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)

    technology = Column(String, nullable=False)  # solar / wind / hybrid
    capacity_mw = Column(Float, nullable=False)
    capex_usd = Column(Float, nullable=False)
    opex_usd_per_yr = Column(Float, nullable=False)
    discount_rate_pct = Column(Float, nullable=False)
    project_lifetime_yrs = Column(Integer, nullable=False)
    electricity_price_usd_per_mwh = Column(Float, nullable=False)

    annual_energy_mwh = Column(Float, nullable=True)
    npv_usd = Column(Float, nullable=True)
    irr_pct = Column(Float, nullable=True)
    lcoe_usd_per_mwh = Column(Float, nullable=True)
    payback_years = Column(Float, nullable=True)

    computed_at = Column(DateTime, default=datetime.datetime.utcnow)

    site = relationship("Site", back_populates="financial_analyses")


class ReportTemplate(Base):
    """Custom Report Builder — saved section selections a user can re-run."""
    __tablename__ = "report_templates"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    # Comma-separated section keys, e.g. "summary,suitability,solar,wind,financial,environmental"
    sections = Column(Text, nullable=False)
    is_executive_summary = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class IntegrationTypeEnum(str, enum.Enum):
    financial_modeling = "financial_modeling"
    project_management = "project_management"
    scada_iot = "scada_iot"
    power_simulation = "power_simulation"
    third_party_analytics = "third_party_analytics"


class IntegrationConnection(Base):
    """
    Outbound/inbound connector registration for the platform's five
    Integrations (financial modeling, project-mgmt tools, SCADA/IoT,
    power simulation, third-party analytics). Generic webhook/REST
    connector — point it at any compatible endpoint (Zapier, a Jira
    webhook, an MQTT-to-HTTP bridge, Segment, etc). No vendor lock-in
    to one named product per integration category.
    """
    __tablename__ = "integration_connections"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    integration_type = Column(Enum(IntegrationTypeEnum), nullable=False)
    name = Column(String, nullable=False)
    endpoint_url = Column(String, nullable=False)
    auth_header_name = Column(String, nullable=True)     # e.g. "Authorization"
    auth_header_value = Column(String, nullable=True)     # stored as provided; see security note in router
    is_active = Column(Integer, default=1)

    last_status = Column(String, nullable=True)  # "ok" / "error" / null (never used)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class TelemetryReading(Base):
    """
    SCADA/IoT ingestion — live operational telemetry pushed in from an
    already-deployed site's monitoring system (inverter output, turbine
    RPM, grid export, etc). Append-only time series; a TimescaleDB
    hypertable is created over this table when the DB supports it (see
    database.py) since this is the platform's highest-volume time series.
    """
    __tablename__ = "telemetry_readings"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)
    integration_id = Column(Integer, ForeignKey("integration_connections.id"), nullable=True)

    metric_name = Column(String, nullable=False)  # e.g. "ac_power_kw", "turbine_rpm", "grid_export_kwh"
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=True)
    recorded_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    site = relationship("Site", back_populates="telemetry_readings")


class AuditLog(Base):
    """Minimal audit trail for security/compliance (who did what, when)."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)       # e.g. "login", "create_project", "delete_site"
    resource = Column(String, nullable=True)       # e.g. "project:14"
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class SiteRollup(Base):
    """
    Data Warehouse — denormalized, query-optimized snapshot of one site's
    latest cross-engine metrics, one row per site, overwritten on each
    refresh. This is the "Data Warehouse (Snowflake/BigQuery)" layer in
    the architecture diagram, implemented as a materialized Postgres table
    so it works with zero extra infra; app/warehouse.py additionally
    exports the same row set to Parquet (WAREHOUSE_EXPORT_DIR) for an
    external warehouse to bulk-load if one is configured.

    Kept separate from the normalized operational tables (Sites,
    SuitabilityScore, etc.) on purpose: those are optimized for
    transactional reads/writes, this one is optimized for BI/reporting
    fan-out queries (whole-portfolio aggregates) without joining six
    tables every time a dashboard loads.
    """
    __tablename__ = "warehouse_site_rollup"

    site_id = Column(Integer, ForeignKey("sites.id"), primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    site_name = Column(String, nullable=False)
    region_name = Column(String, nullable=True)

    overall_suitability_score = Column(Float, nullable=True)
    suitability_category = Column(String, nullable=True)

    solar_expected_output_mwh_yr = Column(Float, nullable=True)
    solar_capacity_factor_pct = Column(Float, nullable=True)
    wind_expected_aep_mwh_yr = Column(Float, nullable=True)
    wind_capacity_factor_pct = Column(Float, nullable=True)

    financial_npv_usd = Column(Float, nullable=True)
    financial_irr_pct = Column(Float, nullable=True)
    financial_lcoe_usd_per_mwh = Column(Float, nullable=True)

    protected_area_distance_km = Column(Float, nullable=True)
    substation_distance_km = Column(Float, nullable=True)

    refreshed_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
