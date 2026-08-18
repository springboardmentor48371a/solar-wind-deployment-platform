from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def ensure_postgis_extension() -> None:
    """
    Enables the PostGIS extension on the target database, if the database
    is PostgreSQL. No-op (and safe to call) for SQLite dev databases.
    Requires the connecting role to have CREATE privileges, or for a
    superuser to have already run `CREATE EXTENSION postgis;` once.
    """
    if not settings.database_url.startswith("postgresql"):
        return
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
            conn.commit()
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: could not ensure PostGIS extension is enabled: {exc}")


def ensure_timescaledb() -> None:
    """
    Enables the TimescaleDB extension and converts the platform's two
    genuine time-series tables (weather_readings, telemetry_readings —
    both append-only, both queried by time range) into hypertables.

    Best-effort and fully optional, same pattern as ensure_postgis_extension:
    a plain Postgres or a Postgres without the timescaledb extension
    installed just logs a warning and the app keeps running against
    ordinary Postgres tables. Must run *after* Base.metadata.create_all,
    since create_hypertable requires the target table to already exist.
    """
    if not settings.database_url.startswith("postgresql"):
        return
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb"))
            conn.commit()
            for table, time_col in (
                ("weather_readings", "reading_date"),
                ("telemetry_readings", "recorded_at"),
            ):
                try:
                    conn.execute(
                        text(
                            f"SELECT create_hypertable('{table}', '{time_col}', "
                            "if_not_exists => TRUE, migrate_data => TRUE)"
                        )
                    )
                    conn.commit()
                except Exception as exc:  # noqa: BLE001
                    conn.rollback()
                    print(f"Warning: could not create hypertable for {table}: {exc}")
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: TimescaleDB extension unavailable, using plain Postgres tables: {exc}")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
