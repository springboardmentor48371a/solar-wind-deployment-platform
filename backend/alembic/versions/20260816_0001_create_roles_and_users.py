"""create roles and users tables

Revision ID: 20260816_0001
Revises:
Create Date: 2026-08-16
"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260816_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


roles_table = sa.table(
    "roles",
    sa.column("role_id", postgresql.UUID(as_uuid=True)),
    sa.column("role_name", sa.String(length=50)),
    sa.column("description", sa.Text()),
)


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("role_id"),
    )

    op.create_table(
        "users",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("full_name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=150), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("phone_number", sa.String(length=20), nullable=True),
        sa.Column("organization", sa.String(length=150), nullable=True),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "account_status",
            sa.String(length=20),
            server_default="active",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "account_status IN ('active', 'inactive')",
            name="ck_users_account_status",
        ),
        sa.ForeignKeyConstraint(["role_id"], ["roles.role_id"]),
        sa.PrimaryKeyConstraint("user_id"),
        sa.UniqueConstraint("email"),
    )

    op.bulk_insert(
        roles_table,
        [
            {
                "role_id": uuid.UUID("5d26d31c-0f17-4ff5-9ff7-0a79d7729f8b"),
                "role_name": "Planner",
                "description": "Plans renewable energy deployment projects.",
            },
            {
                "role_id": uuid.UUID("d6310ee8-18cf-4f06-aafe-942f11e5c412"),
                "role_name": "GIS Analyst",
                "description": "Analyzes geospatial and environmental site data.",
            },
            {
                "role_id": uuid.UUID("767c13f9-8cef-4837-9fa2-b8d7ad0f86b0"),
                "role_name": "Project Manager",
                "description": "Manages project delivery and coordination.",
            },
            {
                "role_id": uuid.UUID("dd29f934-53f4-4825-a19b-fc19cdd01707"),
                "role_name": "Admin",
                "description": "Administers platform users and settings.",
            },
        ],
    )


def downgrade() -> None:
    op.drop_table("users")
    op.drop_table("roles")
