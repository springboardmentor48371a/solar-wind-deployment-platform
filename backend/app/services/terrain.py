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
    except Exception as exc:  # noqa: BLE001
        # Deliberately broad, not just requests.RequestException: an
        # upstream hiccup (rate-limit page, gateway error, malformed
        # body) can return HTTP 200 with a non-JSON or unexpectedly
        # shaped body, which raises JSONDecodeError/AttributeError/
        # IndexError here — none of which are RequestException
        # subclasses. A real 500 from this — "Could not register site"
        # with no explanation — is worse than a logged warning and a
        # None elevation the pipeline already knows how to handle.
        print(f"Warning: elevation lookup failed: {exc}")
    return None


def estimate_slope_pct(latitude: float, longitude: float, delta_deg: float = 0.01) -> float | None:
    """
    Rough slope estimate: samples elevation at 2 diagonal points (NE and
    SW) and returns the steeper of the 2, as percent grade over the
    sampled distance. This is a simplification — production-grade slope
    analysis should use a proper DEM (digital elevation model) raster
    with GDAL, as listed in the GIS & Remote Sensing tech stack.

    delta_deg was originally 0.001 (~111m) — a real, significant bug
    found via live testing: a genuinely mountainous real site
    (Mawsynram, in India's steep Khasi Hills) came back with an
    estimated slope of exactly 0%, which gave it a perfect Geographic
    sub-score and masked what should have been a much lower overall
    suitability result. Root cause: Open-Elevation's underlying SRTM
    data is typically 30-90m resolution, so two sample points only 111m
    apart can easily land on the same or adjacent pixels with
    near-identical elevation. 0.01 degrees (~1.1km) samples far enough
    apart to reliably clear DEM resolution artifacts.

    Originally sampled all 4 cardinal directions (5 total elevation
    calls) — a second real issue found via live testing: this
    meaningfully increased load on Open-Elevation's free public API,
    and elevation itself started coming back blank on sites that had
    worked fine before, consistent with hitting a burst rate limit.
    Reduced to 2 diagonal points (3 total calls) — still catches slope
    in both the north-south and east-west directions simultaneously
    (a diagonal isn't purely one axis), while keeping the same total
    load as the original single-direction version plus one extra call,
    not more than double it.
    """
    center = fetch_elevation(latitude, longitude)
    if center is None:
        return None

    # ~111km per degree of latitude; longitude scales down by cos(latitude),
    # but for a rough same-order-of-magnitude slope estimate this is a
    # reasonable simplification rather than requiring a full projection.
    horizontal_distance_m = (delta_deg * 111_000) * (2 ** 0.5)  # diagonal distance
    if horizontal_distance_m == 0:
        return None

    directions = [
        (latitude + delta_deg, longitude + delta_deg),  # NE
        (latitude - delta_deg, longitude - delta_deg),  # SW
    ]
    slopes = []
    for lat, lon in directions:
        elevation = fetch_elevation(lat, lon)
        if elevation is not None:
            rise_m = abs(elevation - center)
            slopes.append(round((rise_m / horizontal_distance_m) * 100, 2))

    if not slopes:
        return None
    return max(slopes)
