from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import get_settings


def get_jwt_secret_key() -> str:
    settings = get_settings()
    if settings.jwt_secret_key is None:
        raise RuntimeError("JWT_SECRET_KEY is not configured.")

    secret_key = settings.jwt_secret_key.get_secret_value()
    if len(secret_key) < 32:
        raise RuntimeError("JWT_SECRET_KEY must be at least 32 characters long.")

    return secret_key


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    return hashed_password.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        password_hash.encode("utf-8"),
    )


def create_access_token(subject: str) -> str:
    settings = get_settings()
    expire_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_access_token_expire_minutes,
    )
    payload = {
        "sub": subject,
        "exp": expire_at,
    }
    return jwt.encode(
        payload,
        get_jwt_secret_key(),
        algorithm=settings.jwt_algorithm,
    )
