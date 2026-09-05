import httpx

NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
HEADERS = {"User-Agent": "SolarWindPlatform/1.0"}

# Road type → score (0–100) based on accessibility
_ROAD_SCORES = {
    "motorway": 100, "trunk": 95, "primary": 90,
    "secondary": 75, "tertiary": 60,
    "unclassified": 40, "residential": 35,
    "track": 15, "path": 10, "footway": 5,
}

async def fetch_infrastructure_score(lat: float, lon: float) -> dict:
    """
    Estimate infrastructure score from Nominatim reverse geocode.
    Road score based on nearest road type; power score inferred from road quality.
    """
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(
                NOMINATIM_URL,
                params={"lat": lat, "lon": lon, "format": "json", "zoom": 17},
                headers=HEADERS,
            )
            res.raise_for_status()
        data = res.json()
    except Exception:
        return {"infrastructure_score": 50.0, "road_distance_km": None, "power_distance_km": None}

    obj_class = data.get("class", "")
    obj_type  = data.get("type", "")

    if obj_class == "highway":
        road_score = _ROAD_SCORES.get(obj_type, 30)
    else:
        # No road at this zoom level — remote location
        road_score = 10

    # Power infrastructure correlates strongly with road quality
    power_score = min(100, road_score + 10)

    return {
        "infrastructure_score": round((road_score + power_score) / 2, 2),
        "road_distance_km": None,
        "power_distance_km": None,
    }
