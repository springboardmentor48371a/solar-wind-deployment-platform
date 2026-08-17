import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class Settings:
    # Database Settings
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5433")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "solar_wind_db")

    @property
    def DATABASE_URL(self) -> str:
        # Construct PostgreSQL URL dynamically
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # JWT Settings
    JWT_SECRET: str = os.getenv("JWT_SECRET", "default_jwt_secret_key_change_me")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    # Default Suitability Weights (must sum to 1.0)
    DEFAULT_WEIGHT_RESOURCE: float = 0.35      # Resource Availability (35%)
    DEFAULT_WEIGHT_GEOGRAPHIC: float = 0.25    # Geographic Suitability (25%)
    DEFAULT_WEIGHT_INFRASTRUCTURE: float = 0.15# Infrastructure Accessibility (15%)
    DEFAULT_WEIGHT_ENVIRONMENT: float = 0.15   # Environmental Impact (15%)
    DEFAULT_WEIGHT_ECONOMIC: float = 0.10      # Economic Feasibility (10%)

settings = Settings()
