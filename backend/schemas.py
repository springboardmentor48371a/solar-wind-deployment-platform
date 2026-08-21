from pydantic import BaseModel, EmailStr, Field
from typing import Optional


# ============================================================
# USER REGISTRATION
# ============================================================

class UserCreate(BaseModel):

    name: str

    email: EmailStr

    password: str


# ============================================================
# USER LOGIN
# ============================================================

class UserLogin(BaseModel):

    email: EmailStr

    password: str


# ============================================================
# COMPLETE SITE ANALYSIS
#
# User only needs to enter:
#   1. Location
#   2. Land area
#
# Backend will automatically obtain:
#   - Latitude
#   - Longitude
#   - Solar irradiance
#   - Temperature
#   - Wind speed
# from external datasets/APIs.
# ============================================================

class SiteAnalysisRequest(BaseModel):

    location: str = Field(
        ...,
        min_length=2,
        description="Site location such as Vizag, Hyderabad, Chennai"
    )

    land_area: float = Field(
        ...,
        gt=0,
        description="Available land in acres"
    )


# ============================================================
# SOLAR ANALYSIS
#
# Environmental values are OPTIONAL now.
#
# If they are not provided:
# backend fetches them automatically.
# ============================================================

class SolarAnalysisRequest(BaseModel):

    location: str

    land_area: float = Field(
        ...,
        gt=0
    )

    irradiance: Optional[float] = Field(
        default=None,
        ge=0
    )

    temperature: Optional[float] = None

    cloud_cover: Optional[float] = Field(
        default=None,
        ge=0,
        le=100
    )


# ============================================================
# WIND ANALYSIS
#
# Wind speed and temperature are optional because
# backend can obtain them automatically.
# ============================================================

class WindAnalysisRequest(BaseModel):

    location: str

    land_area: float = Field(
        ...,
        gt=0
    )

    wind_speed: Optional[float] = Field(
        default=None,
        ge=0
    )

    temperature: Optional[float] = None

    air_density: float = Field(
        default=1.225,
        gt=0
    )