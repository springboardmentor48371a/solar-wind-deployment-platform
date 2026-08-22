import sys
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import SessionLocal
from app.models.user import User
from app.models.site import Site

# Setup FastAPI test client
client = TestClient(app)

def test_full_assessment_flow():
    print("=" * 60)
    print("TESTING SITE ASSESSMENT API FLOW (ML + MATH)")
    print("=" * 60)

    # 1. Create a unique user
    import time
    timestamp = int(time.time())
    email = f"test.user_{timestamp}@solar-wind-ai.com"
    user_payload = {
        "full_name": "Test Architect",
        "email": email,
        "password": "SecretPassword123",
        "confirm_password": "SecretPassword123"
    }
    
    print(f"\n[STEP 1] Registering test user: {email}...")
    reg_response = client.post("/api/auth/register", json=user_payload)
    if reg_response.status_code != 201:
        print(f"[FAIL] Registration failed: {reg_response.text}")
        sys.exit(1)
    print(f"[SUCCESS] User registered successfully.")

    # 2. Login to retrieve JWT Token
    print("\n[STEP 2] Logging in to retrieve JWT Auth token...")
    login_payload = {"email": email, "password": "SecretPassword123"}
    login_response = client.post("/api/auth/login", json=login_payload)
    if login_response.status_code != 200:
        print(f"[FAIL] Login failed: {login_response.text}")
        sys.exit(1)
        
    token_data = login_response.json()
    token = token_data["access_token"]
    print(f"[SUCCESS] Token received: Bearer {token[:15]}...")

    # 3. Assess a candidate site (e.g. coordinates in Rajasthan)
    headers = {"Authorization": f"Bearer {token}"}
    site_payload = {
        "name": "Kurnool Solar Array Site A",
        "latitude": 15.8281,
        "longitude": 78.0373,
        "region": "Andhra Pradesh",
        "land_area": 120000.0,
        "land_ownership": "Government Lease"
    }
    
    print("\n[STEP 3] Calling /api/sites/assess with candidate site...")
    print(f"Site name: {site_payload['name']}")
    print(f"Coordinates: Lat {site_payload['latitude']}, Lon {site_payload['longitude']}")
    
    assess_response = client.post("/api/sites/assess", json=site_payload, headers=headers)
    if assess_response.status_code != 201:
        print(f"[FAIL] Assessment failed: {assess_response.text}")
        sys.exit(1)
        
    site_data = assess_response.json()
    print("[SUCCESS] Site assessed and database record created!")

    # 4. Display Results
    print("\n" + "=" * 50)
    print("AI MACHINE LEARNING PREDICTIONS")
    print("=" * 50)
    print(f" Predicted Solar Irradiance (GHI): {site_data['predicted_irradiance']} kWh/m2/day")
    print(f" Predicted Wind Speed:            {site_data['predicted_wind_speed']} m/s")
    print(f" Predicted Temperature:           {site_data['predicted_temp']} °C")
    print(f" Predicted Cloud Cover:           {site_data['predicted_cloud_cover']} %")
    print(f" Predicted Elevation:              {site_data['predicted_elevation']} m")
    print(f" Derived Land Slope:               {site_data['predicted_slope']} °")

    print("\n" + "=" * 50)
    print("DECISION ENGINE WEIGHTED SCORES")
    print("=" * 50)
    print(f" Resource Score (35% weight):      {site_data['resource_score']} / 100")
    print(f" Geographic Score (25% weight):    {site_data['geographic_score']} / 100")
    print(f" Infrastructure Score (15% wt):    {site_data['infrastructure_score']} / 100")
    print(f" Environmental Score (15% wt):    {site_data['environmental_score']} / 100")
    print(f" Economic Score (10% weight):      {site_data['economic_score']} / 100")
    print("-" * 50)
    print(f" OVERALL SUITABILITY SCORE:       {site_data['overall_score']} %")
    print(f" SUITABILITY CLASSIFICATION:       {site_data['suitability_class']}")
    print("=" * 50)

    # 5. Fetch Sites History list
    print("\n[STEP 4] Fetching history from GET /api/sites/...")
    history_response = client.get("/api/sites/", headers=headers)
    if history_response.status_code != 200:
        print(f"[FAIL] Failed to retrieve history: {history_response.text}")
        sys.exit(1)
    
    history_list = history_response.json()
    print(f"[SUCCESS] Retrieved {len(history_list)} records from your site history list.")
    print("=" * 60)

if __name__ == "__main__":
    test_full_assessment_flow()
