import math
import httpx

NOMINATIM_URL  = "https://nominatim.openstreetmap.org/reverse"
OVERPASS_URL   = "https://overpass-api.de/api/interpreter"
HEADERS        = {"User-Agent": "SolarWindPlatform/1.0"}

# Road type → score (0–100) based on accessibility
_ROAD_SCORES = {
    "motorway": 100, "trunk": 95, "primary": 90,
    "secondary": 75, "tertiary": 60,
    "unclassified": 40, "residential": 35,
    "track": 15, "path": 10, "footway": 5,
}

# Grid proximity thresholds (km)
# 0–5 km  → full score (100)
# 5–20 km → linear decay from 100 → 20
# >20 km  → floor score (20)
_GRID_FULL_KM  = 5.0
_GRID_MAX_KM   = 20.0
_GRID_FLOOR    = 20.0
_SEARCH_RADIUS = 25000  # metres — covers the max suitable distance + margin


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def _grid_score_from_distance(dist_km: float) -> float:
    if dist_km <= _GRID_FULL_KM:
        return 100.0
    if dist_km >= _GRID_MAX_KM:
        return _GRID_FLOOR
    # Linear decay between full and max thresholds
    ratio = (dist_km - _GRID_FULL_KM) / (_GRID_MAX_KM - _GRID_FULL_KM)
    return round(100.0 - ratio * (100.0 - _GRID_FLOOR), 2)


async def _fetch_road_score(lat: float, lon: float) -> float:
    """Score road accessibility via Nominatim reverse geocode."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(
                NOMINATIM_URL,
                params={"lat": lat, "lon": lon, "format": "json", "zoom": 17},
                headers=HEADERS,
            )
            res.raise_for_status()
        data = res.json()
        if data.get("class") == "highway":
            return float(_ROAD_SCORES.get(data.get("type", ""), 30))
        return 10.0  # no road at this zoom level
    except Exception:
        return 50.0  # fallback for this half only


async def _fetch_power_score(lat: float, lon: float) -> float:
    """
    Score grid proximity via Overpass API.
    Queries OSM power infrastructure (lines, minor lines, substations, towers)
    within _SEARCH_RADIUS metres and scores based on distance to nearest feature.
    """
    query = f"""
    [out:json][timeout:25];
    (
      way["power"~"line|minor_line"](around:{_SEARCH_RADIUS},{lat},{lon});
      node["power"~"substation|tower"](around:{_SEARCH_RADIUS},{lat},{lon});
    );
    out geom;
    """
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            res = await client.post(OVERPASS_URL, data={"data": query})
            res.raise_for_status()
        elements = res.json().get("elements", [])
    except Exception:
        return 50.0  # fallback for this half only

    if not elements:
        # No grid infrastructure within search radius — remote site
        return _GRID_FLOOR

    min_dist_km = float("inf")
    for el in elements:
        if el.get("type") == "node":
            d = _haversine_km(lat, lon, el["lat"], el["lon"])
            min_dist_km = min(min_dist_km, d)
        elif el.get("type") == "way" and "geometry" in el:
            for pt in el["geometry"]:
                d = _haversine_km(lat, lon, pt["lat"], pt["lon"])
                min_dist_km = min(min_dist_km, d)

    return _grid_score_from_distance(min_dist_km)


async def fetch_infrastructure_score(lat: float, lon: float) -> dict:
    """
    Infrastructure score = average of road accessibility score and grid proximity score.
    Road score: Nominatim reverse geocode → nearest road type.
    Power score: Overpass API → distance to nearest OSM power line / substation / tower.
    Each half falls back independently to 50.0 on API failure.
    """
    road_score  = await _fetch_road_score(lat, lon)
    power_score = await _fetch_power_score(lat, lon)

    return {
        "infrastructure_score": round((road_score + power_score) / 2, 2),
        "road_distance_km": None,
        "power_distance_km": None,
    }
