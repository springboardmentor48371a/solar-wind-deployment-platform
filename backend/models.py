import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, Float, ForeignKey, Boolean, Enum, Numeric
from sqlalchemy.dialects.postgresql import UUID

try:
    from .database import Base
except ImportError:
    from database import Base


class Role(Base):
    __tablename__ = "roles"

    role_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    phone_number = Column(String(20))
    organization = Column(String(150))
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.role_id"), nullable=True)
    # Legacy role string retained for backward compatibility with existing API payloads.
    role = Column(String(50), nullable=False, default="Renewable Energy Planner")
    account_status = Column(
        Enum("Active", "Inactive", name="account_status_enum", native_enum=False),
        default="Active",
        nullable=False,
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class Project(Base):
    __tablename__ = "projects"

    project_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_name = Column(String(150), nullable=False)
    description = Column(Text)
    region = Column(String(100), nullable=False)
    project_status = Column(
        Enum("Planning", "Analysis", "Completed", name="project_status_enum", native_enum=False),
        default="Planning",
        nullable=False,
    )
    created_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class Site(Base):
    __tablename__ = "sites"

    site_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=False)
    site_name = Column(String(150), nullable=False)
    latitude = Column(Numeric(10, 7), nullable=False)
    longitude = Column(Numeric(10, 7), nullable=False)
    region = Column(String(100))
    land_area = Column(Float)
    elevation = Column(Float)
    land_type = Column(String(100))
    ownership = Column(String(100))
    # Legacy fields kept for compatibility with existing site form and APIs.
    area_acres = Column(Float)
    existing_infrastructure = Column(Text)
    land_ownership = Column(Text)
    address = Column(Text)
    site_status = Column(String(20), default="Draft")
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class EnvironmentalData(Base):
    __tablename__ = "environmental_data"

    environment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.site_id"), nullable=False)
    solar_irradiance = Column(Float)
    wind_speed = Column(Float)
    wind_direction = Column(Float)
    temperature = Column(Float)
    rainfall = Column(Float)
    humidity = Column(Float)
    cloud_cover = Column(Float)
    terrain_slope = Column(Float)
    vegetation_index = Column(Float)
    nearest_substation_distance = Column(Float)
    road_distance = Column(Float)
    protected_area = Column(Boolean, default=False)
    collected_at = Column(DateTime, default=datetime.utcnow)


class SiteAssessment(Base):
    __tablename__ = "site_assessments"

    assessment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.site_id"), nullable=False)
    solar_energy_prediction = Column(Float)
    wind_energy_prediction = Column(Float)
    solar_capacity_factor = Column(Float)
    wind_capacity_factor = Column(Float)
    suitability_score = Column(Float)
    suitability_category = Column(
        Enum("Excellent", "High", "Moderate", "Low", "Unsuitable", name="suitability_category_enum", native_enum=False)
    )
    energy_forecast = Column(Float)
    revenue_estimate = Column(Float)
    deployment_type = Column(Enum("Solar", "Wind", "Hybrid", name="deployment_type_enum", native_enum=False))
    recommendation = Column(Text)
    analysis_status = Column(Enum("Pending", "Completed", name="analysis_status_enum", native_enum=False), default="Pending")
    analyzed_at = Column(DateTime)


class Report(Base):
    __tablename__ = "reports"

    report_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=False)
    report_type = Column(String(100), nullable=False)
    generated_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    report_url = Column(Text)
    generated_at = Column(DateTime, default=datetime.utcnow)


class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50))
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
