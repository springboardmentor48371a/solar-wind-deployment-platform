import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, ForeignKey
from app.database.session import Base
from app.models.user import GUID

class Site(Base):
    __tablename__ = "sites"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    region = Column(String(100), nullable=False)
    land_area = Column(Float, nullable=False)
    land_ownership = Column(String(100), nullable=False)

    # Predicted Variables from ML
    predicted_irradiance = Column(Float, nullable=False)
    predicted_wind_speed = Column(Float, nullable=False)
    predicted_temp = Column(Float, nullable=False)
    predicted_cloud_cover = Column(Float, nullable=False)
    predicted_elevation = Column(Float, nullable=False)
    predicted_slope = Column(Float, nullable=False)

    # Suitability scoring breakdown
    resource_score = Column(Float, nullable=False)
    geographic_score = Column(Float, nullable=False)
    infrastructure_score = Column(Float, nullable=False)
    environmental_score = Column(Float, nullable=False)
    economic_score = Column(Float, nullable=False)
    overall_score = Column(Float, nullable=False)
    suitability_class = Column(String(50), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Site(id={self.id}, name={self.name}, overall_score={self.overall_score})>"
