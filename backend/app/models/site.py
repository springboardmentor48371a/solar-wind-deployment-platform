import uuid

from sqlalchemy import CheckConstraint, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Site(Base):
    __tablename__ = "sites"
    __table_args__ = (
        CheckConstraint(
            "latitude >= -90 AND latitude <= 90",
            name="ck_sites_latitude_range",
        ),
        CheckConstraint(
            "longitude >= -180 AND longitude <= 180",
            name="ck_sites_longitude_range",
        ),
        CheckConstraint(
            "land_area IS NULL OR land_area >= 0",
            name="ck_sites_land_area_non_negative",
        ),
    )

    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.project_id"),
        nullable=False,
    )
    site_name: Mapped[str] = mapped_column(String(150), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    land_area: Mapped[float | None] = mapped_column(Float, nullable=True)
    elevation: Mapped[float | None] = mapped_column(Float, nullable=True)
    land_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ownership: Mapped[str | None] = mapped_column(String(100), nullable=True)

    project = relationship("Project", back_populates="sites")
    environmental_data = relationship(
        "EnvironmentalData",
        back_populates="site",
        cascade="all, delete-orphan",
    )
