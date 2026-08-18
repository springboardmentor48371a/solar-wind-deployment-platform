"""
Security hardening utilities:
- Security response headers (defends against clickjacking, MIME sniffing, etc.)
- Rate limiter instance (brute-force / abuse protection)
- Audit logging helper (who did what, when — useful for your faculty review
  and for any future compliance/security question)
"""

from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app import models
from app.config import settings

# default_limits applies to every route automatically; auth routes layer a
# stricter limit on top via their own @limiter.limit(...) decorator.
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit_default])


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        # Only set HSTS if actually served over HTTPS in production (behind a reverse proxy)
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response


def log_action(
    db: Session,
    user_id: int | None,
    action: str,
    resource: str | None = None,
    ip_address: str | None = None,
) -> None:
    entry = models.AuditLog(
        user_id=user_id, action=action, resource=resource, ip_address=ip_address
    )
    db.add(entry)
    db.commit()
