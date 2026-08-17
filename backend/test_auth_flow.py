import sys
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import SessionLocal
from app.models.user import User

client = TestClient(app)

def test_full_auth_workflow():
    print("=" * 60)
    print("STARTING COMPLETE AUTHENTICATION WORKFLOW VERIFICATION")
    print("=" * 60)

    import time
    test_email = f"test.engineer_{int(time.time())}@solar-wind-ai.com"
    test_password = "SecurePassword123!"
    test_name = "Dr. Elena Vance"

    # Step 1: Register a new user
    print("\n[TEST 1/10] Testing User Registration Endpoint (POST /api/auth/register)...")
    reg_payload = {
        "full_name": test_name,
        "email": test_email,
        "password": test_password,
        "confirm_password": test_password
    }
    response = client.post("/api/auth/register", json=reg_payload)
    assert response.status_code == 201, f"Registration failed with code {response.status_code}: {response.text}"
    user_data = response.json()
    print(f"-> Registered user ID: {user_data['id']}")
    print(f"-> Full name: {user_data['full_name']}")
    print(f"-> Email: {user_data['email']}")

    # Step 2 & 3 & 4: Verify Database, Password Hash & Response Safety
    print("\n[TEST 2, 3 & 4/10] Verifying Database Record, Hashing, and Security Filters...")
    assert "password_hash" not in user_data, "CRITICAL ERROR: password_hash was returned in registration API response!"
    assert "password" not in user_data, "CRITICAL ERROR: password was returned in registration API response!"

    db = SessionLocal()
    try:
        db_user = db.query(User).filter(User.email == test_email).first()
        assert db_user is not None, "User not found in database!"
        assert db_user.password_hash.startswith("$2b$") or db_user.password_hash.startswith("$2a$"), "Password is not bcrypt hashed!"
        assert db_user.password_hash != test_password, "Plaintext password stored in database!"
        print(f"-> Verified user stored in database table 'users'")
        print(f"-> Verified bcrypt hash in DB: {db_user.password_hash[:20]}...")
        print(f"-> Verified password_hash is strictly EXCLUDED from API responses!")
    finally:
        db.close()

    # Step 5: Login using correct credentials
    print("\n[TEST 5/10] Testing Valid Credentials Login (POST /api/auth/login)...")
    login_payload = {
        "email": test_email,
        "password": test_password
    }
    login_resp = client.post("/api/auth/login", json=login_payload)
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token_data = login_resp.json()
    assert "access_token" in token_data, "JWT access token missing!"
    access_token = token_data["access_token"]
    print(f"-> Received JWT Bearer Token: {access_token[:30]}...")

    # Step 6: Reject incorrect credentials
    print("\n[TEST 6/10] Testing Incorrect Credentials Rejection...")
    invalid_login_resp = client.post("/api/auth/login", json={
        "email": test_email,
        "password": "WrongPassword999!"
    })
    assert invalid_login_resp.status_code == 401, f"Expected 401 Unauthorized, got {invalid_login_resp.status_code}"
    print(f"-> Successfully rejected bad password with HTTP 401 Unauthorized")

    # Step 7: Access current user endpoint with valid JWT
    print("\n[TEST 7/10] Testing Authenticated Current User Endpoint (GET /api/auth/me)...")
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me_resp.status_code == 200, f"Failed to fetch authenticated user: {me_resp.text}"
    me_data = me_resp.json()
    assert me_data["email"] == test_email, "Email mismatch in /me response!"
    assert me_data["full_name"] == test_name, "Name mismatch in /me response!"
    assert "password_hash" not in me_data, "CRITICAL ERROR: password_hash in /me response!"
    print(f"-> Authenticated /me response verified for user: {me_data['full_name']}")

    # Step 8: Reject unauthenticated access
    print("\n[TEST 8/10] Testing Unauthenticated Access Rejection...")
    no_auth_resp = client.get("/api/auth/me")
    assert no_auth_resp.status_code == 401, f"Expected 401 Unauthorized for missing token, got {no_auth_resp.status_code}"
    print(f"-> Unauthenticated access to protected route correctly blocked with HTTP 401")

    # Step 9 & 10: Logout endpoint test
    print("\n[TEST 9 & 10/10] Testing Logout Endpoint...")
    logout_resp = client.post("/api/auth/logout")
    assert logout_resp.status_code == 200
    print(f"-> Logout endpoint responded successfully")

    print("\n" + "=" * 60)
    print("ALL 10 VERIFICATION CHECKS PASSED WITH 100% SUCCESS!")
    print("=" * 60)

if __name__ == "__main__":
    test_full_auth_workflow()
