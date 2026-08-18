import os
import sqlite3
import uuid
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite:///./solarwind.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()

DEFAULT_ROLES = [
    ("Renewable Energy Planner", "Plans renewable energy projects"),
    ("GIS Analyst", "Performs spatial and GIS analysis"),
    ("Project Manager", "Manages project execution and delivery"),
    ("Administrator", "Manages platform users and settings"),
]


def ensure_user_columns():
    if DATABASE_URL.startswith("sqlite"):
        db_path = Path(__file__).resolve().with_name("solarwind.db")
        if not db_path.exists():
            return

        conn = sqlite3.connect(db_path)
        try:
            columns = conn.execute("PRAGMA table_info(users)").fetchall()
            existing_columns = {column[1] for column in columns}

            if "role" not in existing_columns:
                conn.execute("ALTER TABLE users ADD COLUMN role VARCHAR(50) NOT NULL DEFAULT 'Renewable Energy Planner'")
            if "organization" not in existing_columns:
                conn.execute("ALTER TABLE users ADD COLUMN organization VARCHAR(150)")
            if "role_id" not in existing_columns:
                conn.execute("ALTER TABLE users ADD COLUMN role_id TEXT")
            if "phone_number" not in existing_columns:
                conn.execute("ALTER TABLE users ADD COLUMN phone_number VARCHAR(20)")
            if "account_status" not in existing_columns:
                conn.execute("ALTER TABLE users ADD COLUMN account_status VARCHAR(20) DEFAULT 'Active'")
            if "updated_at" not in existing_columns:
                conn.execute("ALTER TABLE users ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP")

            conn.commit()
        finally:
            conn.close()
        return

    with engine.begin() as conn:
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'users'"))
        existing_columns = {row[0] for row in result.fetchall()}

        if "role" not in existing_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(50) NOT NULL DEFAULT 'Renewable Energy Planner'"))
        if "organization" not in existing_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN organization VARCHAR(150)"))
        if "role_id" not in existing_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN role_id UUID"))
        if "phone_number" not in existing_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN phone_number VARCHAR(20)"))
        if "account_status" not in existing_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN account_status VARCHAR(20) DEFAULT 'Active'"))
        if "updated_at" not in existing_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))


def ensure_default_roles():
    with engine.begin() as conn:
        for role_name, description in DEFAULT_ROLES:
            conn.execute(
                text(
                    """
                    INSERT INTO roles (role_id, role_name, description, created_at)
                    VALUES (:role_id, :role_name, :description, CURRENT_TIMESTAMP)
                    ON CONFLICT (role_name) DO NOTHING
                    """
                ),
                {
                    "role_id": str(uuid.uuid4()),
                    "role_name": role_name,
                    "description": description,
                },
            )
