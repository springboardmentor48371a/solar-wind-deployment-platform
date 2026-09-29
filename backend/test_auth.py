import pytest
from app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token


def test_password_hashing():
    pwd = "SecurePlannerPassword2026!"
    hashed = get_password_hash(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_token_flow():
    token = create_access_token(
        subject="planner@example.com",
        role="Renewable Energy Planner",
        user_id=1
    )
    assert isinstance(token, str)
    assert len(token) > 20

    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "planner@example.com"
    assert payload["role"] == "Renewable Energy Planner"
    assert payload["user_id"] == 1
