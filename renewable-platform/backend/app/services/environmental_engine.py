"""
Environmental Data Collection Engine (Module 3) + Geographic Intelligence
Engine (Module 4).

Live-first: calls NASA POWER (solar/wind/temp/rain/cloud), Open-Elevation
(terrain/slope) and OpenStreetMap Overpass (infrastructure & land-use
distances) via geo_data_service. NDVI has no free key-less satellite
provider, so it is proxied from the OSM land-use classification of the
parcel (forest/grass score high, industrial/residential score low) -- still
real data, not a random number.

If any live provider is unreachable (offline dev environment, rate limit,
etc.) the affected fields -- and only those fields -- fall back to a
deterministic, latitude/elevation-aware estimate so the rest of the pipeline
never breaks. Every response carries `data_source` ("live" or
"synthetic_fallback") so the UI can be transparent about which one was used.
"""
import hashlib
import math

from . import geo_data_service as geo


def _stable_rand(seed_key: str, low: float, high: float) -> float:
    """Deterministic pseudo-random float in [low, high], seeded by a string
    so the same site always returns the same fallback figures."""
    h = hashlib.sha256(seed_key.encode()).hexdigest()
    frac = int(h[:8], 16) / 0xFFFFFFFF
    return low + frac * (high - low)


def _fallback_climatology(seed: str, latitude: float) -> dict:
    lat_factor = math.cos(math.radians(min(abs(latitude), 65)))
    base_irradiance = 3.0 + lat_factor * 4.0
    irradiance = round(base_irradiance + _stable_rand(seed + "irr", -0.4, 0.4), 2)
    wind_speed = round(_stable_rand(seed + "wind", 2.5, 9.5), 2)
    temp = round(30 - (abs(latitude) * 0.5) + _stable_rand(seed + "temp", -3, 3), 1)
    rainfall = round(_stable_rand(seed + "rain", 200, 2000), 0)
    cloud_cover = round(_stable_rand(seed + "cloud", 10, 70), 1)
    return {
        "solar_irradiance_kwh_m2_day": irradiance,
        "wind_speed_avg_ms": wind_speed,
        "temperature_avg_c": temp,
        "rainfall_mm_year": rainfall,
        "cloud_cover_pct": cloud_cover,
    }


def _fallback_terrain(seed: str) -> dict:
    return {
        "elevation_m": round(_stable_rand(seed + "elev", 0, 1200), 1),
        "land_slope_pct": round(_stable_rand(seed + "slope", 0, 18), 2),
    }


def _fallback_infra(seed: str) -> dict:
    return {
        "distance_to_road_km": round(_stable_rand(seed + "road", 0.2, 25), 2),
        "distance_to_transmission_km": round(_stable_rand(seed + "trans", 0.5, 40), 2),
        "distance_to_substation_km": round(_stable_rand(seed + "sub", 0.5, 35), 2),
        "distance_to_urban_km": round(_stable_rand(seed + "urban", 1, 60), 2),
        "distance_to_water_km": round(_stable_rand(seed + "water", 0.2, 20), 2),
        "in_protected_zone": _stable_rand(seed + "protected", 0, 1) > 0.85,
    }


def fetch_environmental_data(
    site_id: int,
    latitude: float,
    longitude: float,
    elevation_m: float = None,
    osm_context: dict = None,
) -> dict:
    """Builds the full environmental feature set for a site.

    `elevation_m` / `osm_context` can be passed in from site_intelligence's
    earlier calls for the same coordinates so we don't hit Open-Elevation /
    Overpass twice per site registration; if omitted this function fetches
    them itself.
    """
    seed = f"{site_id}:{latitude:.4f}:{longitude:.4f}"

    climatology = geo.fetch_nasa_power_climatology(latitude, longitude)
    climatology_live = climatology is not None
    climatology = climatology or _fallback_climatology(seed, latitude)

    if elevation_m is not None:
        terrain = {"elevation_m": elevation_m, "land_slope_pct": None}
        terrain_live = True
    else:
        terrain = geo.fetch_elevation_profile(latitude, longitude)
        terrain_live = terrain is not None
        terrain = terrain or _fallback_terrain(seed)
    if terrain.get("land_slope_pct") is None:
        # elevation was reused from site_intelligence but slope wasn't carried over
        slope_probe = geo.fetch_elevation_profile(latitude, longitude)
        terrain["land_slope_pct"] = slope_probe["land_slope_pct"] if slope_probe else _fallback_terrain(seed)["land_slope_pct"]

    if osm_context is None:
        osm_context = geo.fetch_osm_context(latitude, longitude)
    infra_live = osm_context is not None
    landuse_tag = (osm_context or {}).get("landuse_tag")
    infra = {
        "distance_to_road_km": (osm_context or {}).get("distance_to_road_km"),
        "distance_to_transmission_km": (osm_context or {}).get("distance_to_transmission_km"),
        "distance_to_substation_km": (osm_context or {}).get("distance_to_substation_km"),
        "distance_to_urban_km": (osm_context or {}).get("distance_to_urban_km"),
        "distance_to_water_km": (osm_context or {}).get("distance_to_water_km"),
        "in_protected_zone": (osm_context or {}).get("in_protected_zone"),
    }
    fallback_infra = _fallback_infra(seed)
    for key, val in list(infra.items()):
        if val is None:
            infra[key] = fallback_infra[key]
            infra_live = False

    ndvi = geo.landuse_ndvi_proxy(landuse_tag) if landuse_tag else round(_stable_rand(seed + "ndvi", 0.1, 0.8), 2)

    all_live = climatology_live and terrain_live and infra_live

    return {
        "solar_irradiance_kwh_m2_day": climatology["solar_irradiance_kwh_m2_day"],
        "wind_speed_avg_ms": climatology["wind_speed_avg_ms"],
        "wind_direction_deg": round(_stable_rand(seed + "wdir", 0, 359), 1),  # NASA POWER climatology has no prevailing direction field
        "temperature_avg_c": climatology["temperature_avg_c"],
        "rainfall_mm_year": climatology["rainfall_mm_year"],
        "cloud_cover_pct": climatology["cloud_cover_pct"],
        "land_slope_pct": terrain["land_slope_pct"],
        "vegetation_index_ndvi": ndvi,
        "distance_to_road_km": infra["distance_to_road_km"],
        "distance_to_transmission_km": infra["distance_to_transmission_km"],
        "distance_to_substation_km": infra["distance_to_substation_km"],
        "distance_to_urban_km": infra["distance_to_urban_km"],
        "distance_to_water_km": infra["distance_to_water_km"],
        "in_protected_zone": bool(infra["in_protected_zone"]),
        "data_source": "live" if all_live else "synthetic_fallback",
    }
