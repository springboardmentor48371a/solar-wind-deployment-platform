import uuid
from sqlalchemy import Column, String, Text, Boolean, Float, Numeric, ForeignKey, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Role(Base):
    __tablename__ = "roles"

    role_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_name = Column(String(50), unique=True, nullable=False) # Planner, GIS Analyst, Project Manager, Admin
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    users = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=True)
    organization = Column(String(150), nullable=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.role_id"), nullable=False)
    account_status = Column(String(20), default="Active") # Active / Inactive
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    role = relationship("Role", back_populates="users")
    projects = relationship("Project", back_populates="creator")
    reports = relationship("Report", back_populates="generator")
    notifications = relationship("Notification", back_populates="user")


class Project(Base):
    __tablename__ = "projects"

    project_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    region = Column(String(100), nullable=False)
    project_status = Column(String(20), default="Planning") # Planning / Analysis / Completed
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    creator = relationship("User", back_populates="projects")
    sites = relationship("Site", back_populates="project", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="project", cascade="all, delete-orphan")


class Site(Base):
    __tablename__ = "sites"

    site_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=False)
    site_name = Column(String(150), nullable=False)
    latitude = Column(Numeric(10, 7), nullable=False)
    longitude = Column(Numeric(10, 7), nullable=False)
    region = Column(String(100), nullable=False)
    land_area = Column(Float, nullable=False) # Area in Acres/Hectares
    elevation = Column(Float, nullable=False) # Elevation in meters
    land_type = Column(String(100), nullable=True) # Desert / Agriculture / Plain etc.
    ownership = Column(String(100), nullable=True) # Private / Government
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="sites")
    environmental_data = relationship("EnvironmentalData", back_populates="site", uselist=False, cascade="all, delete-orphan")
    assessments = relationship("SiteAssessment", back_populates="site", cascade="all, delete-orphan")


class EnvironmentalData(Base):
    __tablename__ = "environmental_data"

    environment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.site_id"), nullable=False, unique=True)
    solar_irradiance = Column(Float, nullable=False) # kWh/m²/day
    wind_speed = Column(Float, nullable=False) # m/s
    wind_direction = Column(Float, nullable=False) # Degrees
    temperature = Column(Float, nullable=False) # °C
    rainfall = Column(Float, nullable=False) # mm
    humidity = Column(Float, nullable=False) # %
    cloud_cover = Column(Float, nullable=False) # %
    terrain_slope = Column(Float, nullable=False) # Degrees
    vegetation_index = Column(Float, nullable=False) # NDVI
    nearest_substation_distance = Column(Float, nullable=False) # km
    road_distance = Column(Float, nullable=False) # km
    protected_area = Column(Boolean, nullable=False) # True/False
    collected_at = Column(DateTime(timezone=True), server_default=func.now())

    site = relationship("Site", back_populates="environmental_data")

    @property
    def climate_data_source(self) -> str:
        if self.site and self.site.assessments:
            for assessment in sorted(self.site.assessments, key=lambda a: a.analyzed_at, reverse=True):
                if assessment.recommendation:
                    if "Climate Source: NASA POWER Climatology" in assessment.recommendation:
                        return "NASA POWER Climatology"
                    elif "Climate Source: Local Estimate" in assessment.recommendation:
                        return "Local Estimate"
        return "Local Estimate"

    @property
    def wind_power_density(self) -> float:
        if self.site:
            from app.global_wind_atlas import fetch_gwa_point_data
            gwa_data = fetch_gwa_point_data(float(self.site.latitude), float(self.site.longitude))
            if gwa_data:
                return gwa_data["wind_power_density"]
        # Fallback to local estimate calculation
        return round(0.5 * 1.225 * (self.wind_speed ** 3), 2)

    @property
    def wind_resource(self) -> str:
        if self.site:
            from app.global_wind_atlas import fetch_gwa_point_data
            gwa_data = fetch_gwa_point_data(float(self.site.latitude), float(self.site.longitude))
            if gwa_data:
                return gwa_data["wind_resource"]
        v = self.wind_speed
        if v < 5.6:
            res_class = "Class 1 (Poor)"
        elif v < 6.4:
            res_class = "Class 2 (Marginal)"
        elif v < 7.0:
            res_class = "Class 3 (Fair)"
        elif v < 7.5:
            res_class = "Class 4 (Good)"
        elif v < 8.0:
            res_class = "Class 5 (Excellent)"
        elif v < 8.8:
            res_class = "Class 6 (Outstanding)"
        else:
            res_class = "Class 7 (Superb)"
        return f"Derived Wind Resource Class: {res_class}"

    @property
    def wind_data_source(self) -> str:
        if self.site:
            from app.global_wind_atlas import fetch_gwa_point_data
            gwa_data = fetch_gwa_point_data(float(self.site.latitude), float(self.site.longitude))
            if gwa_data:
                if abs(self.wind_speed - gwa_data["wind_speed"]) < 0.01:
                    return "Global Wind Atlas"
        if self.climate_data_source == "NASA POWER Climatology":
            return "NASA POWER"
        return "Local Estimate"

    @property
    def infra_data_source(self) -> str:
        if self.site:
            from app.osm import fetch_osm_infrastructure
            osm_data = fetch_osm_infrastructure(float(self.site.latitude), float(self.site.longitude))
            if osm_data:
                if (abs(self.nearest_substation_distance - osm_data["nearest_substation_distance"]) < 0.01 and 
                    abs(self.road_distance - osm_data["road_distance"]) < 0.01):
                    return "OpenStreetMap"
        return "Local Estimate"

    @property
    def elevation_data_source(self) -> str:
        if self.site:
            from app.srtm import fetch_srtm_data
            srtm_data = fetch_srtm_data(float(self.site.latitude), float(self.site.longitude))
            if srtm_data:
                if abs(self.site.elevation - srtm_data["elevation"]) < 0.01:
                    return "SRTM"
        return "Local Estimate"

    @property
    def land_cover_data_source(self) -> str:
        if self.site:
            from app.landcover import fetch_esri_landcover
            landcover_data = fetch_esri_landcover(float(self.site.latitude), float(self.site.longitude))
            if landcover_data and self.site.land_type == landcover_data["mapped_land_type"]:
                return landcover_data["source"]
        return "Local Estimate"

    @property
    def protected_area_data_source(self) -> str:
        if self.site:
            from app.osm import fetch_osm_protected_areas
            osm_data = fetch_osm_protected_areas(float(self.site.latitude), float(self.site.longitude))
            if osm_data and self.protected_area == osm_data["is_protected"]:
                return "OpenStreetMap"
        return "Local Estimate"


