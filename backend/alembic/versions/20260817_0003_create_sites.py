"""create sites table

Revision ID: 20260817_0003
Revises: 20260817_0002
Create Date: 2026-08-17
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260817_0003"
down_revision: Union[str, None] = "20260817_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sites",
        sa.Column("site_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("site_name", sa.String(length=150), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("region", sa.String(length=100), nullable=True),
        sa.Column("land_area", sa.Float(), nullable=True),
        sa.Column("elevation", sa.Float(), nullable=True),
        sa.Column("land_type", sa.String(length=100), nullable=True),
        sa.Column("ownership", sa.String(length=100), nullable=True),
        sa.CheckConstraint(
            "latitude >= -90 AND latitude <= 90",
            name="ck_sites_latitude_range",
        ),
        sa.CheckConstraint(
            "longitude >= -180 AND longitude <= 180",
            name="ck_sites_longitude_range",
        ),
        sa.CheckConstraint(
            "land_area IS NULL OR land_area >= 0",
            name="ck_sites_land_area_non_negative",
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.project_id"]),
        sa.PrimaryKeyConstraint("site_id"),
    )


def downgrade() -> None:
    op.drop_table("sites")
