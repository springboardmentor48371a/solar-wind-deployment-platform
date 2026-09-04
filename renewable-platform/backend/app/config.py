import os

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://renewable_user:renewable_pass@db:5432/renewable_platform")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "solar_wind_deployment_intelligence_secret_key_2026")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

    # Configurable financial model parameters
    SOLAR_CAPEX_PER_MW_USD: float = float(os.getenv("SOLAR_CAPEX_PER_MW_USD", "850000.0"))
    WIND_CAPEX_PER_MW_USD: float = float(os.getenv("WIND_CAPEX_PER_MW_USD", "1300000.0"))
    PRICE_PER_MWH_USD: float = float(os.getenv("PRICE_PER_MWH_USD", "55.0"))

    # Environmental API endpoints
    NASA_POWER_BASE_URL: str = os.getenv("NASA_POWER_BASE_URL", "https://power.larc.nasa.gov/api/temporal/climatology/point")
    OPEN_ELEVATION_BASE_URL: str = os.getenv("OPEN_ELEVATION_BASE_URL", "https://api.open-elevation.com/api/v1/lookup")
    OVERPASS_BASE_URL: str = os.getenv("OVERPASS_BASE_URL", "https://overpass-api.de/api/interpreter")
    NOMINATIM_BASE_URL: str = os.getenv("NOMINATIM_BASE_URL", "https://nominatim.openstreetmap.org/search")

settings = Settings()
