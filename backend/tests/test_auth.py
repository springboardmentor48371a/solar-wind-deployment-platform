from tests.conftest import auth_headers, register_and_login


def test_register_self_service_role_needs_no_pin(client):
    resp = client.post(
        "/auth/register",
        json={
            "full_name": "Alex Planner",
            "email": "alex.planner@example.com",
            "password": "Str0ngPass!",
            "role": "Renewable Energy Planner",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["role"] == "Renewable Energy Planner"


def test_register_staff_role_without_pin_is_rejected(client):
    resp = client.post(
        "/auth/register",
        json={
            "full_name": "Fake Admin",
            "email": "fake.admin@example.com",
            "password": "Str0ngPass!",
            "role": "Administrator",
        },
    )
    assert resp.status_code == 403


def test_register_staff_role_with_correct_pin_succeeds(client):
    resp = client.post(
        "/auth/register",
        json={
            "full_name": "Real Admin",
            "email": "real.admin@example.com",
            "password": "Str0ngPass!",
            "role": "Administrator",
            "pin": "1248",
        },
    )
    assert resp.status_code == 201


def test_client_cannot_self_assign_unknown_role(client):
    """A role string outside the known enum values is a 422 (schema
    validation on the Enum), not a silently-accepted arbitrary role."""
    resp = client.post(
        "/auth/register",
        json={
            "full_name": "Sneaky",
            "email": "sneaky@example.com",
            "password": "Str0ngPass!",
            "role": "SuperUser",
        },
    )
    assert resp.status_code == 422


def test_weak_password_rejected(client):
    resp = client.post(
        "/auth/register",
        json={
            "full_name": "Weak Pw",
            "email": "weak@example.com",
            "password": "weak",
            "role": "Renewable Energy Planner",
        },
    )
    assert resp.status_code in (400, 422)


def test_duplicate_email_rejected(client):
    payload = {
        "full_name": "Dup",
        "email": "dup@example.com",
        "password": "Str0ngPass!",
        "role": "Renewable Energy Planner",
    }
    first = client.post("/auth/register", json=payload)
    assert first.status_code == 201
    second = client.post("/auth/register", json=payload)
    assert second.status_code == 400


def test_login_wrong_password_is_generic_401(client):
    client.post(
        "/auth/register",
        json={
            "full_name": "Login Test",
            "email": "logintest@example.com",
            "password": "Str0ngPass!",
            "role": "Renewable Energy Planner",
        },
    )
    resp = client.post(
        "/auth/login", data={"username": "logintest@example.com", "password": "WrongPass1"}
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Incorrect email or password"


def test_login_unknown_email_same_generic_error(client):
    """Regression guard for the timing/enumeration protection in auth.py —
    an unknown email must fail with the exact same message as a known
    email + wrong password, not a distinct 'no such user' error."""
    resp = client.post(
        "/auth/login", data={"username": "nobody@example.com", "password": "WhoKnows1"}
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Incorrect email or password"


def test_staff_login_without_pin_prompts_for_pin(client):
    client.post(
        "/auth/register",
        json={
            "full_name": "Staff",
            "email": "staff.nopin@example.com",
            "password": "Str0ngPass!",
            "role": "GIS Analyst",
            "pin": "1248",
        },
    )
    resp = client.post(
        "/auth/login", data={"username": "staff.nopin@example.com", "password": "Str0ngPass!"}
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "STAFF_PIN_REQUIRED"


def test_me_returns_authenticated_user(client, planner):
    resp = client.get("/auth/me", headers=auth_headers(planner))
    assert resp.status_code == 200
    assert resp.json()["email"] == planner["email"]


def test_me_rejects_missing_token(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_me_rejects_garbage_token(client):
    resp = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401


def test_change_password_then_old_password_fails(client):
    user = register_and_login(client, "Renewable Energy Planner", password="OldPass1!")
    resp = client.post(
        "/auth/change-password",
        headers=auth_headers(user),
        json={"current_password": "OldPass1!", "new_password": "NewPass1!"},
    )
    assert resp.status_code == 200

    old_login = client.post("/auth/login", data={"username": user["email"], "password": "OldPass1!"})
    assert old_login.status_code == 401

    new_login = client.post("/auth/login", data={"username": user["email"], "password": "NewPass1!"})
    assert new_login.status_code == 200
