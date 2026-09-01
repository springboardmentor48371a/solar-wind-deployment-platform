from datetime import datetime, date
from sqlalchemy import Column, Integer, Float, String, DateTime, Date, Text
from .database import Base

class SitePrediction(Base):
    __tablename__ = "site_predictions"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, unique=True, nullable=False, index=True)

    # Solar (Module 5)
    solar_yield_kwh = Column(Float, nullable=True)
    solar_capacity_factor = Column(Float, nullable=True)
    solar_score = Column(Float, nullable=True)

    # Wind (Module 6)
    wind_power_kw = Column(Float, nullable=True)
    wind_capacity_factor = Column(Float, nullable=True)
    wind_score = Column(Float, nullable=True)

    # Land Cover (Module 4)
    land_cover_class = Column(String(50), nullable=True)
    vegetation_index = Column(Float, nullable=True)
    land_slope = Column(Float, nullable=True)
    land_cover_score = Column(Float, nullable=True)

    # Suitability (Module 7)
    suitability_score = Column(Float, nullable=True)
    suitability_category = Column(String(50), nullable=True)
    resource_score = Column(Float, nullable=True)
    geographic_score = Column(Float, nullable=True)
    infrastructure_score = Column(Float, nullable=True)
    environmental_score = Column(Float, nullable=True)
    economic_score = Column(Float, nullable=True)

    predicted_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EnergyForecast(Base):
    __tablename__ = "energy_forecasts"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, nullable=False, index=True)
    forecast_date = Column(Date, nullable=False)
    predicted_solar_kwh = Column(Float, nullable=True)
    predicted_wind_kwh = Column(Float, nullable=True)
    predicted_total_kwh = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class LandCover(Base):
    __tablename__ = "land_cover"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, unique=True, nullable=False, index=True)
    cover_class = Column(String(50), nullable=True)
    vegetation_pct = Column(Float, nullable=True)
    urban_pct = Column(Float, nullable=True)
    water_pct = Column(Float, nullable=True)
    barren_pct = Column(Float, nullable=True)
    ndvi = Column(Float, nullable=True)
    slope_deg = Column(Float, nullable=True)
    aspect_deg = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    analyzed_at = Column(DateTime, default=datetime.utcnow)
