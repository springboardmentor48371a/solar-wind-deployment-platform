from datetime import datetime
from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, Date, String
from sqlalchemy.orm import relationship
from ..database import Base

class EnvironmentalData(Base):
    __tablename__ = "environmental_data"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False, index=True)

    # Date of the reading
    date = Column(Date, nullable=False, index=True)

    # Solar
    solar_irradiance = Column(Float, nullable=True)       # W/m²
    peak_sun_hours = Column(Float, nullable=True)         # hours/day

    # Wind
    wind_speed = Column(Float, nullable=True)             # m/s at 10m
    wind_speed_50m = Column(Float, nullable=True)         # m/s at 50m
    wind_direction = Column(Float, nullable=True)         # degrees

    # Climate
    temperature_max = Column(Float, nullable=True)        # °C
    temperature_min = Column(Float, nullable=True)        # °C
    temperature_avg = Column(Float, nullable=True)        # °C
    rainfall = Column(Float, nullable=True)               # mm
    cloud_cover = Column(Float, nullable=True)            # %
    humidity = Column(Float, nullable=True)               # %

    # Terrain (static, fetched once)
    elevation = Column(Float, nullable=True)              # meters
    land_slope = Column(Float, nullable=True)             # degrees
    aspect_deg = Column(Float, nullable=True)             # degrees 0-360, 180=south-facing

    # Vegetation
    vegetation_index = Column(Float, nullable=True)       # NDVI -1 to 1

    source = Column(String(50), nullable=True)            # "nasa_power", "open_meteo"
    fetched_at = Column(DateTime, default=datetime.utcnow)

    site = relationship("Site")
