from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base

class EnvironmentalData(Base):
    __tablename__ = "environmental_data"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"))
    
    # Solar data (from NASA POWER)
    solar_irradiance = Column(Float)  # kWh/m²/day
    temperature = Column(Float)  # °C
    cloud_cover = Column(Float)  # percentage
    rainfall = Column(Float)  # mm/year
    
    # Wind data
    wind_speed = Column(Float)  # m/s
    wind_direction = Column(Float)  # degrees
    
    # Terrain data (from SRTM)
    slope = Column(Float)  # degrees
    
    # Vegetation data (from Sentinel)
    ndvi = Column(Float)  # Normalized Difference Vegetation Index
    
    # Additional data
    land_cover = Column(String(255))
    data_source = Column(String(255))
    fetch_date = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    site = relationship("Site", back_populates="environmental_data")