import httpx
from typing import Dict, Any, Optional

NASA_POWER_BASE_URL = "https://power.larc.nasa.gov/api/temporal/climatology/point"

async def fetch_nasa_environmental_data(latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Queries the official NASA POWER Climatology API to retrieve multi-year
    satellite solar irradiance, temperature, precipitation, and cloud cover.
    """
    params = {
        "parameters": "ALLSKY_SFC_SW_DWN,T2M,PRECTOTCORR,CLOUD_AMT,WS50M",
        "community": "RE",
        "longitude": round(longitude, 4),
        "latitude": round(latitude, 4),
        "format": "JSON"
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(NASA_POWER_BASE_URL, params=params)
            
        if response.status_code != 200:
            return get_fallback_environmental_data(latitude, longitude)

        data = response.json()
        props = data.get("properties", {}).get("parameter", {})

        # Extract annual 13-month averages ('ANN') from NASA POWER
        solar_ghi = props.get("ALLSKY_SFC_SW_DWN", {}).get("ANN", 5.45)
        avg_temp = props.get("T2M", {}).get("ANN", 26.5)
        daily_rain_mm = props.get("PRECTOTCORR", {}).get("ANN", 1.2)
        cloud_cover = props.get("CLOUD_AMT", {}).get("ANN", 42.0)
        wind_speed_50m = props.get("WS50M", {}).get("ANN", 5.8)

        # Annual rainfall estimate: daily precipitation rate * 365 days
        annual_rainfall = round(daily_rain_mm * 365.0, 1) if daily_rain_mm > 0 else 120.0

        # Estimate preliminary Capacity Factor (CF%) based on GHI
        capacity_factor = round(min(max(solar_ghi * 4.2, 16.0), 28.5), 1)
        est_yield = round(capacity_factor * 87.6 * 0.75, 1)

        return {
            "source": "NASA POWER Climatology API (Live)",
            "solar_ghi": round(solar_ghi, 2),
            "avg_temp": round(avg_temp, 1),
            "rainfall_mm": annual_rainfall,
            "cloud_cover_pct": round(cloud_cover, 1),
            "wind_speed_50m": round(wind_speed_50m, 2),
            "capacity_factor": capacity_factor,
            "est_yield_gwh": est_yield
        }

    except Exception as exc:
        print(f"NASA POWER API sync error: {exc}. Using deterministic regional baseline.")
        return get_fallback_environmental_data(latitude, longitude)

def get_fallback_environmental_data(latitude: float, longitude: float) -> Dict[str, Any]:
    """Fallback generator based on Indian latitude/longitude coordinates if offline."""
    lat_factor = max(0.85, 1.0 - abs(latitude - 26.0) * 0.02)
    ghi = round(5.2 * lat_factor + 0.35, 2)
    temp = round(27.8 - abs(latitude - 24.0) * 0.4, 1)
    
    return {
        "source": "Regional Solar Baseline Fallback",
        "solar_ghi": ghi,
        "avg_temp": temp,
        "rainfall_mm": 145.0,
        "cloud_cover_pct": 38.5,
        "wind_speed_50m": 5.4,
        "capacity_factor": round(ghi * 4.1, 1),
        "est_yield_gwh": 1380.0
    }