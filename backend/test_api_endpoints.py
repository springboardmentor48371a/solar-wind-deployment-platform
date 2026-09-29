import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_login_and_auth_me():
    login_resp = client.post(
        "/api/v1/auth/login-json",
        json={"email": "planner@example.com", "password": "Planner123!"}
    )
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    token = token_data["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    user_info = me_resp.json()
    assert user_info["email"] == "planner@example.com"
    assert user_info["role"]["name"] == "Renewable Energy Planner"


def test_projects_and_sites_api():
    login_resp = client.post(
        "/api/v1/auth/login-json",
        json={"email": "planner@example.com", "password": "Planner123!"}
    )
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}
    
    projects_resp = client.get("/api/v1/projects", headers=headers)
    assert projects_resp.status_code == 200
    projects = projects_resp.json()
    assert len(projects) >= 4
    
    sites_resp = client.get("/api/v1/sites", headers=headers)
    assert sites_resp.status_code == 200
    sites = sites_resp.json()
    assert len(sites) >= 5


def test_solar_prediction_endpoint():
    login_resp = client.post(
        "/api/v1/auth/login-json",
        json={"email": "planner@example.com", "password": "Planner123!"}
    )
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}
    
    payload = {
        "site_id": 1,
        "model_type": "gradient_boosting"
    }
    resp = client.post("/api/v1/solar/predict", json=payload, headers=headers)
    assert resp.status_code == 200
    result = resp.json()
    assert result["expected_mwh_year"] > 0
    assert result["capacity_factor"] > 0
    assert "model_name" in result


def test_wind_prediction_endpoint():
    login_resp = client.post(
        "/api/v1/auth/login-json",
        json={"email": "planner@example.com", "password": "Planner123!"}
    )
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}
    
    payload = {
        "site_id": 2,
        "model_type": "gradient_boosting"
    }
    resp = client.post("/api/v1/wind/predict", json=payload, headers=headers)
    assert resp.status_code == 200
    result = resp.json()
    assert result["expected_mwh_year"] > 0
    assert result["capacity_factor"] > 0
    assert "model_name" in result


def test_suitability_endpoint():
    login_resp = client.post(
        "/api/v1/auth/login-json",
        json={"email": "planner@example.com", "password": "Planner123!"}
    )
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}
    
    payload = {
        "site_id": 1,
        "technology": "solar",
        "custom_weights": {
            "resource_quality": 35.0,
            "terrain_slope": 25.0,
            "grid_proximity": 15.0,
            "land_cover": 15.0,
            "road_access": 10.0
        }
    }
    resp = client.post("/api/v1/suitability/calculate", json=payload, headers=headers)
    assert resp.status_code == 200
    res = resp.json()
    assert 0 <= res["overall_score"] <= 100
    assert res["category"] in ["Highly Suitable", "Suitable", "Moderate", "Unsuitable"]


def test_reports_endpoints():
    login_resp = client.post(
        "/api/v1/auth/login-json",
        json={"email": "planner@example.com", "password": "Planner123!"}
    )
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}
    
    pdf_resp = client.post(
        "/api/v1/reports/site",
        json={"site_id": 1, "format": "pdf"},
        headers=headers
    )
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert len(pdf_resp.content) > 1000

    excel_resp = client.post(
        "/api/v1/reports/site",
        json={"site_id": 1, "format": "excel"},
        headers=headers
    )
    assert excel_resp.status_code == 200
    assert "openxmlformats" in excel_resp.headers["content-type"]
    assert len(excel_resp.content) > 1000
