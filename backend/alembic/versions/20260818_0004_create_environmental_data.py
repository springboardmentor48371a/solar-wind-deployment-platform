"""create environmental_data table

Revision ID: 20260818_0004
Revises: 20260817_0003
Create Date: 2026-08-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260818_0004"
down_revision: Union[str, None] = "20260817_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "environmental_data",
        sa.Column("environment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("solar_irradiance", sa.Float(), nullable=True),
        sa.Column("wind_speed", sa.Float(), nullable=True),
        sa.Column("wind_direction", sa.Float(), nullable=True),
        sa.Column("temperature", sa.Float(), nullable=True),
        sa.Column("rainfall", sa.Float(), nullable=True),
        sa.Column("humidity", sa.Float(), nullable=True),
        sa.Column("cloud_cover", sa.Float(), nullable=True),
        sa.Column("terrain_slope", sa.Float(), nullable=True),
        sa.Column("vegetation_index", sa.Float(), nullable=True),
        sa.Column("nearest_substation_distance", sa.Float(), nullable=True),
        sa.Column("road_distance", sa.Float(), nullable=True),
        sa.Column("protected_area", sa.Boolean(), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "solar_irradiance IS NULL OR solar_irradiance >= 0",
            name="ck_environmental_data_solar_irradiance_non_negative",
        ),
        sa.CheckConstraint(
            "wind_speed IS NULL OR wind_speed >= 0",
            name="ck_environmental_data_wind_speed_non_negative",
        ),
        sa.CheckConstraint(
            "wind_direction IS NULL OR (wind_direction >= 0 AND wind_direction <= 360)",
            name="ck_environmental_data_wind_direction_range",
        ),
        sa.CheckConstraint(
            "humidity IS NULL OR (humidity >= 0 AND humidity <= 100)",
            name="ck_environmental_data_humidity_range",
        ),
        sa.CheckConstraint(
            "cloud_cover IS NULL OR (cloud_cover >= 0 AND cloud_cover <= 100)",
            name="ck_environmental_data_cloud_cover_range",
        ),
        sa.CheckConstraint(
            "terrain_slope IS NULL OR terrain_slope >= 0",
            name="ck_environmental_data_terrain_slope_non_negative",
        ),
        sa.CheckConstraint(
            "vegetation_index IS NULL OR (vegetation_index >= -1 AND vegetation_index <= 1)",
            name="ck_environmental_data_vegetation_index_range",
        ),
        sa.CheckConstraint(
            "nearest_substation_distance IS NULL OR nearest_substation_distance >= 0",
            name="ck_environmental_data_substation_distance_non_negative",
        ),
        sa.CheckConstraint(
            "road_distance IS NULL OR road_distance >= 0",
            name="ck_environmental_data_road_distance_non_negative",
        ),
        sa.ForeignKeyConstraint(["site_id"], ["sites.site_id"]),
        sa.PrimaryKeyConstraint("environment_id"),
    )


def downgrade() -> None:
    op.drop_table("environmental_data")
