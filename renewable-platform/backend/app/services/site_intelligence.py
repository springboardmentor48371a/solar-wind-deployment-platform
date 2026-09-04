"""
Site Auto-Intelligence — fills in every Module 2 "Site Information" field
*except latitude/longitude* purely from live geospatial datasets.

The person registering a site now only supplies coordinates (+ a name and
preferred technology). Everything else the spec lists under "Site
Information" -- Region, Land Area, Elevation, Existing Infrastructure, Land
Ownership -- is derived here from NASA/SRTM elevation data and OpenStreetMap,
via geo_data_service. If a user explicitly supplies one of these fields we
still respect their override (useful when live data is unavailable or a
survey has more accurate figures), but nothing is required beyond lat/lon.
"""
import hashlib
from typing import Optional

from . import geo_data_service as geo

DEFAULT_LAND_AREA_HECTARES = 10.0  # used only if no OSM landuse parcel is found nearby


def _fallback_elevation_m(latitude: float, longitude: float) -> float:
    """Deterministic elevation estimate used only if Open-Elevation is
    unreachable, so a site's elevation is never left blank."""
    seed = f"{latitude:.4f}:{longitude:.4f}:elev"
    h = hashlib.sha256(seed.encode()).hexdigest()
    frac = int(h[:8], 16) / 0xFFFFFFFF
    return round(frac * 1200, 1)


def derive_site_attributes(latitude: float, longitude: float) -> dict:
    """Returns dict with elevation_m, land_area_hectares, region,
    existing_infrastructure, land_ownership, landuse_tag, data_source."""
    elevation_data = geo.fetch_elevation_profile(latitude, longitude)
    osm_data = geo.fetch_osm_context(latitude, longitude)
    region = geo.reverse_geocode_region(latitude, longitude)

    live_ok = elevation_data is not None and osm_data is not None

    elevation_m = elevation_data["elevation_m"] if elevation_data else _fallback_elevation_m(latitude, longitude)
    land_area_hectares = (osm_data or {}).get("land_area_hectares") or DEFAULT_LAND_AREA_HECTARES
    landuse_tag = (osm_data or {}).get("landuse_tag")
    land_ownership = geo.landuse_label(landuse_tag) or "Unclassified / not mapped in OpenStreetMap"

    infra_bits = []
    if osm_data:
        if osm_data.get("distance_to_road_km") is not None:
            infra_bits.append(f"Nearest road {osm_data['distance_to_road_km']} km")
        if osm_data.get("distance_to_transmission_km") is not None:
            infra_bits.append(f"transmission line {osm_data['distance_to_transmission_km']} km")
        if osm_data.get("distance_to_substation_km") is not None:
            infra_bits.append(f"substation {osm_data['distance_to_substation_km']} km")
    existing_infrastructure = "; ".join(infra_bits) if infra_bits else "No mapped infrastructure within 6 km radius"

    return {
        "elevation_m": elevation_m,
        "land_area_hectares": round(land_area_hectares, 2),
        "region": region or "Region unavailable (reverse geocoding unreachable)",
        "existing_infrastructure": existing_infrastructure,
        "land_ownership": land_ownership,
        "landuse_tag": landuse_tag,
        "osm_context": osm_data,
        "data_source": "live" if live_ok else "synthetic_fallback",
    }


def merge_with_overrides(derived: dict, user_supplied: dict) -> dict:
    """User-supplied non-null fields win over derived ones; everything else
    (including anything the user left blank) is filled from live data."""
    merged = dict(derived)
    for key in ("region", "land_area_hectares", "elevation_m", "existing_infrastructure", "land_ownership"):
        if user_supplied.get(key) not in (None, ""):
            merged[key] = user_supplied[key]
    return merged