class SiteAssessment(Base):
    __tablename__ = "site_assessments"

    assessment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.site_id"), nullable=False)
    solar_energy_prediction = Column(Float, nullable=False)
    wind_energy_prediction = Column(Float, nullable=False)
    solar_capacity_factor = Column(Float, nullable=False)
    wind_capacity_factor = Column(Float, nullable=False)
    suitability_score = Column(Float, nullable=False)
    suitability_category = Column(String(50), nullable=False) # Excellent / High / Moderate / Low / Unsuitable
    energy_forecast = Column(Float, nullable=False)
    revenue_estimate = Column(Float, nullable=False)
    deployment_type = Column(String(20), nullable=False) # Solar / Wind / Hybrid
    recommendation = Column(Text, nullable=True)
    analysis_status = Column(String(20), default="Pending") # Pending / Completed
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now())

    site = relationship("Site", back_populates="assessments")

    @property
    def climate_data_source(self) -> str:
        if self.recommendation:
            if "Climate Source: NASA POWER Climatology" in self.recommendation:
                return "NASA POWER Climatology"
            elif "Climate Source: Local Estimate" in self.recommendation:
                return "Local Estimate"
        return "Local Estimate"

    @property
    def wind_power_density(self) -> float:
        if self.site and self.site.environmental_data:
            return self.site.environmental_data.wind_power_density
        return 0.0

    @property
    def wind_resource(self) -> str:
        if self.site and self.site.environmental_data:
            return self.site.environmental_data.wind_resource
        return "Derived Wind Resource Class: Class 1 (Poor)"

    @property
    def wind_data_source(self) -> str:
        if self.site and self.site.environmental_data:
            return self.site.environmental_data.wind_data_source
        return "Local Estimate"

    @property
    def infra_data_source(self) -> str:
        if self.site and self.site.environmental_data:
            return self.site.environmental_data.infra_data_source
        return "Local Estimate"

    @property
    def elevation_data_source(self) -> str:
        if self.site and self.site.environmental_data:
            return self.site.environmental_data.elevation_data_source
        return "Local Estimate"

    @property
    def land_cover_data_source(self) -> str:
        if self.site and self.site.environmental_data:
            return self.site.environmental_data.land_cover_data_source
        return "Local Estimate"

    @property
    def protected_area_data_source(self) -> str:
        if self.site and self.site.environmental_data:
            return self.site.environmental_data.protected_area_data_source
        return "Local Estimate"

    @property
    def solar_model_source(self) -> str:
        return "Synthetic Fallback — Required Feature Unavailable"

    @property
    def wind_model_source(self) -> str:
        try:
            from app.ml_model import predictor
            if predictor.real_wind_model is not None:
                return "Real Historical ML Model — Kelmarsh SCADA (Not validated for Gujarat/Rajasthan)"
        except Exception:
            pass
        return "Synthetic Fallback"

    @property
    def is_hybrid_mode(self) -> bool:
        return "Real" in self.wind_model_source and "Synthetic" in self.solar_model_source

    @property
    def is_synthetic(self) -> bool:
        return self.wind_model_source == "Synthetic Fallback"


class Report(Base):
    __tablename__ = "reports"

    report_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=False)
    report_type = Column(String(100), nullable=False) # Site Report / Investment Report
    generated_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    report_url = Column(Text, nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="reports")
    generator = relationship("User", back_populates="reports")


class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False) # Weather / AI / System
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="notifications")
