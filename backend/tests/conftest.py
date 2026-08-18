"""
Shared pytest fixtures.

Every test runs against a fresh, isolated SQLite database (file-based, one
per test, deleted after) rather than the real Postgres/Mongo/Redis the app
uses in production. That's a deliberate trade-off: SQLite doesn't speak
PostGIS, so `Site.geom` is exercised as a plain nullable column, not real
geometry — anything that specifically needs PostGIS operators belongs in
a separate integration test run against the real docker-compose stack,
not here. What SQLite *does* let us verify, fast and with zero external
services, is everything that matters most for correctness: auth, RBAC/
IDOR protection, request validation, and the suitability scoring math.

External services (NASA POWER, Overpass, elevation, Mongo, Redis) are
never called in this suite — nothing here exercises app/services/
environmental.py's or infrastructure.py's live HTTP calls, since doing so
would make tests flaky and dependent on the internet being up. Redis/Mongo
being unreachable during tests is fine and expected: app/cache.py and
app/mongo.py are both designed to degrade gracefully rather than error.
"""

import os
import uuid

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("STAFF_PIN", "1248")
# Generous rate limits for tests — the point of these tests is business
# logic, not re-proving slowapi works. Rate limiting itself is exercised
# in test_security.py with its own tight, explicit limit.
os.environ.setdefault("RATE_LIMIT_DEFAULT", "10000/minute")
os.environ.setdefault("RATE_LIMIT_AUTH", "10000/minute")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_swdip.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6399/0")  # deliberately unused port

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app import models

