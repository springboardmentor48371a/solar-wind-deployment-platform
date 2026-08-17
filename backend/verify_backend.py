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

    print("\n==================================================")
    print("   ALL BACKEND INTEGRATION TESTS PASSED SUCCESSFULLY!  ")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
