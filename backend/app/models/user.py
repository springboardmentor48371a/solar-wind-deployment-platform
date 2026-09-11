from enum import Enum
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./solar_wind.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class UserRole(str, Enum):
    PLANNER = "Renewable Energy Planner"
    GIS_ANALYST = "GIS Analyst"
    PROJECT_MANAGER = "Project Manager"
    ADMIN = "Administrator"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default=UserRole.PLANNER.value)
    organization = Column(String, default="National Renewable Energy Grid")
    department = Column(String, default="Geospatial Planning Division")
    phone = Column(String, default="+1-555-0199")
    bio = Column(String, default="Renewable energy deployment specialist.")
    is_active = Column(Boolean, default=True)

Base.metadata.create_all(bind=engine)