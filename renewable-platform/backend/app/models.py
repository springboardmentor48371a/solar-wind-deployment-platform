"""
SQLAlchemy ORM models covering:
 - Users & Roles                    (Module 1)
 - Projects & Sites                 (Module 2)
 - Environmental Data               (Module 3)
 - Solar / Wind Potential           (Modules 5 & 6)
 - Site Suitability & Scoring       (Modules 7 & 10)
 - Energy Forecasts                 (Module 8)
 - Deployment Recommendations       (Module 9)
"""
import enum
import datetime as dt
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text, Boolean
)
from sqlalchemy.orm import relationship
from .database import Base


class RoleEnum(str, enum.Enum):
    planner = "renewable_energy_planner"
    gis_analyst = "gis_analyst"
    project_manager = "project_manager"
    admin = "administrator"


class SiteTypeEnum(str, enum.Enum):
    solar = "solar"
    wind = "wind"
    hybrid = "hybrid"


class SuitabilityCategory(str, enum.Enum):
    excellent = "Excellent"
    highly_suitable = "Highly Suitable"
    moderately_suitable = "Moderately Suitable"
    low_suitability = "Low Suitability"
    unsuitable = "Unsuitable"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.planner, nullable=False)
    organization = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    projects = relationship("Project", back_populates="owner")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    objective = Column(String, nullable=True)
    region = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    owner = relationship("User", back_populates="projects")
    sites = relationship("Site", back_populates="project", cascade="all, delete-orphan")


class Site(Base):
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    name = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    region = Column(String, nullable=True)
    land_area_hectares = Column(Float, nullable=True)
    elevation_m = Column(Float, nullable=True)
    existing_infrastructure = Column(String, nullable=True)
    land_ownership = Column(String, nullable=True)
    site_type = Column(Enum(SiteTypeEnum), default=SiteTypeEnum.hybrid)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    project = relationship("Project", back_populates="sites")
    environmental_data = relationship("EnvironmentalData", back_populates="site", uselist=False, cascade="all, delete-orphan")
    solar_prediction = relationship("SolarPrediction", back_populates="site", uselist=False, cascade="all, delete-orphan")
    wind_prediction = relationship("WindPrediction", back_populates="site", uselist=False, cascade="all, delete-orphan")
    score = relationship("SiteScore", back_populates="site", uselist=False, cascade="all, delete-orphan")
    forecast = relationship("EnergyForecast", back_populates="site", uselist=False, cascade="all, delete-orphan")


class EnvironmentalData(Base):
    __tablename__ = "environmental_data"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), unique=True)

    solar_irradiance_kwh_m2_day = Column(Float)
    wind_speed_avg_ms = Column(Float)
    wind_direction_deg = Column(Float)
    temperature_avg_c = Column(Float)
    rainfall_mm_year = Column(Float)
    cloud_cover_pct = Column(Float)
    land_slope_pct = Column(Float)
    vegetation_index_ndvi = Column(Float)

    distance_to_road_km = Column(Float)
    distance_to_transmission_km = Column(Float)
    distance_to_substation_km = Column(Float)
    distance_to_urban_km = Column(Float)
    distance_to_water_km = Column(Float)
    in_protected_zone = Column(Boolean, default=False)

    fetched_at = Column(DateTime, default=dt.datetime.utcnow)

    site = relationship("Site", back_populates="environmental_data")


class SolarPrediction(Base):
    __tablename__ = "solar_predictions"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), unique=True)

    annual_irradiance_kwh_m2 = Column(Float)
    peak_sun_hours = Column(Float)
    panel_efficiency_pct = Column(Float)
    performance_ratio = Column(Float)
    capacity_factor_pct = Column(Float)
    expected_energy_output_mwh_year = Column(Float)
    shading_loss_pct = Column(Float)
    computed_at = Column(DateTime, default=dt.datetime.utcnow)

    site = relationship("Site", back_populates="solar_prediction")


class WindPrediction(Base):
    __tablename__ = "wind_predictions"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), unique=True)

    avg_wind_speed_ms = Column(Float)
    wind_power_density_w_m2 = Column(Float)
    turbulence_intensity_pct = Column(Float)
    turbine_suitability = Column(String)
    capacity_factor_pct = Column(Float)
    expected_annual_energy_mwh = Column(Float)
    computed_at = Column(DateTime, default=dt.datetime.utcnow)

    site = relationship("Site", back_populates="wind_prediction")


class SiteScore(Base):
    __tablename__ = "site_scores"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), unique=True)

    resource_score = Column(Float)       # 35%
    geographic_score = Column(Float)     # 25%
    infrastructure_score = Column(Float) # 15%
    environmental_score = Column(Float)  # 15%
    economic_score = Column(Float)       # 10%
    overall_score = Column(Float)
    category = Column(Enum(SuitabilityCategory))
    recommended_technology = Column(Enum(SiteTypeEnum))
    computed_at = Column(DateTime, default=dt.datetime.utcnow)

    site = relationship("Site", back_populates="score")


class EnergyForecast(Base):
    __tablename__ = "energy_forecasts"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), unique=True)

    year1_mwh = Column(Float)
    year5_mwh = Column(Float)
    year10_mwh = Column(Float)
    year25_mwh = Column(Float)
    estimated_capex_usd = Column(Float)
    estimated_annual_revenue_usd = Column(Float)
    payback_period_years = Column(Float)
    computed_at = Column(DateTime, default=dt.datetime.utcnow)

    site = relationship("Site", back_populates="forecast")
