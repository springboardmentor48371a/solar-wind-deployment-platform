from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base

class SolarAssessment(Base):
    __tablename__ = "solar_assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), unique=True)
    
    peak_sun_hours = Column(Float)
    solar_energy_potential = Column(Float)  # MWh/year
    capacity_factor = Column(Float)  # percentage
    performance_ratio = Column(Float)
    monthly_generation = Column(Text)  # JSON data
    ml_prediction = Column(Float)
    prediction_confidence = Column(Float)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    site = relationship("Site", back_populates="solar_assessment")

class WindAssessment(Base):
    __tablename__ = "wind_assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), unique=True)
    
    avg_wind_speed = Column(Float)
    wind_power_density = Column(Float)
    capacity_factor = Column(Float)
    annual_energy_production = Column(Float)  # MWh/year
    turbine_suitability = Column(Text)  # JSON data
    ml_prediction = Column(Float)
    prediction_confidence = Column(Float)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    site = relationship("Site", back_populates="wind_assessment")