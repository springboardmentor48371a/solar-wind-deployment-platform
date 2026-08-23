"""
Demographic & land data, and environmental-constraint proximity — per the
"Demographic & land data" (World Bank) and "Environmental databases"
(protected areas, land use) modules.

Two real, live data sources, no API key required for either:
  - OpenStreetMap/Overpass: protected-area, water-body, agricultural-land,
    and urban-area proximity around the site (same public Overpass
    instance the infrastructure connector already uses).
  - World Bank Open Data API: country-level population density and GDP
    per capita, used as demographic/economic context for the site's
    country. This is necessarily country-level (World Bank doesn't
    publish sub-national indicators for most countries) — the country
    itself is resolved via a reverse-geocode lookup against Nominatim.
"""

import requests
from sqlalchemy.orm import Session

from app.cache import cache_get, cache_set
from app.config import settings
from app import models
from app.services.geo_utils import nearest_features_km
from app import mongo
from app import data_lake

SEARCH_RADIUS_M = 20000

WB_POP_DENSITY_INDICATOR = "EN.POP.DNST"
WB_GDP_PER_CAPITA_INDICATOR = "NY.GDP.PCAP.CD"
WB_ELECTRICITY_PER_CAPITA_INDICATOR = "EG.USE.ELEC.KH.PC"  # kWh per capita/year — feeds Grid Contribution Forecasting


