from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base

class SuitabilityScore(Base):
    __tablename__ = "suitability_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), unique=True)
    
    renewable_resource_score = Column(Float)
    geographic_suitability_score = Column(Float)
    infrastructure_accessibility_score = Column(Float)
    environmental_impact_score = Column(Float)
    economic_feasibility_score = Column(Float)
    overall_score = Column(Float)
    category = Column(String(50))
    recommendations = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    site = relationship("Site", back_populates="suitability_score")