"""
Environmental Data Collection Engine (Module 3) + Geographic Intelligence
Engine (Module 4).

In production this calls out to NASA POWER, Global Wind Atlas, NASA SRTM,
OpenStreetMap and Copernicus Sentinel Hub (see README). To keep this
scaffold runnable with zero API keys, we generate deterministic,
latitude/elevation-aware synthetic values so every downstream engine
(solar/wind prediction, scoring, forecasting) has real numbers to work
with. Swap `fetch_environmental_data` for real API calls when you wire in
credentials -- nothing downstream needs to change since the function
signature/return shape stays the same.
"""
import hashlib
import math


def _stable_rand(seed_key: str, low: float, high: float) -> float:
    """Deterministic pseudo-random float in [low, high], seeded by a string
    so the same site always returns the same environmental figures."""
    h = hashlib.sha256(seed_key.encode()).hexdigest()
    frac = int(h[:8], 16) / 0xFFFFFFFF
    return low + frac * (high - low)


def fetch_environmental_data(site_id: int, latitude: float, longitude: float, elevation_m: float = 0.0) -> dict:
    seed = f"{site_id}:{latitude:.4f}:{longitude:.4f}"

    # Solar irradiance peaks near the equator and falls off with latitude
    lat_factor = math.cos(math.radians(min(abs(latitude), 65)))
    base_irradiance = 3.0 + lat_factor * 4.0
    irradiance = round(base_irradiance + _stable_rand(seed + "irr", -0.4, 0.4), 2)

    wind_speed = round(_stable_rand(seed + "wind", 2.5, 9.5), 2)
    wind_dir = round(_stable_rand(seed + "wdir", 0, 359), 1)

    temp = round(30 - (abs(latitude) * 0.5) + _stable_rand(seed + "temp", -3, 3), 1)
    rainfall = round(_stable_rand(seed + "rain", 200, 2000), 0)
    cloud_cover = round(_stable_rand(seed + "cloud", 10, 70), 1)

    slope = round(_stable_rand(seed + "slope", 0, 18), 2)
    ndvi = round(_stable_rand(seed + "ndvi", 0.1, 0.8), 2)

    dist_road = round(_stable_rand(seed + "road", 0.2, 25), 2)
    dist_transmission = round(_stable_rand(seed + "trans", 0.5, 40), 2)
    dist_substation = round(_stable_rand(seed + "sub", 0.5, 35), 2)
    dist_urban = round(_stable_rand(seed + "urban", 1, 60), 2)
    dist_water = round(_stable_rand(seed + "water", 0.2, 20), 2)
    protected = _stable_rand(seed + "protected", 0, 1) > 0.85

    return {
        "solar_irradiance_kwh_m2_day": irradiance,
        "wind_speed_avg_ms": wind_speed,
        "wind_direction_deg": wind_dir,
        "temperature_avg_c": temp,
        "rainfall_mm_year": rainfall,
        "cloud_cover_pct": cloud_cover,
        "land_slope_pct": slope,
        "vegetation_index_ndvi": ndvi,
        "distance_to_road_km": dist_road,
        "distance_to_transmission_km": dist_transmission,
        "distance_to_substation_km": dist_substation,
        "distance_to_urban_km": dist_urban,
        "distance_to_water_km": dist_water,
        "in_protected_zone": protected,
    }
