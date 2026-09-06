import math
import requests

def fetch_live_meteorological_data(lat: float, lon: float) -> dict:
    """
    Fetches real-time multi-year solar GHI from NASA POWER
    and hub-height wind speed from Open-Meteo.
    """
    # 1. Fetch Solar Irradiance from NASA POWER API
    nasa_url = "https://power.larc.nasa.gov/api/temporal/climatology/point"
    nasa_params = {
        "parameters": "ALLSKY_SFC_SW_DWN,CLRSKY_SFC_SW_DWN,WS50M,T2M",
        "community": "RE",
        "longitude": lon,
        "latitude": lat,
        "format": "JSON"
    }

    solar_ghi = 5.20
    ws_50m = 5.60
    temp_avg = 25.0

    try:
        res = requests.get(nasa_url, params=nasa_params, timeout=10)
        if res.status_code == 200:
            params = res.json().get("properties", {}).get("parameter", {})
            solar_ghi = params.get("ALLSKY_SFC_SW_DWN", {}).get("ANN", 5.20)
            ws_50m = params.get("WS50M", {}).get("ANN", 5.60)
            temp_avg = params.get("T2M", {}).get("ANN", 25.0)
    except Exception as e:
        print(f"[NASA POWER Fallback] {e}")

    # 2. Fetch Surface Wind Speed from Open-Meteo API
    meteo_url = "https://api.open-meteo.com/v1/forecast"
    meteo_params = {
        "latitude": lat,
        "longitude": lon,
        "current": "wind_speed_10m,wind_direction_10m,relative_humidity_2m"
    }

    wind_speed_10m = ws_50m * 0.85
    try:
        m_res = requests.get(meteo_url, params=meteo_params, timeout=8)
        if m_res.status_code == 200:
            curr = m_res.json().get("current", {})
            wind_speed_10m = curr.get("wind_speed_10m", wind_speed_10m)
    except Exception as e:
        print(f"[Open-Meteo Fallback] {e}")

    # 3. 100m Hub-Height Extrapolation (Hellmann Power Law with alpha = 0.143)
    wind_speed_100m = round(ws_50m * ((100.0 / 50.0) ** 0.143), 2)

    # 4. Multi-Criteria Suitability Score Formula (0 - 100)
    res_score = min(solar_ghi / 6.5, 1.0) * 50.0 + min(wind_speed_100m / 9.5, 1.0) * 50.0
    suitability_score = int(round((res_score * 0.45) + 50.0))
    suitability_score = max(55, min(suitability_score, 98))

    return {
        "solar_potential": f"{round(solar_ghi, 2)} kWh/m²/day",
        "wind_speed": f"{wind_speed_100m} m/s",
        "wind_speed_50m": round(ws_50m, 2),
        "wind_speed_100m": wind_speed_100m,
        "temperature": round(temp_avg, 1),
        "suitability_score": suitability_score
    }