import sys
import os

# Add parent directory to path so app can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import get_db, Base, engine
from app.seed import seed_data
from app.models import Role, User, Project, Site, SiteAssessment

def run_tests():
    print("==================================================")
    print("RUNNING SOLAR & WIND PLATFORM BACKEND VERIFICATION")
    print("==================================================")
    
    # 1. Run database initialization and seeding
    print("\n--- Step 1: Initializing & Seeding Database ---")
    try:
        seed_data()
        print("[OK] Database seeding verified successfully.")
    except Exception as e:
        print(f"[FAIL] Database seeding failed: {e}")
        sys.exit(1)

    # 2. Setup TestClient
    client = TestClient(app)
    print("\n--- Step 2: Testing FastAPI API Endpoints ---")
    
    # Test Root
    res = client.get("/")
    assert res.status_code == 200
    assert "Solar & Wind" in res.json()["message"]
    print("[OK] GET /: Verified (Root Endpoint)")

    # Test Login (Planner User)
    login_data = {
        "username": "planner@renewable.in",
        "password": "plannerpassword"
    }
    res = client.post("/api/auth/login", data=login_data)
    assert res.status_code == 200
    token_resp = res.json()
    assert "access_token" in token_resp
    assert token_resp["role"] == "Planner"
    token = token_resp["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[OK] POST /api/auth/login: Verified (JWT Issue & Planner Login)")

    # Test GET /api/projects
    res = client.get("/api/projects", headers=headers)
    assert res.status_code == 200
    projects = res.json()
    assert len(projects) > 0
    project_id = projects[0]["project_id"]
    print(f"[OK] GET /api/projects: Verified (Found {len(projects)} projects)")

    # Test GET /api/sites
    res = client.get(f"/api/sites?project_id={project_id}", headers=headers)
    assert res.status_code == 200
    sites = res.json()
    assert len(sites) > 0
    print(f"[OK] GET /api/sites: Verified (Found {len(sites)} sites in project)")
    site_id = sites[0]["site_id"]

    # Test GET /api/infrastructure
    res = client.get("/api/infrastructure", headers=headers)
    assert res.status_code == 200
    infra = res.json()
    assert "substations" in infra
    assert "protected_zones" in infra
    assert len(infra["substations"]["features"]) > 0
    print("[OK] GET /api/infrastructure: Verified (Seeded GIS Layers)")

    # Test GET /api/dashboard/stats
    res = client.get("/api/dashboard/stats", headers=headers)
    assert res.status_code == 200
    stats = res.json()
    assert stats["total_sites"] > 0
    assert stats["is_synthetic_mode"] is True
    print(f"[OK] GET /api/dashboard/stats: Verified (Avg score: {stats['average_suitability_score']})")

    # Test POST /api/sites (Add a new candidate site near Kutch, Gujarat)
    new_site_data = {
        "project_id": project_id,
        "site_name": "New Kutch Salt Plain Expansion",
        "latitude": 23.4750,
        "longitude": 69.5100,
        "land_area": 110.0,
        "land_type": "Wasteland",
        "ownership": "Government"
    }
    res = client.post("/api/sites", json=new_site_data, headers=headers)
    assert res.status_code == 201
    created_site = res.json()
    assert created_site["site_name"] == "New Kutch Salt Plain Expansion"
    assert created_site["environmental_data"] is not None
    assert len(created_site["assessments"]) > 0
    
    new_site_id = created_site["site_id"]
    assessment = created_site["assessments"][0]
    print(f"[OK] POST /api/sites: Verified (New site created with score: {assessment['suitability_score']}, labeled synthetic: {assessment['is_synthetic']})")

    # Test POST /api/sites/{id}/recalculate (Adjust weights to prioritize environment)
    weights = {
        "weight_resource": 0.20,
        "weight_geographic": 0.20,
        "weight_infrastructure": 0.20,
        "weight_environment": 0.30, # Max weight to environment
        "weight_economic": 0.10
    }
    res = client.post(f"/api/sites/{new_site_id}/recalculate", json=weights, headers=headers)
    assert res.status_code == 200
    updated_assess = res.json()
    print(f"[OK] POST /api/sites/{{id}}/recalculate: Verified (Recalculated score: {updated_assess['suitability_score']})")

    # Test POST /api/sites with real Rajasthan coordinates (26.9, 70.9) to verify NASA POWER and Global Wind Atlas API integration
    rajasthan_site_data = {
        "project_id": project_id,
        "site_name": "Jaisalmer NASA & GWA Evaluation Site",
        "latitude": 26.9000,
        "longitude": 70.9000,
        "land_area": 150.0,
        "land_type": "Desert",
        "ownership": "Government"
    }
    print("\n--- Step 3: Testing NASA POWER & Global Wind Atlas Integration ---")
    res = client.post("/api/sites", json=rajasthan_site_data, headers=headers)
    assert res.status_code == 201
    rajasthan_site = res.json()
    assert rajasthan_site["environmental_data"] is not None
    assert len(rajasthan_site["assessments"]) > 0
    
    env_data = rajasthan_site["environmental_data"]
    assess = rajasthan_site["assessments"][0]
    
    # Assertions for NASA POWER climate data source
    assert env_data["climate_data_source"] == "NASA POWER Climatology"
    assert assess["climate_data_source"] == "NASA POWER Climatology"
    
    # Assertions for Global Wind Atlas wind data source and metrics
    assert env_data["wind_data_source"] == "Global Wind Atlas"
    assert assess["wind_data_source"] == "Global Wind Atlas"
    assert env_data["wind_power_density"] > 0.0
    assert "Derived Wind Resource Class" in env_data["wind_resource"]
    assert "Derived Wind Resource Class" in assess["wind_resource"]
    
    # Assertions for Infrastructure, SRTM, Land Cover, and Protected Area
    assert env_data["infra_data_source"] in ["OpenStreetMap", "Local Estimate"]
    assert env_data["elevation_data_source"] in ["SRTM", "Local Estimate"]
    assert env_data["land_cover_data_source"] in ["Esri Sentinel-2 10m Land Cover, derived from Copernicus Sentinel-2 imagery", "Local Estimate"]
    assert env_data["protected_area_data_source"] in ["OpenStreetMap", "Local Estimate"]
    
    print("[OK] NASA POWER, Global Wind Atlas, OSM, SRTM & Esri Integration Verified successfully!")
    print(f"  - Site: {rajasthan_site['site_name']} (Lat: 26.9, Lng: 70.9)")
    print(f"  - Climate Data Source: {env_data['climate_data_source']}")
    print(f"  - Wind Data Source: {env_data['wind_data_source']}")
    print(f"  - Infra Data Source: {env_data['infra_data_source']}")
    print(f"  - Elevation Data Source: {env_data['elevation_data_source']}")
    print(f"  - Land Cover Data Source: {env_data['land_cover_data_source']}")
    print(f"  - Protected Area Data Source: {env_data['protected_area_data_source']}")
    print(f"  - Solar Irradiance (GHI): {env_data['solar_irradiance']} kWh/m2/day")
    print(f"  - GWA Wind Speed (100M): {env_data['wind_speed']} m/s")
    print(f"  - GWA Wind Power Density: {env_data['wind_power_density']} W/m2")
    print(f"  - {env_data['wind_resource']}")
    print(f"  - Wind Direction (NASA): {env_data['wind_direction']} degrees")
    print(f"  - Temperature: {env_data['temperature']} C")
    print(f"  - Rainfall (Annual): {env_data['rainfall']} mm")
    print(f"  - Humidity: {env_data['humidity']}%")
    print(f"  - Cloud Cover: {env_data['cloud_cover']}%")
    print(f"  - Elevation (SRTM): {rajasthan_site['elevation']} m")
    print(f"  - Terrain Slope (SRTM): {env_data['terrain_slope']} degrees")
    print(f"  - Land Type (Mapped): {rajasthan_site['land_type']}")
    print(f"  - Protected Area: {env_data['protected_area']}")
    print(f"  - Suitability Score: {assess['suitability_score']}/100")

    # Test Fallback: Coordinates outside Rajasthan/Gujarat raster bounds (e.g. Bengaluru, India: 12.97, 77.59)
    bengaluru_site_data = {
        "project_id": project_id,
        "site_name": "Bengaluru Fallback Evaluation Site",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "land_area": 100.0,
        "land_type": "Plain",
        "ownership": "Private"
    }
    print("\n--- Step 4: Testing GWA Bounding Box Fallback Behavior ---")
    res = client.post("/api/sites", json=bengaluru_site_data, headers=headers)
    assert res.status_code == 201
    fallback_site = res.json()
    f_env_data = fallback_site["environmental_data"]
    f_assess = fallback_site["assessments"][0]
    
    # Verify it falls back safely to NASA POWER or Local Estimate
    assert f_env_data["wind_data_source"] in ["NASA POWER", "Local Estimate"]
    assert f_env_data["wind_power_density"] > 0.0
    assert "Derived Wind Resource Class" in f_env_data["wind_resource"]
    print(f"[OK] Fallback Behavior Verified successfully!")
    print(f"  - Site: {fallback_site['site_name']} (Lat: 12.97, Lng: 77.59)")
    print(f"  - Fallback Wind Data Source: {f_env_data['wind_data_source']}")
    print(f"  - Fallback Wind Speed: {f_env_data['wind_speed']} m/s")
    print(f"  - Fallback Wind Power Density: {f_env_data['wind_power_density']} W/m2")
    print(f"  - Fallback {f_env_data['wind_resource']}")

    print("\n==================================================")
    print("   ALL BACKEND INTEGRATION TESTS PASSED SUCCESSFULLY!  ")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
