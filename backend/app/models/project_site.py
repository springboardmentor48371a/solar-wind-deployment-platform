from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.user import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    target_capacity_mw = Column(Float, default=100.0)
    region = Column(String, nullable=False)
    status = Column(String, default="Planning")  # Planning, Active, Completed
    timeline_cod = Column(String, default="Q4 2027")  # Deployment Timeline
    created_at = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"))

    sites = relationship("Site", back_populates="project", cascade="all, delete-orphan")

class Site(Base):
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    site_name = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    elevation_m = Column(Float, nullable=False)
    land_area_sqkm = Column(Float, nullable=False)
    region = Column(String, nullable=False)
    
    # Environmental & GIS attributes (GIS Analyst editable)
    solar_ghi = Column(Float, default=5.69)        # kWh/m²
    avg_temp = Column(Float, default=28.4)         # °C
    rainfall_mm = Column(Float, default=120.0)      # mm
    cloud_cover_pct = Column(Float, default=45.0)   # %
    slope_deg = Column(Float, default=2.1)          # Terrain slope
    vegetation_ndvi = Column(Float, default=0.18)   # Sentinel NDVI
    
    # Financial & Feasibility attributes (Planner / PM metrics)
    suitability_score = Column(Float, default=8.2) # Out of 10
    capacity_factor = Column(Float, default=24.5)  # %
    est_yield_gwh = Column(Float, default=1450.0)
    lcoe_usd_mwh = Column(Float, default=38.5)
    
    # PM Governance
    is_shortlisted = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=False)     # Final Approval by PM
    approval_notes = Column(String, nullable=True)

    land_ownership = Column(String, default="Government Lease")
    existing_infrastructure = Column(String, default="400kV Corridor within 5km")
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="sites")