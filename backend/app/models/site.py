from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime, Enum, Boolean
from sqlalchemy.orm import relationship
import enum
from ..database import Base

class EnergyType(str, enum.Enum):
    solar = "solar"
    wind = "wind"
    hybrid = "hybrid"

class SiteStatus(str, enum.Enum):
    under_review = "under_review"
    approved = "approved"
    rejected = "rejected"

class LandOwnership(str, enum.Enum):
    government = "government"
    private = "private"
    community = "community"
    unknown = "unknown"

class Site(Base):
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    elevation = Column(Float, nullable=True)          # meters
    land_area = Column(Float, nullable=True)          # hectares
    energy_type = Column(Enum(EnergyType), nullable=False)
    status = Column(Enum(SiteStatus), default=SiteStatus.under_review)
    land_ownership = Column(Enum(LandOwnership), default=LandOwnership.unknown)
    existing_infrastructure = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="sites")
    creator = relationship("User")
    history = relationship("DeploymentHistory", back_populates="site", order_by="DeploymentHistory.changed_at.desc()")

class DeploymentHistory(Base):
    __tablename__ = "deployment_history"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    previous_status = Column(Enum(SiteStatus), nullable=True)
    new_status = Column(Enum(SiteStatus), nullable=False)
    notes = Column(Text, nullable=True)
    changed_at = Column(DateTime, default=datetime.utcnow)

    site = relationship("Site", back_populates="history")
    user = relationship("User")
