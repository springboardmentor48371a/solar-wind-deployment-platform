import uuid
import enum
from sqlalchemy import Column, String, Text, Float, Boolean, ForeignKey, DateTime, Enum, Numeric
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime

Base = declarative_base()

# --- ENUMS ---
class AccountStatus(str, enum.Enum):
    Active = "Active"
    Inactive = "Inactive"

class ProjectStatus(str, enum.Enum):
    Planning = "Planning"
    Analysis = "Analysis"
    Completed = "Completed"

class SuitabilityCategory(str, enum.Enum):
    Excellent = "Excellent"
    High = "High"
    Moderate = "Moderate"
    Low = "Low"
    Unsuitable = "Unsuitable"

class DeploymentType(str, enum.Enum):
    Solar = "Solar"
    Wind = "Wind"
    Hybrid = "Hybrid"

class AnalysisStatus(str, enum.Enum):
    Pending = "Pending"
    Completed = "Completed"

# --- TABLES ---

class Role(Base):
    __tablename__ = "roles"
    
    role_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_name = Column(String(50), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    users = relationship("User", back_populates="role")

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    phone_number = Column(String(20))
    organization = Column(String(150))
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.role_id"))
    account_status = Column(Enum(AccountStatus), default=AccountStatus.Active)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    role = relationship("Role", back_populates="users")
    projects = relationship("Project", back_populates="creator")
    reports = relationship("Report", back_populates="generator")
    notifications = relationship("Notification", back_populates="user")

class Project(Base):
    __tablename__ = "projects"
    
    project_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_name = Column(String(150), nullable=False)
    description = Column(Text)
    region = Column(String(100))
    project_status = Column(Enum(ProjectStatus), default=ProjectStatus.Planning)

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    creator = relationship("User", back_populates="projects")
    sites = relationship("Site", back_populates="project", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="project")

class Site(Base):
    __tablename__ = "sites"
    
    site_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id"))
    site_name = Column(String(150), nullable=False)
    latitude = Column(Numeric(10, 7), nullable=False)
    longitude = Column(Numeric(10, 7), nullable=False)
    region = Column(String(100))
    land_area = Column(Float)
    elevation = Column(Float)
    land_type = Column(String(100))
    ownership = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("Project", back_populates="sites")
    environmental_data = relationship("EnvironmentalData", back_populates="site", uselist=False, cascade="all, delete-orphan")
    assessment = relationship("SiteAssessment", back_populates="site", uselist=False, cascade="all, delete-orphan")

class EnvironmentalData(Base):
    __tablename__ = "environmental_data"
    
    environment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.site_id"), unique=True)
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
    protected_area = Column(Boolean)
    collected_at = Column(DateTime, default=datetime.utcnow)
    
    site = relationship("Site", back_populates="environmental_data")

class SiteAssessment(Base):
    __tablename__ = "site_assessments"
    
    assessment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.site_id"), unique=True)
    solar_energy_prediction = Column(Float)
    wind_energy_prediction = Column(Float)
    solar_capacity_factor = Column(Float)
    wind_capacity_factor = Column(Float)
    suitability_score = Column(Float)
    suitability_category = Column(Enum(SuitabilityCategory))
    energy_forecast = Column(Float)
    revenue_estimate = Column(Float)
    deployment_type = Column(Enum(DeploymentType))
    recommendation = Column(Text)
    analysis_status = Column(Enum(AnalysisStatus), default=AnalysisStatus.Pending)
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    
    site = relationship("Site", back_populates="assessment")

class Report(Base):
    __tablename__ = "reports"
    
    report_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id"))
    report_type = Column(String(100))
    generated_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    report_url = Column(Text)
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("Project", back_populates="reports")
    generator = relationship("User", back_populates="reports")

class Notification(Base):
    __tablename__ = "notifications"
    
    notification_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    title = Column(String(150))
    message = Column(Text)
    notification_type = Column(String(50))
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="notifications")