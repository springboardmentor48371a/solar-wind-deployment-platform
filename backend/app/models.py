from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from database import Base

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Site(Base):
    __tablename__ = "sites"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, nullable=True)
    site_name = Column(String, nullable=False) # Must match frontend!
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    elevation = Column(Float, nullable=True)
    land_area = Column(Float, nullable=True)
    land_ownership = Column(String, nullable=True)
    existing_infrastructure = Column(String, nullable=True) # Must match frontend!
    region = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)