def _reverse_geocode_country(lat: float, lon: float) -> tuple[str | None, str | None]:
    """Returns (country_name, iso3_alpha3) via Nominatim, cached hard (country doesn't move)."""
    cache_key = f"geocode:country:{round(lat, 2)}:{round(lon, 2)}"
    cached = cache_get(cache_key)
    if cached:
        return cached.get("country"), cached.get("iso3")

    try:
        response = requests.get(
            settings.nominatim_reverse_url,
            params={"lat": lat, "lon": lon, "format": "jsonv2", "zoom": 3},
            headers={"User-Agent": "solstice-os-solar-wind-platform/1.0"},
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        address = payload.get("address", {})
        country = address.get("country")
        iso2 = address.get("country_code", "").upper()
        iso3 = _iso2_to_iso3(iso2)
        cache_set(cache_key, {"country": country, "iso3": iso3}, ttl_seconds=30 * 24 * 60 * 60)
        return country, iso3
    except Exception:  # noqa: BLE001
        return None, None


# Small ISO2->ISO3 map covering the countries this platform is realistically
# deployed for; falls back to querying World Bank's own country list for
# anything not in here rather than hardcoding all ~195 countries.
_ISO2_ISO3_FALLBACK = {}


def _iso2_to_iso3(iso2: str) -> str | None:
    if not iso2:
        return None
    if iso2 in _ISO2_ISO3_FALLBACK:
        return _ISO2_ISO3_FALLBACK[iso2]
    cache_key = "geocode:iso2_iso3_table"
    table = cache_get(cache_key)
    if table is None:
        try:
            response = requests.get(
                f"{settings.world_bank_base_url}/country",
                params={"format": "json", "per_page": 400},
                timeout=15,
            )
            response.raise_for_status()
            rows = response.json()[1]
            table = {r["iso2Code"]: r["id"] for r in rows if r.get("iso2Code")}
            cache_set(cache_key, table, ttl_seconds=30 * 24 * 60 * 60)
        except Exception:  # noqa: BLE001
            table = {}
    _ISO2_ISO3_FALLBACK.update(table)
    return table.get(iso2)


def _fetch_world_bank_indicator(iso3: str, indicator: str) -> float | None:
    cache_key = f"worldbank:{iso3}:{indicator}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached.get("value")
    try:
        response = requests.get(
            f"{settings.world_bank_base_url}/country/{iso3}/indicator/{indicator}",
            params={"format": "json", "per_page": 5, "mrnev": 1},  # most recent non-empty value
            timeout=15,
        )
        response.raise_for_status()
        rows = response.json()
        value = None
        if len(rows) > 1 and rows[1]:
            value = rows[1][0].get("value")
        cache_set(cache_key, {"value": value}, ttl_seconds=7 * 24 * 60 * 60)
        return value
    except Exception:  # noqa: BLE001
        return None


def fetch_and_store_environmental_constraints(
    db: Session, site: models.Site
) -> models.EnvironmentalConstraint:
    """
    Combines OSM proximity (protected areas, water bodies, agricultural
    land, urban areas) with World Bank country-level demographic context
    into one EnvironmentalConstraint row per site.
    """
    query = f"""
    [out:json][timeout:25];
    (
      way["boundary"="protected_area"](around:{SEARCH_RADIUS_M},{site.latitude},{site.longitude});
      way["leisure"="nature_reserve"](around:{SEARCH_RADIUS_M},{site.latitude},{site.longitude});
      way["natural"="water"](around:{SEARCH_RADIUS_M},{site.latitude},{site.longitude});
      way["landuse"="farmland"](around:{SEARCH_RADIUS_M},{site.latitude},{site.longitude});
      way["landuse"="residential"](around:{SEARCH_RADIUS_M},{site.latitude},{site.longitude});
    );
    out center 20;
    """
    cache_key = f"environmental:overpass:{round(site.latitude,3)}:{round(site.longitude,3)}"
    payload = cache_get(cache_key)
    if payload is None:
        response = requests.post(settings.overpass_api_base_url, data={"data": query}, timeout=30)
        response.raise_for_status()
        payload = response.json()
        cache_set(cache_key, payload, ttl_seconds=7 * 24 * 60 * 60)

    mongo.store_raw_payload("environmental_raw", site.id, "OVERPASS_ENVIRONMENTAL", payload)
    data_lake.archive_payload("environmental_raw", site.id, "OVERPASS_ENVIRONMENTAL", payload)

    elements = payload.get("elements", [])
    buckets = {"protected": [], "water": [], "farmland": [], "residential": []}
    for el in elements:
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        if lat is None or lon is None:
            continue
        tags = el.get("tags", {})
        candidate = {"lat": lat, "lon": lon, "name": tags.get("name")}
        if tags.get("boundary") == "protected_area" or tags.get("leisure") == "nature_reserve":
            buckets["protected"].append(candidate)
        elif tags.get("natural") == "water":
            buckets["water"].append(candidate)
        elif tags.get("landuse") == "farmland":
            buckets["farmland"].append(candidate)
        elif tags.get("landuse") == "residential":
            buckets["residential"].append(candidate)

    def nearest_km(candidates):
        if not candidates:
            return None
        scored = nearest_features_km(site.latitude, site.longitude, candidates)
        return round(float(scored["distance_km"].min()), 2)

    country, iso3 = _reverse_geocode_country(site.latitude, site.longitude)
    pop_density = _fetch_world_bank_indicator(iso3, WB_POP_DENSITY_INDICATOR) if iso3 else None
    gdp_per_capita = _fetch_world_bank_indicator(iso3, WB_GDP_PER_CAPITA_INDICATOR) if iso3 else None
    electricity_per_capita = _fetch_world_bank_indicator(iso3, WB_ELECTRICITY_PER_CAPITA_INDICATOR) if iso3 else None

    db.query(models.EnvironmentalConstraint).filter(
        models.EnvironmentalConstraint.site_id == site.id
    ).delete()

    record = models.EnvironmentalConstraint(
        site_id=site.id,
        protected_area_distance_km=nearest_km(buckets["protected"]),
        water_body_distance_km=nearest_km(buckets["water"]),
        agricultural_land_nearby=1 if buckets["farmland"] else 0,
        urban_area_distance_km=nearest_km(buckets["residential"]),
        country_iso3=iso3,
        population_density_km2=pop_density,
        gdp_per_capita_usd=gdp_per_capita,
        electricity_consumption_kwh_per_capita=electricity_per_capita,
        data_source="OpenStreetMap (Overpass) + World Bank Open Data",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
