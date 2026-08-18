import time
from typing import List

import requests
from fastapi import APIRouter, Depends

from app import models, schemas, auth
from app.config import settings
from app import mongo
from app import data_lake
from app.cache import cache_health
from app.services import satellite

router = APIRouter(prefix="/data-sources", tags=["Data Sources"])


def _check_endpoint(name: str, url: str, params: dict, headers: dict | None = None) -> schemas.DataSourceStatusOut:
    start = time.monotonic()
    try:
        response = requests.get(url, params=params, headers=headers, timeout=8)
        latency_ms = int((time.monotonic() - start) * 1000)
        if response.status_code < 400:
            return schemas.DataSourceStatusOut(name=name, status="operational", latency_ms=latency_ms)
        return schemas.DataSourceStatusOut(
            name=name, status="degraded", latency_ms=latency_ms, detail=f"HTTP {response.status_code}"
        )
    except requests.RequestException as exc:
        return schemas.DataSourceStatusOut(name=name, status="down", detail=str(exc))


def _not_configured(name: str, hint: str) -> schemas.DataSourceStatusOut:
    return schemas.DataSourceStatusOut(name=name, status="not_configured", detail=hint)


@router.get("/status", response_model=List[schemas.DataSourceStatusOut])
def data_source_status(current_user: models.User = Depends(auth.get_current_user)):
    """
    Live health check for every external connector and infrastructure
    dependency the platform actually has wired up — mirrors the "DATA
    CONNECTORS · OPERATIONAL" indicator and the Admin Dashboard's "Data
    source management" module. Connectors that need credentials
    (Sentinel Hub, OpenWeather, the S3 data lake) report
    "not_configured" rather than attempting — and failing — a call with
    no credentials, so the distinction between "down" and "never set up"
    is visible to whoever's operating the deployment.
    """
    checks = [
        _check_endpoint(
            "NASA POWER",
            settings.nasa_power_base_url,
            {
                "parameters": "T2M",
                "community": "RE",
                "longitude": 0,
                "latitude": 0,
                "start": "20260101",
                "end": "20260101",
                "format": "JSON",
            },
        ),
        _check_endpoint(
            "OpenStreetMap (Overpass)",
            settings.overpass_api_base_url,
            {"data": "[out:json];node(1);out;"},
        ),
        _check_endpoint(
            "Elevation (SRTM)",
            settings.elevation_api_base_url,
            {"locations": "0,0"},
        ),
        _check_endpoint(
            "World Bank Open Data",
            f"{settings.world_bank_base_url}/country",
            {"format": "json", "per_page": 1},
        ),
        _check_endpoint(
            "NOAA / National Weather Service",
            f"{settings.noaa_base_url}/38.8894,-77.0352",  # Washington, DC — guaranteed US coverage
            {},
            headers={"User-Agent": "SolsticeOS (solar-wind-deployment-intelligence)"},
        ),
    ]

    if satellite.settings.sentinel_hub_client_id and satellite.settings.sentinel_hub_client_secret:
        try:
            token = satellite._get_access_token()
            checks.append(
                schemas.DataSourceStatusOut(name="Copernicus Sentinel Hub", status="operational" if token else "down")
            )
        except requests.RequestException as exc:
            checks.append(schemas.DataSourceStatusOut(name="Copernicus Sentinel Hub", status="down", detail=str(exc)))
    else:
        checks.append(_not_configured("Copernicus Sentinel Hub", "Set SENTINEL_HUB_CLIENT_ID/SECRET to enable satellite imagery."))

    if settings.openweather_api_key:
        checks.append(
            _check_endpoint(
                "OpenWeather",
                settings.openweather_base_url,
                {"lat": 0, "lon": 0, "appid": settings.openweather_api_key},
            )
        )
    else:
        checks.append(_not_configured("OpenWeather", "Set OPENWEATHER_API_KEY to enable live current-conditions data."))

    mongo_ok = mongo.check_connection()
    checks.append(
        schemas.DataSourceStatusOut(
            name="MongoDB (raw payload store)",
            status="operational" if mongo_ok else "down",
            detail=None if mongo_ok else "Could not reach MongoDB",
        )
    )

    cache_status = cache_health()
    checks.append(
        schemas.DataSourceStatusOut(
            name=f"Cache ({cache_status['backend']})",
            status=cache_status["status"],
            detail=cache_status.get("detail"),
        )
    )

    if data_lake.is_configured():
        checks.append(schemas.DataSourceStatusOut(name="Data Lake (S3)", status="operational"))
    else:
        checks.append(_not_configured("Data Lake (S3)", "Set DATA_LAKE_BUCKET to enable raw-payload archival."))

    return checks
