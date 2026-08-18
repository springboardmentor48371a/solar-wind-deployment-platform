"""
Create (or promote) an Administrator account from the command line.

Why this exists: the public POST /auth/register endpoint deliberately
refuses to grant the Administrator or Project Manager roles, no matter
what the request body says -- otherwise anyone could sign up as an
Administrator. That means the very first admin account has to be created
some other way. This script is that "other way": it runs locally against
the database directly, never over HTTP, so it can't be hit by an outside
request.

Usage (run from the backend/ directory, with your venv active and the
same .env the API uses):

    python scripts/create_admin.py you@company.com "Your Name"

You'll be prompted for a password (hidden input). If the email already
exists, the script promotes that existing user to Administrator instead
of creating a duplicate.
"""

import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import Base, engine, SessionLocal  # noqa: E402
from app import models, auth  # noqa: E402


def main() -> None:
    if len(sys.argv) != 3:
        print('Usage: python scripts/create_admin.py <email> "<full name>"')
        sys.exit(1)

    email, full_name = sys.argv[1], sys.argv[2]

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.query(models.User).filter(models.User.email == email).first()
        if existing:
            existing.role = models.RoleEnum.admin
            existing.is_active = 1
            db.commit()
            print(f"Promoted existing user '{email}' to Administrator.")
            return

        password = getpass.getpass("Set a password for this admin account: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Passwords didn't match. Nothing was created.")
            sys.exit(1)

        try:
            auth.validate_password_strength(password)
        except Exception as exc:  # HTTPException outside a request context
            detail = getattr(exc, "detail", str(exc))
            print(f"Password rejected: {detail}")
            sys.exit(1)

        user = models.User(
            full_name=full_name,
            email=email,
            hashed_password=auth.hash_password(password),
            role=models.RoleEnum.admin,
            is_active=1,
        )
        db.add(user)
        db.commit()
        print(f"Created Administrator account for '{email}'. You can log in now.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
