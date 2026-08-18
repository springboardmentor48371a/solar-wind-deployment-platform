"""
Satellite image processing — Copernicus Sentinel Hub (Copernicus Data
Space Ecosystem), per the "Satellite image processing" module and the
"Copernicus Sentinel Satellite Data" recommended dataset (land cover
analysis, environmental monitoring).

Real integration, same graceful-degradation pattern as every other
external connector in this codebase (see environmental.py, cache.py):
if SENTINEL_HUB_CLIENT_ID/SECRET aren't configured, or the upstream call
fails, the site still gets a SiteImage row — just one clearly marked
source_status="unavailable_no_credentials" / "unavailable_error" instead
of silently pretending nothing happened. Callers (scoring, dashboards)
can branch on source_status rather than guessing from None fields.
"""

import datetime

import requests
from sqlalchemy.orm import Session

from app.cache import cache_get, cache_set
from app.config import settings
from app import models
from app import mongo
from app import data_lake

_token_cache_key = "satellite:sentinel_hub:access_token"


def _get_access_token() -> str | None:
    if not settings.sentinel_hub_client_id or not settings.sentinel_hub_client_secret:
        return None

    cached = cache_get(_token_cache_key)
    if cached:
        return cached.get("access_token")

    response = requests.post(
        settings.sentinel_hub_token_url,
        data={
            "grant_type": "client_credentials",
            "client_id": settings.sentinel_hub_client_id,
            "client_secret": settings.sentinel_hub_client_secret,
        },
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    # Cache for slightly less than the token's real lifetime.
    cache_set(_token_cache_key, payload, ttl_seconds=max(60, payload.get("expires_in", 3600) - 60))
    return payload.get("access_token")


def _bbox_around(lat: float, lon: float, half_size_deg: float = 0.02) -> list:
    return [lon - half_size_deg, lat - half_size_deg, lon + half_size_deg, lat + half_size_deg]


def fetch_and_store_satellite_summary(db: Session, site: models.Site) -> models.SiteImage:
    """
    Pulls the most recent low-cloud Sentinel-2 scene covering the site
    and a NDVI (vegetation index) statistic over a small bounding box
    around it, via Sentinel Hub's Statistical API. Stores a summary row
    in SiteImage and archives the full raw response to MongoDB.
    """
    token = _get_access_token()
    if not token:
        image = models.SiteImage(
            site_id=site.id,
            provider="copernicus_sentinel_hub",
            source_status="unavailable_no_credentials",
        )
        db.add(image)
        db.commit()
        db.refresh(image)
        return image

    bbox = _bbox_around(site.latitude, site.longitude)
    end = datetime.date.today()
    start = end - datetime.timedelta(days=30)

    cache_key = f"satellite:ndvi:{round(site.latitude,3)}:{round(site.longitude,3)}:{start}:{end}"
    stats_payload = cache_get(cache_key)

    request_body = {
        "input": {
            "bounds": {"bbox": bbox, "properties": {"crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"}},
            "data": [{"type": "sentinel-2-l2a"}],
        },
        "aggregation": {
            "timeRange": {"from": f"{start}T00:00:00Z", "to": f"{end}T23:59:59Z"},
            "aggregationInterval": {"of": "P30D"},
            "resx": 20,
            "resy": 20,
            "evalscript": (
                "//VERSION=3\n"
                "function setup() { return { input: [\"B04\",\"B08\",\"CLM\",\"dataMask\"], "
                "output: [{ id: \"data\", bands: 2 }] }; }\n"
                "function evaluatePixel(s) { "
                "let ndvi = (s.B08 - s.B04) / (s.B08 + s.B04 + 1e-6); "
                "return { data: [ndvi, s.CLM] }; }"
            ),
        },
        "calculations": {"default": {}},
    }

    try:
        if stats_payload is None:
            response = requests.post(
                settings.sentinel_hub_stats_url,
                json=request_body,
                headers={"Authorization": f"Bearer {token}"},
                timeout=25,
            )
            response.raise_for_status()
            stats_payload = response.json()
            cache_set(cache_key, stats_payload, ttl_seconds=24 * 60 * 60)

        mongo.store_raw_payload("satellite_raw", site.id, "SENTINEL_HUB_STATS", stats_payload)
        data_lake.archive_payload("satellite_raw", site.id, "SENTINEL_HUB_STATS", stats_payload)

        intervals = stats_payload.get("data", [])
        ndvi_mean = None
        cloud_pct = None
        scene_date = None
        if intervals:
            latest = intervals[-1]
            outputs = latest.get("outputs", {}).get("data", {}).get("bands", {})
            band0 = outputs.get("B0", {}).get("stats", {})  # NDVI band
            band1 = outputs.get("B1", {}).get("stats", {})  # cloud mask band
            ndvi_mean = band0.get("mean")
            cloud_pct = (band1.get("mean") or 0) * 100
            scene_date = datetime.datetime.fromisoformat(
                latest["interval"]["to"].replace("Z", "+00:00")
            )

        land_cover = _classify_land_cover(ndvi_mean)

        image = models.SiteImage(
            site_id=site.id,
            provider="copernicus_sentinel_hub",
            scene_date=scene_date,
            cloud_cover_pct=round(cloud_pct, 1) if cloud_pct is not None else None,
            ndvi_mean=round(ndvi_mean, 3) if ndvi_mean is not None else None,
            land_cover_summary=land_cover,
            source_status="live",
        )
    except Exception as exc:  # noqa: BLE001
        image = models.SiteImage(
            site_id=site.id,
            provider="copernicus_sentinel_hub",
            source_status="unavailable_error",
            land_cover_summary=str(exc)[:200],
        )

    db.add(image)
    db.commit()
    db.refresh(image)
    return image


def _classify_land_cover(ndvi_mean: float | None) -> str | None:
    """Coarse NDVI-band land-cover bucket — a simple threshold rule, not ML."""
    if ndvi_mean is None:
        return None
    if ndvi_mean < 0.1:
        return "bare_soil_or_built_up"
    if ndvi_mean < 0.3:
        return "sparse_vegetation"
    if ndvi_mean < 0.6:
        return "cropland_or_grassland"
    return "dense_vegetation_or_forest"
