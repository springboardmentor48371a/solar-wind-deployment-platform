import math
from datetime import date, timedelta
from typing import Optional
import httpx

NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"
OPEN_TOPO_URL  = "https://api.opentopodata.org/v1/srtm30m"

async def fetch_nasa_power(lat: float, lon: float, start: date, end: date) -> dict:
    """Fetch solar irradiance and wind data from NASA POWER API."""
    params = {
        "parameters": "ALLSKY_SFC_SW_DWN,WS10M,WS50M,WD10M,T2M_MAX,T2M_MIN,T2M,PRECTOTCORR",
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

async def fetch_open_meteo(lat: float, lon: float, start: date, end: date) -> tuple[dict, dict]:
    """Fetch humidity and cloud cover from Open-Meteo."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": "relative_humidity_2m_max,cloudcover_mean",
        "timezone": "auto",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        res = await client.get(OPEN_METEO_URL, params=params)
        res.raise_for_status()
    data = res.json()
    dates     = data["daily"]["time"]
    humidity  = data["daily"]["relative_humidity_2m_max"]
    cloud     = data["daily"]["cloudcover_mean"]
    return dict(zip(dates, humidity)), dict(zip(dates, cloud))

async def fetch_elevation_and_slope(lat: float, lon: float) -> tuple[Optional[float], Optional[float], Optional[float]]:
    """
    Fetch elevation, slope, and aspect from OpenTopoData in a single request.
    Samples 4 points ~500m apart.
    Returns (elevation, slope_deg, aspect_deg).
    aspect_deg: 0=north, 90=east, 180=south, 270=west (0-360)
    """
    offset = 0.0045  # ~500m in degrees
    locations = f"{lat},{lon}|{lat+offset},{lon}|{lat},{lon+offset}|{lat-offset},{lon}"
    async with httpx.AsyncClient(timeout=15) as client:
        res = await client.get(OPEN_TOPO_URL, params={"locations": locations})
        res.raise_for_status()
    results = res.json().get("results", [])
    if len(results) < 4:
        elev = results[0]["elevation"] if results else None
        return elev, None, None
    e_center = results[0]["elevation"] or 0
    e_north  = results[1]["elevation"] or 0
    e_east   = results[2]["elevation"] or 0
    e_south  = results[3]["elevation"] or 0
    ns_diff   = (e_north - e_south) / 1000.0
    ew_diff   = (e_east  - e_center) / 500.0
    slope_deg  = round(math.degrees(math.atan(math.sqrt(ns_diff**2 + ew_diff**2))), 2)
    aspect_raw = math.degrees(math.atan2(e_north - e_south, e_east - e_center))
    aspect_deg = round(aspect_raw % 360, 2)
    return e_center, slope_deg, aspect_deg

async def fetch_elevation(lat: float, lon: float) -> Optional[float]:
    """Fetch elevation only — used by site creation preview."""
    elev, _, _ = await fetch_elevation_and_slope(lat, lon)
    return elev

def parse_nasa_daily(nasa_data: dict, target_date: date) -> dict:
    """Extract a single day's values from NASA POWER response."""
    key = target_date.strftime("%Y%m%d")
    def get(param):
        val = nasa_data.get(param, {}).get(key)
        return None if val in (None, -999.0, -999) else val

    irradiance = get("ALLSKY_SFC_SW_DWN")
    return {
        "solar_irradiance": irradiance,
        "peak_sun_hours": round(irradiance, 2) if irradiance else None,
        "wind_speed": get("WS10M"),
        "wind_speed_50m": get("WS50M"),
        "wind_direction": get("WD10M"),
        "temperature_max": get("T2M_MAX"),
        "temperature_min": get("T2M_MIN"),
        "temperature_avg": get("T2M"),
        "rainfall": get("PRECTOTCORR"),
        "cloud_cover": None,  # sourced from Open-Meteo instead
    }

def _ndvi_proxy(rainfall: Optional[float], temperature: Optional[float],
                irradiance: Optional[float], cloud_cover: Optional[float]) -> float:
    """
    Estimate NDVI from climate variables (-1 to 1).
    High rainfall + moderate temp = vegetation (positive NDVI)
    Low rainfall + high temp + high irradiance = barren/arid (low NDVI)
    """
    rain_score  = min((rainfall or 0) / 10.0, 1.0) * 0.4
    solar_score = min((irradiance or 0) / 7.0, 1.0) * (1 - (cloud_cover or 0) / 100) * 0.3
    heat_penalty = max(0, ((temperature or 25) - 35) / 10.0) * 0.3
    raw = rain_score + solar_score - heat_penalty
    return round(max(-1.0, min(1.0, raw)), 4)

async def collect_environmental_data(lat: float, lon: float, days: int = 30, elevation: Optional[float] = None) -> list[dict]:
    """
    Main function — collects last N days of environmental data for a location.
    Returns list of daily records ready to be saved to DB.
    """
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=days - 1)

    nasa_data = await fetch_nasa_power(lat, lon, start, end)
    humidity_map, cloud_map = await fetch_open_meteo(lat, lon, start, end)

    # Fetch elevation + slope + aspect together (4-point grid)
    if elevation is None:
        elevation, slope, aspect = await fetch_elevation_and_slope(lat, lon)
    else:
        _, slope, aspect = await fetch_elevation_and_slope(lat, lon)

    records = []
    current = start
    while current <= end:
        daily = parse_nasa_daily(nasa_data, current)
        daily["date"]             = current
        daily["humidity"]         = humidity_map.get(current.isoformat())
        daily["cloud_cover"]      = cloud_map.get(current.isoformat())
        daily["elevation"]        = elevation
        daily["land_slope"]       = slope
        daily["aspect_deg"]       = aspect
        daily["vegetation_index"] = _ndvi_proxy(
            daily.get("rainfall"),
            daily.get("temperature_avg"),
            daily.get("solar_irradiance"),
            daily.get("cloud_cover"),
        )
        daily["source"] = "nasa_power+open_meteo"
        records.append(daily)
        current += timedelta(days=1)

    return records
