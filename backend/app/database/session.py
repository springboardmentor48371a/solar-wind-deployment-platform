import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

def get_engine():
    db_url = settings.DATABASE_URL
    try:
        if db_url.startswith("sqlite"):
            return create_engine(db_url, connect_args={"check_same_thread": False})
        else:
            # Test engine initialization for PostgreSQL
            engine = create_engine(db_url, pool_pre_ping=True)
            # Verify connection works or fallback gracefully for local standalone dev testing
            with engine.connect() as conn:
                pass
            return engine
    except Exception as e:
        logger.warning(f"Could not connect to primary DB at {db_url}: {e}. Falling back to local SQLite DB.")
        fallback_url = "sqlite:///./solar_wind_fallback.db"
        return create_engine(fallback_url, connect_args={"check_same_thread": False})

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
