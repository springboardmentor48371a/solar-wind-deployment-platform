from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Primary database: PostgreSQL + PostGIS, per the platform's tech stack.
    # docker-compose ships a postgis/postgis container wired to this URL by
    # default; override it if you're pointing at your own Postgres instance.
    database_url: str = "postgresql://swdip_user:swdip_pass@localhost:5432/swdip_db"

    # Secondary database: MongoDB, for raw/unstructured external-API payloads
    # (full NASA POWER responses, full Overpass responses) kept alongside the
    # structured PostGIS tables for audit and reprocessing. Include
    # credentials in the URL for any Mongo instance that isn't purely
    # localhost-only — an unauthenticated Mongo is a full read/write
    # database open to anyone who can reach the port.
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "swdip_raw"

    # Cache layer: Redis. Used to (a) cache external API responses
    # (NASA POWER, Overpass, elevation) so repeat lookups for the same
    # site/date don't re-hit rate-limited public APIs, and (b) as the
    # request-rate-limit backend in production (see security.py). If
    # Redis is unreachable, app/cache.py degrades to an in-process
    # dict cache automatically — caching is a performance optimization
    # here, never a hard dependency the app can't run without.
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 3600

    secret_key: str = "dev-secret-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    nasa_power_base_url: str = "https://power.larc.nasa.gov/api/temporal/daily/point"
    elevation_api_base_url: str = "https://api.open-elevation.com/api/v1/lookup"
    overpass_api_base_url: str = "https://overpass-api.de/api/interpreter"

    # --- Satellite imagery: Copernicus Data Space Ecosystem / Sentinel Hub ---
    # OAuth2 client-credentials flow. Leave blank to run without live
    # imagery — the satellite service then returns a clearly-labeled
    # "unavailable_no_credentials" result instead of failing the request.
    sentinel_hub_client_id: str = ""
    sentinel_hub_client_secret: str = ""
    sentinel_hub_token_url: str = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    sentinel_hub_stats_url: str = "https://sh.dataspace.copernicus.eu/api/v1/statistics"
    sentinel_hub_catalog_url: str = "https://sh.dataspace.copernicus.eu/api/v1/catalog/1.0.0/search"

    # --- Supplemental weather sources ---
    openweather_api_key: str = ""
    openweather_base_url: str = "https://api.openweathermap.org/data/2.5/weather"
    noaa_base_url: str = "https://api.weather.gov/points"

    # --- Demographic & land data ---
    world_bank_base_url: str = "https://api.worldbank.org/v2"
    # Nominatim reverse geocode is used only to resolve a site's country
    # ISO3 code (needed to query World Bank's country-level indicators);
    # it is NOT used for anything else, and results are cached hard.
    nominatim_reverse_url: str = "https://nominatim.openstreetmap.org/reverse"

    # --- Monitoring / Observability ---
    metrics_enabled: bool = True
    sentry_dsn: str = ""  # leave blank to disable error tracking; app.main no-ops if empty

    # --- Data Lake (S3-compatible: AWS S3, MinIO, R2, B2) ---
    # Leave data_lake_bucket blank to disable archival entirely (best-effort,
    # never a hard dependency — see app/data_lake.py).
    data_lake_bucket: str = ""
    data_lake_region: str = ""
    data_lake_s3_endpoint_url: str = ""  # set for MinIO/R2/B2; leave blank for AWS S3
    data_lake_access_key_id: str = ""
    data_lake_secret_access_key: str = ""

    # --- Data Warehouse ---
    # Nightly/on-demand rollup destination. "postgres" (default) writes
    # aggregate tables into the same Postgres instance via materialized
    # views — zero extra infra required. Point warehouse_export_dir at a
    # local/mounted path to also emit Parquet snapshots for an external
    # warehouse (Snowflake/BigQuery/Redshift) to pick up via its own
    # bulk-load job.
    warehouse_export_dir: str = ""

    # Staff PIN — a shared secret (like an office door code) that any user
    # registering for or logging into an elevated role (GIS Analyst,
    # Project Manager, Administrator) must also provide, on top of their
    # own individual password. Ordinary self-service accounts (Renewable
    # Energy Planner) never need it. Change this in production — it's
    # meant to be handed out by whoever runs the platform, not left at
    # the default.
    staff_pin: str = "1248"

    # Security
    refresh_token_expire_days: int = 7
    rate_limit_default: str = "100/minute"
    rate_limit_auth: str = "10/minute"
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"
    environment: str = "development"  # set to "production" to disable /docs and /redoc


settings = Settings()
