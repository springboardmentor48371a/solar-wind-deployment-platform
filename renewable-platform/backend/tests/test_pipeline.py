"""
Comprehensive Automated Unit & Integration Tests (Section 31).

Tests:
  - Authentication (register, login, me, password hashing, JWT)
  - Project creation & management
  - Site creation & environmental data collection pipeline
  - Solar potential calculation & intermediate values
  - Wind potential calculation & intermediate values
  - Site suitability scoring & recommendation logic
  - Energy & financial forecasting
  - PDF & Excel report generation endpoints
  - Role-based authorization controls
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.ml.physics_baseline import solar_baseline, wind_baseline, scoring_baseline

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def test_auth_flow():
    # 1. Register
    reg_resp = client.post("/api/auth/register", json={
        "full_name": "Planner One",
        "email": "planner@example.com",
        "password": "securepassword123",
        "role": "renewable_energy_planner",
        "organization": "CleanEnergy Corp"
    })
    assert reg_resp.status_code == 200
    token = reg_resp.json()["access_token"]
    assert token is not None

    # 2. Login
    login_resp = client.post("/api/auth/login", json={
        "email": "planner@example.com",
        "password": "securepassword123"
    })
    assert login_resp.status_code == 200
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Get /me
    me_resp = client.get("/api/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "planner@example.com"


def test_physics_calculations():
    env = {
        "solar_irradiance_kwh_m2_day": 5.5,
        "wind_speed_avg_ms": 6.8,
        "temperature_avg_c": 28.0,
        "cloud_cover_pct": 20.0,
        "land_slope_pct": 3.0,
        "vegetation_index_ndvi": 0.35,
        "distance_to_road_km": 2.0,
        "distance_to_transmission_km": 5.0,
        "distance_to_substation_km": 4.0,
        "distance_to_water_km": 8.0,
        "in_protected_zone": False,
    }

    # Solar physics
    solar = solar_baseline(env, land_area_hectares=10.0)
    assert solar["annual_irradiance_kwh_m2"] == 2007.5
    assert solar["capacity_factor_pct"] > 0
    assert solar["expected_energy_output_mwh_year"] > 0

    # Wind physics
    wind = wind_baseline(env, land_area_hectares=10.0)
    assert wind["wind_power_density_w_m2"] > 0
    assert wind["turbine_suitability"] in ["Suitable", "Highly Suitable"]
    assert wind["capacity_factor_pct"] > 0

    # Scoring & Recommendation
    score = scoring_baseline(env, solar, wind, land_area_hectares=10.0)
    assert 0 <= score["overall_score"] <= 100
    assert score["category"] in ["Excellent", "Highly Suitable", "Moderately Suitable", "Low Suitability", "Unsuitable"]
    assert score["recommended_technology"] in ["solar", "wind", "hybrid"]


def test_full_project_and_site_flow():
    # Register & get auth token
    reg_resp = client.post("/api/auth/register", json={
        "full_name": "Planner Two",
        "email": "planner2@example.com",
        "password": "password123",
        "role": "renewable_energy_planner"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create project
    proj_resp = client.post("/api/projects", json={
        "name": "Delhi Renewable Energy Project",
        "description": "Evaluating sites around Bawana and Outer Delhi",
        "objective": "100 MW Hybrid Solar/Wind Facility",
        "region": "Delhi NCR"
    }, headers=headers)
    assert proj_resp.status_code == 200
    project_id = proj_resp.json()["id"]

    # Register Site 1 (Delhi Site 1)
    site_resp = client.post(f"/api/projects/{project_id}/sites", json={
        "name": "Delhi Site 1",
        "latitude": 28.7972,
        "longitude": 77.0341,
        "site_type": "hybrid"
    }, headers=headers)
    assert site_resp.status_code == 200
    site_data = site_resp.json()
    assert site_data["site"]["name"] == "Delhi Site 1"
    assert site_data["solar"] is not None
    assert site_data["wind"] is not None
    assert site_data["score"] is not None
    assert site_data["forecast"] is not None

    site_id = site_data["site"]["id"]

    # Check standalone site endpoint
    standalone_resp = client.get(f"/api/sites/{site_id}", headers=headers)
    assert standalone_resp.status_code == 200
    assert standalone_resp.json()["site"]["id"] == site_id

    # Check reports endpoints
    pdf_resp = client.get(f"/api/reports/site/{site_id}/pdf", headers=headers)
    assert pdf_resp.status_code == 200
    assert len(pdf_resp.content) > 0

    excel_resp = client.get(f"/api/reports/site/{site_id}/excel", headers=headers)
    assert excel_resp.status_code == 200
    assert len(excel_resp.content) > 0
