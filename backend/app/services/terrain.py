"""
Terrain data connector — NASA SRTM equivalent.

Open-Elevation is used here as a free, no-API-key SRTM-backed elevation
source, matching the "NASA SRTM Elevation Dataset -> Terrain analysis /
Elevation mapping" row in the Recommended Datasets section of the project
spec. If your mentor wants raw SRTM tiles processed locally instead
(via rasterio/GDAL, listed in your tech stack), swap the HTTP call below
for a rasterio read against a downloaded .hgt/.tif tile — the function
signature (site in, elevation out) stays the same, so nothing else in the
codebase needs to change.
"""

import requests

from app.cache import cached
from app.config import settings


def _elevation_cache_key(latitude: float, longitude: float) -> str:
    # Rounded to ~11m precision — nearby lookups within a site reuse a hit.
    return f"elevation:{round(latitude, 4)}:{round(longitude, 4)}"


@cached(_elevation_cache_key, ttl_seconds=60 * 60 * 24 * 30)  # elevation doesn't change; 30-day TTL
def fetch_elevation(latitude: float, longitude: float) -> float | None:
    """Returns elevation in meters, or None if the lookup fails."""
    try:
        response = requests.get(
            settings.elevation_api_base_url,
            params={"locations": f"{latitude},{longitude}"},
            timeout=10,
        )
        response.raise_for_status()
        results = response.json().get("results", [])
        if results:
            return results[0].get("elevation")
    except requests.RequestException as exc:
        print(f"Warning: elevation lookup failed: {exc}")
    return None


def estimate_slope_pct(latitude: float, longitude: float, delta_deg: float = 0.001) -> float | None:
    """
    Rough slope estimate: samples elevation at a nearby point and computes
    percent grade over the sampled distance. This is a simplification —
    production-grade slope analysis should use a proper DEM (digital
    elevation model) raster with GDAL, as listed in the GIS & Remote
    Sensing tech stack.
    """
    center = fetch_elevation(latitude, longitude)
    north = fetch_elevation(latitude + delta_deg, longitude)
    if center is None or north is None:
        return None

    # ~111km per degree of latitude
    horizontal_distance_m = delta_deg * 111_000
    rise_m = abs(north - center)
    if horizontal_distance_m == 0:
        return None
    return round((rise_m / horizontal_distance_m) * 100, 2)
