from datetime import date, timedelta
from typing import Optional
import httpx

NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"
OPEN_TOPO_URL  = "https://api.opentopodata.org/v1/srtm30m"

async def fetch_nasa_power(lat: float, lon: float, start: date, end: date) -> dict:
    """Fetch solar irradiance and wind data from NASA POWER API."""
    params = {
        "parameters": "ALLSKY_SFC_SW_DWN,WS10M,WS50M,WD10M,T2M_MAX,T2M_MIN,T2M,PRECTOTCORR,CLOUD_AMT",
        "community": "RE",
        "longitude": lon,
        "latitude": lat,
        "start": start.strftime("%Y%m%d"),
        "end": end.strftime("%Y%m%d"),
        "format": "JSON",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        res = await client.get(NASA_POWER_URL, params=params)
        res.raise_for_status()
    return res.json()["properties"]["parameter"]

async def fetch_open_meteo(lat: float, lon: float, start: date, end: date) -> dict:
    """Fetch humidity and additional climate data from Open-Meteo."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": "relative_humidity_2m_max",
        "timezone": "auto",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        res = await client.get(OPEN_METEO_URL, params=params)
        res.raise_for_status()
    data = res.json()
    dates = data["daily"]["time"]
    humidity = data["daily"]["relative_humidity_2m_max"]
    return dict(zip(dates, humidity))

async def fetch_elevation(lat: float, lon: float) -> Optional[float]:
    """Fetch elevation from OpenTopoData SRTM30m dataset."""
    async with httpx.AsyncClient(timeout=15) as client:
        res = await client.get(OPEN_TOPO_URL, params={"locations": f"{lat},{lon}"})
        res.raise_for_status()
    results = res.json().get("results", [])
    return results[0]["elevation"] if results else None

def parse_nasa_daily(nasa_data: dict, target_date: date) -> dict:
    """Extract a single day's values from NASA POWER response."""
    key = target_date.strftime("%Y%m%d")
    def get(param):
        val = nasa_data.get(param, {}).get(key)
        return None if val in (None, -999.0, -999) else val

    irradiance = get("ALLSKY_SFC_SW_DWN")
    return {
        "solar_irradiance": irradiance,
        "peak_sun_hours": round(irradiance / 1000 * 24, 2) if irradiance else None,
        "wind_speed": get("WS10M"),
        "wind_speed_50m": get("WS50M"),
        "wind_direction": get("WD10M"),
        "temperature_max": get("T2M_MAX"),
        "temperature_min": get("T2M_MIN"),
        "temperature_avg": get("T2M"),
        "rainfall": get("PRECTOTCORR"),
        "cloud_cover": get("CLOUD_AMT"),
    }

async def collect_environmental_data(lat: float, lon: float, days: int = 30) -> list[dict]:
    """
    Main function — collects last N days of environmental data for a location.
    Returns list of daily records ready to be saved to DB.
    """
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=days - 1)

    nasa_data = await fetch_nasa_power(lat, lon, start, end)
    humidity_map = await fetch_open_meteo(lat, lon, start, end)
    elevation = await fetch_elevation(lat, lon)

    records = []
    current = start
    while current <= end:
        daily = parse_nasa_daily(nasa_data, current)
        daily["date"] = current
        daily["humidity"] = humidity_map.get(current.isoformat())
        daily["elevation"] = elevation
        daily["source"] = "nasa_power+open_meteo"
        records.append(daily)
        current += timedelta(days=1)

    return records
