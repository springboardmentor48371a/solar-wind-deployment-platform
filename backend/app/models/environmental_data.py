import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EnvironmentalData(Base):
    __tablename__ = "environmental_data"
    __table_args__ = (
        CheckConstraint(
            "solar_irradiance IS NULL OR solar_irradiance >= 0",
            name="ck_environmental_data_solar_irradiance_non_negative",
        ),
        CheckConstraint(
            "wind_speed IS NULL OR wind_speed >= 0",
            name="ck_environmental_data_wind_speed_non_negative",
        ),
        CheckConstraint(
            "wind_direction IS NULL OR (wind_direction >= 0 AND wind_direction <= 360)",
            name="ck_environmental_data_wind_direction_range",
        ),
        CheckConstraint(
            "humidity IS NULL OR (humidity >= 0 AND humidity <= 100)",
            name="ck_environmental_data_humidity_range",
        ),
        CheckConstraint(
            "cloud_cover IS NULL OR (cloud_cover >= 0 AND cloud_cover <= 100)",
            name="ck_environmental_data_cloud_cover_range",
        ),
        CheckConstraint(
            "terrain_slope IS NULL OR terrain_slope >= 0",
            name="ck_environmental_data_terrain_slope_non_negative",
        ),
        CheckConstraint(
            "vegetation_index IS NULL OR (vegetation_index >= -1 AND vegetation_index <= 1)",
            name="ck_environmental_data_vegetation_index_range",
        ),
        CheckConstraint(
            "nearest_substation_distance IS NULL OR nearest_substation_distance >= 0",
            name="ck_environmental_data_substation_distance_non_negative",
        ),
        CheckConstraint(
            "road_distance IS NULL OR road_distance >= 0",
            name="ck_environmental_data_road_distance_non_negative",
        ),
    )

    environment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sites.site_id"),
        nullable=False,
    )
    solar_irradiance: Mapped[float | None] = mapped_column(Float, nullable=True)
    wind_speed: Mapped[float | None] = mapped_column(Float, nullable=True)
    wind_direction: Mapped[float | None] = mapped_column(Float, nullable=True)
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    rainfall: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity: Mapped[float | None] = mapped_column(Float, nullable=True)
    cloud_cover: Mapped[float | None] = mapped_column(Float, nullable=True)
    terrain_slope: Mapped[float | None] = mapped_column(Float, nullable=True)
    vegetation_index: Mapped[float | None] = mapped_column(Float, nullable=True)
    nearest_substation_distance: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    road_distance: Mapped[float | None] = mapped_column(Float, nullable=True)
    protected_area: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    site = relationship("Site", back_populates="environmental_data")
