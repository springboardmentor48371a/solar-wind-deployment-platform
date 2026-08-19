import httpx
from typing import Optional

NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"

async def reverse_geocode(lat: float, lon: float) -> Optional[dict]:
    """
    Reverse geocode coordinates to get location details.
    Returns None if coordinates are invalid or point to ocean/nowhere.
    """
    headers = {"User-Agent": "SolarWindPlatform/1.0"}
    params = {"lat": lat, "lon": lon, "format": "json", "addressdetails": 1}

    async with httpx.AsyncClient(timeout=10) as client:
        res = await client.get(NOMINATIM_URL, params=params, headers=headers)
        if res.status_code != 200:
            return None
        data = res.json()

    # If Nominatim returns an error key, coordinates are invalid
    if "error" in data:
        return None

    address = data.get("address", {})

    # Extract meaningful location parts
    country = address.get("country")
    state = address.get("state") or address.get("province") or address.get("region")
    city = (address.get("city") or address.get("town") or
            address.get("village") or address.get("county") or
            address.get("municipality"))
    display_name = data.get("display_name", "")

    # Reject if no country found — likely ocean or invalid
    if not country:
        return None

    return {
        "country": country,
        "state": state,
        "city": city,
        "display_name": display_name,
        "region_name": state or country,
    }
