import time
from typing import List

import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas, auth
from app.config import settings
from app import mongo
from app import data_lake
from app.cache import cache_health
from app.services import satellite
from app.database import get_db

router = APIRouter(prefix="/data-sources", tags=["Data Sources"])


def _get_overrides(db: Session) -> dict:
    return {
        row.source_name: row
        for row in db.query(models.DataSourceOverride).filter(models.DataSourceOverride.manually_disabled == 1).all()
    }


def _apply_override(check: schemas.DataSourceStatusOut, overrides: dict) -> schemas.DataSourceStatusOut:
    override = overrides.get(check.name)
    if override:
        return schemas.DataSourceStatusOut(
            name=check.name,
            status="manually_disabled",
            detail=override.disabled_reason or "Manually disabled by an administrator.",
        )
    return check


def _check_endpoint(name: str, url: str, params: dict, headers: dict | None = None, method: str = "get", json_body: bool = False) -> schemas.DataSourceStatusOut:
    start = time.monotonic()
    try:
        if method == "post":
            if json_body:
                response = requests.post(url, json=params, headers=headers, timeout=8)
            else:
                response = requests.post(url, data=params, headers=headers, timeout=8)
        else:
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
def data_source_status(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
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
            method="post",  # was GET — Overpass's real interpreter endpoint expects POST, and rejected the GET health-check with a 406 while the real infrastructure.py fetch (which already correctly used POST) was unaffected by this specific bug
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

    checks.append(
        _check_endpoint(
            "AWS Earth Search (Sentinel-2)",
            satellite.EARTH_SEARCH_URL,
            {"collections": ["sentinel-2-l2a"], "limit": 1},
            method="post",
            json_body=True,
        )
    )

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

    overrides = _get_overrides(db)
    return [_apply_override(check, overrides) for check in checks]


@router.post("/{source_name}/override", response_model=schemas.DataSourceStatusOut)
def set_data_source_override(
    source_name: str,
    body: schemas.DataSourceOverrideRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Admin Dashboard's "Data source management" sub-item — real
    management, not just viewing status. Lets an Administrator manually
    pause or resume a connector regardless of whether its credentials
    are configured (e.g. during a vendor outage or to avoid a rate
    limit), without editing environment variables and restarting the
    server. Deliberately does NOT store API keys/credentials in the
    database — that's a real security tradeoff this project avoids, not
    a missing feature (see README for the reasoning).
    """
    if current_user.role != models.RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Only Administrators can manage data sources.")

    override = db.query(models.DataSourceOverride).filter(models.DataSourceOverride.source_name == source_name).first()
    if override is None:
        override = models.DataSourceOverride(source_name=source_name)
        db.add(override)

    override.manually_disabled = 1 if body.manually_disabled else 0
    override.disabled_by_user_id = current_user.id if body.manually_disabled else None
    override.disabled_reason = body.reason if body.manually_disabled else None
    db.commit()

    if body.manually_disabled:
        return schemas.DataSourceStatusOut(name=source_name, status="manually_disabled", detail=body.reason or "Manually disabled by an administrator.")
    return schemas.DataSourceStatusOut(name=source_name, status="operational", detail="Re-enabled — actual status will reflect on the next health check.")
