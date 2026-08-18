from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from ..core.database import Base

class Site(Base):
    __tablename__ = "sites"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    site_name = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    region = Column(String(255))
    land_area = Column(Float)  # in acres
    elevation = Column(Float)  # in meters
    land_ownership = Column(String(255))
    existing_infrastructure = Column(Text)
    geometry = Column(Geometry('POINT', srid=4326))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    project = relationship("Project", back_populates="sites")
    environmental_data = relationship("EnvironmentalData", back_populates="site", cascade="all, delete-orphan")
    solar_assessment = relationship("SolarAssessment", back_populates="site", uselist=False, cascade="all, delete-orphan")
    wind_assessment = relationship("WindAssessment", back_populates="site", uselist=False, cascade="all, delete-orphan")
    suitability_score = relationship("SuitabilityScore", back_populates="site", uselist=False, cascade="all, delete-orphan")