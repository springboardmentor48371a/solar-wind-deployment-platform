from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text

from app.database import Base, engine, ensure_postgis_extension, ensure_timescaledb
from app.config import settings
from app.security import limiter, SecurityHeadersMiddleware
from app.logging_config import configure_logging, RequestLoggingMiddleware
from app.cache import cache_health
from app import mongo
from app import data_lake

from app.routers import auth as auth_router
from app.routers import projects as projects_router
from app.routers import sites as sites_router
from app.routers import analytics as analytics_router
from app.routers import alerts as alerts_router
from app.routers import data_sources as data_sources_router
from app.routers import reports as reports_router
from app.routers import report_templates as report_templates_router
from app.routers import integrations as integrations_router
from app.routers import users as users_router
from app.routers import audit as audit_router
from app.routers import gis as gis_router
from app.routers import regions as regions_router

configure_logging(level="DEBUG" if settings.environment != "production" else "INFO")

# --- Optional error tracking (Sentry) ---
# No-ops entirely if SENTRY_DSN isn't set — never a hard dependency.
if settings.sentry_dsn:
    try:
        import sentry_sdk

        sentry_sdk.init(dsn=settings.sentry_dsn, environment=settings.environment, traces_sample_rate=0.1)
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: Sentry initialization failed: {exc}")

# Enables the PostGIS and (if available) TimescaleDB extensions, then
# creates tables on startup. Swap for Alembic migrations once the schema
# stabilizes.
ensure_postgis_extension()
Base.metadata.create_all(bind=engine)
ensure_timescaledb()

app = FastAPI(
    title="Solstice OS — Solar & Wind Deployment Intelligence Platform API",
    description=(
        "Auth, RBAC, Project & Site Management, Environmental/Terrain/Infrastructure/"
        "Satellite/Demographic data integration, Solar & Wind Potential Engines, "
        "rule-based Site Suitability Scoring, Investment Analytics, Power Simulation, "
        "SCADA/IoT Telemetry, Integrations, Custom Report Builder, Analytics, Alerts, "
        "User Administration, and Audit Logging. AI/ML prediction models are "
        "intentionally excluded — planned for the next phase."
    ),
    version="0.4.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
    openapi_url="/openapi.json" if settings.environment != "production" else None,
)

app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please slow down and try again shortly."},
    )


# SlowAPIMiddleware makes the Limiter's default_limits apply to every route
# automatically, not just ones with an explicit @limiter.limit decorator.
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
# Outermost of the two custom middlewares so it wraps the full request,
# including time spent in SecurityHeadersMiddleware and route handling.
app.add_middleware(RequestLoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Monitoring: Prometheus /metrics scrape endpoint ---
# Request counts, latencies, and status codes for every route, with zero
# per-route instrumentation needed. Toggle off via METRICS_ENABLED=false.
if settings.metrics_enabled:
    try:
        from prometheus_fastapi_instrumentator import Instrumentator

        Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: Prometheus instrumentation unavailable: {exc}")

app.include_router(auth_router.router)
app.include_router(projects_router.router)
app.include_router(sites_router.router)
app.include_router(analytics_router.router)
app.include_router(alerts_router.router)
app.include_router(data_sources_router.router)
app.include_router(reports_router.router)
app.include_router(report_templates_router.router)
app.include_router(integrations_router.router)
app.include_router(users_router.router)
app.include_router(audit_router.router)
app.include_router(gis_router.router)
app.include_router(regions_router.router)


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok"}


@app.get("/health/detailed", tags=["System"])
def health_check_detailed():
    """
    Deeper liveness check for monitoring/ops: reports each dependency
    (primary DB, secondary DB, cache, data lake) individually instead of
    just process-is-up, so a dashboard or alert can tell *what* is degraded.
    """
    db_ok = True
    db_detail = None
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        db_ok = False
        db_detail = str(exc)

    mongo_ok = mongo.check_connection()
    cache_status = cache_health()

    overall = "ok" if db_ok and mongo_ok else "degraded"
    return {
        "status": overall,
        "postgres": {"status": "operational" if db_ok else "down", "detail": db_detail},
        "mongodb": {"status": "operational" if mongo_ok else "down"},
        "cache": cache_status,
        "data_lake": {"configured": data_lake.is_configured()},
        "metrics_enabled": settings.metrics_enabled,
        "environment": settings.environment,
    }
