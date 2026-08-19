from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime, timezone
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="Renewable Energy Planner")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Site(Base):
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    region = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    long = Column(Float, nullable=False)
    site_type = Column(String, default="Hybrid (Solar + Wind)")
    area = Column(String, nullable=True)
    solar_potential = Column(String, nullable=True)
    wind_speed = Column(String, nullable=True)
    grid_proximity = Column(String, nullable=True)
    elevation = Column(String, nullable=True)
    suitability_score = Column(Integer, default=85)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))