TEST_DB_PATH = "./test_swdip.db"
engine = create_engine(f"sqlite:///{TEST_DB_PATH}", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function", autouse=True)
def _fresh_database():
    """Recreate all tables before each test, drop them after. Keeps every
    test's data fully isolated without needing per-test transactions."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def _stub_external_connectors(monkeypatch):
    """
    Site creation/analysis triggers real HTTP calls out to NASA POWER,
    Overpass, and the elevation API (see routers/sites.py). Tests must not
    depend on those third-party services being reachable or fast, so every
    test transparently gets fixed, deterministic stand-ins instead. This
    keeps the suite hermetic (no network needed) and fast, and is *why* a
    site created in these tests always ends up with elevation=250m,
    slope=3.5%, one weather reading, and one substation 4.2km away.
    """
    from app.services import terrain, infrastructure, environmental, satellite, land_data, solar_engine, wind_engine, supplemental_weather

    monkeypatch.setattr(terrain, "fetch_elevation", lambda lat, lon: 250.0)
    monkeypatch.setattr(terrain, "estimate_slope_pct", lambda lat, lon, delta_deg=0.001: 3.5)

    def _fake_weather(db, site, days_back=7):
        existing = (
            db.query(models.WeatherReading)
            .filter(models.WeatherReading.site_id == site.id)
            .first()
        )
        if existing:
            return 0
        import datetime as _dt

        db.add(
            models.WeatherReading(
                site_id=site.id,
                reading_date=_dt.datetime.utcnow(),
                solar_irradiance=5.8,
                wind_speed=4.1,
                wind_speed_50m=6.9,
                temperature=27.0,
                rainfall=1.2,
                cloud_cover_pct=30.0,
            )
        )
        db.commit()
        return 1

    def _fake_infrastructure(db, site):
        db.query(models.InfrastructureFeature).filter(
            models.InfrastructureFeature.site_id == site.id
        ).delete()
        db.add(
            models.InfrastructureFeature(
                site_id=site.id, feature_type="substation", name="Test Substation", distance_km=4.2
            )
        )
        db.commit()

    monkeypatch.setattr(environmental, "fetch_and_store_weather_data", _fake_weather)
    monkeypatch.setattr(infrastructure, "fetch_and_store_infrastructure", _fake_infrastructure)

    # Satellite / environmental-constraints / solar / wind engines all make
    # real outbound HTTP calls too (Sentinel Hub, Overpass, World Bank).
    # Same hermetic-test philosophy: deterministic in-memory stand-ins, no
    # network. compute_solar_potential/compute_wind_potential are largely
    # pure math over WeatherReading/Site data already in the (test) DB, so
    # those two are left real — only their own internal network calls (none)
    # need stubbing, i.e. nothing to do there. satellite/land_data *do*
    # make live HTTP calls internally, so those get fake stand-ins.
    def _fake_satellite(db, site):
        db.query(models.SiteImage).filter(models.SiteImage.site_id == site.id).delete()
        image = models.SiteImage(
            site_id=site.id,
            provider="Copernicus Sentinel-2 (test stub)",
            cloud_cover_pct=12.0,
            ndvi_mean=0.35,
            land_cover_summary="Sparse vegetation / bare soil",
            source_status="ok",
        )
        db.add(image)
        db.commit()
        db.refresh(image)
        return image

    def _fake_environmental_constraints(db, site):
        db.query(models.EnvironmentalConstraint).filter(
            models.EnvironmentalConstraint.site_id == site.id
        ).delete()
        record = models.EnvironmentalConstraint(
            site_id=site.id,
            protected_area_distance_km=8.5,
            water_body_distance_km=2.1,
            agricultural_land_nearby=1,
            urban_area_distance_km=5.0,
            country_iso3="IND",
            population_density_km2=450.0,
            gdp_per_capita_usd=2400.0,
            data_source="OpenStreetMap (Overpass) + World Bank Open Data (test stub)",
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    monkeypatch.setattr(satellite, "fetch_and_store_satellite_summary", _fake_satellite)
    monkeypatch.setattr(land_data, "fetch_and_store_environmental_constraints", _fake_environmental_constraints)

    def _fake_supplemental_weather(db, site):
        return []  # no OPENWEATHER_API_KEY / non-US coords in tests — empty is the correct real behavior

    monkeypatch.setattr(supplemental_weather, "fetch_and_store_supplemental_weather", _fake_supplemental_weather)

    # sites.py imported these names directly (`from ... import fetch_elevation`),
    # so the router module's own references must be patched too, not just
    # the source module's.
    from app.routers import sites as sites_router

    monkeypatch.setattr(sites_router, "fetch_elevation", lambda lat, lon: 250.0)
    monkeypatch.setattr(sites_router, "estimate_slope_pct", lambda lat, lon, delta_deg=0.001: 3.5)
    monkeypatch.setattr(sites_router, "fetch_and_store_weather_data", _fake_weather)
    monkeypatch.setattr(sites_router, "fetch_and_store_infrastructure", _fake_infrastructure)
    monkeypatch.setattr(sites_router, "fetch_and_store_satellite_summary", _fake_satellite)
    monkeypatch.setattr(sites_router, "fetch_and_store_environmental_constraints", _fake_environmental_constraints)
    monkeypatch.setattr(sites_router, "fetch_and_store_supplemental_weather", _fake_supplemental_weather)


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def db_session_factory():
    """For tests that want a raw SQLAlchemy Session against the same test
    database, bypassing the HTTP layer entirely (pure service-function
    unit tests, e.g. test_suitability_scoring.py)."""
    return TestingSessionLocal


def _unique_email(prefix: str) -> str:
    return f"{prefix}.{uuid.uuid4().hex[:10]}@example.com"


def register_and_login(client: TestClient, role: str, pin: str | None = None, password: str = "Str0ngPass!"):
    email = _unique_email(role.lower().replace(" ", "").replace("/", ""))
    payload = {
        "full_name": f"Test {role}",
        "email": email,
        "password": password,
        "role": role,
    }
    if pin:
        payload["pin"] = pin
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 201, resp.text

    login_data = {"username": email, "password": password}
    if pin:
        login_data["pin"] = pin
    login_resp = client.post("/auth/login", data=login_data)
    assert login_resp.status_code == 200, login_resp.text
    tokens = login_resp.json()
    return {"email": email, "access_token": tokens["access_token"], "id": resp.json()["id"]}


@pytest.fixture()
def planner(client):
    return register_and_login(client, "Renewable Energy Planner")


@pytest.fixture()
def second_planner(client):
    return register_and_login(client, "Renewable Energy Planner")


@pytest.fixture()
def gis_analyst(client):
    return register_and_login(client, "GIS Analyst", pin="1248")


@pytest.fixture()
def project_manager(client):
    return register_and_login(client, "Project Manager", pin="1248")


@pytest.fixture()
def admin(client):
    return register_and_login(client, "Administrator", pin="1248")


def auth_headers(user: dict) -> dict:
    return {"Authorization": f"Bearer {user['access_token']}"}
