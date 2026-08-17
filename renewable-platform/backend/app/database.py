"""
Database configuration.

Uses SQLite by default so the project runs out of the box with zero setup.
For production, set DATABASE_URL to a PostgreSQL + PostGIS connection string,
e.g. postgresql://user:pass@localhost:5432/renewable_platform
(the spec's target primary database is PostgreSQL/PostGIS; SQLAlchemy models
here use plain lat/lon float columns so they work unmodified on either).
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./renewable_platform.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
