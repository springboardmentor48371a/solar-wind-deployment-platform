import requests
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
OPENWEATHER_API = "https://api.openweathermap.org/data/2.5"

def fetch_weather(lat: float, lon: float) -> Dict[str, Any]:
    """
    Fetch current weather data from OpenWeather API
    """
    if not OPENWEATHER_API_KEY:
        return {"success": False, "error": "OpenWeather API key not configured"}
    
    url = f"{OPENWEATHER_API}/weather"
    
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return {
            "success": True,
            "temperature": data.get("main", {}).get("temp"),
            "wind_speed": data.get("wind", {}).get("speed"),
            "wind_direction": data.get("wind", {}).get("deg"),
            "cloud_cover": data.get("clouds", {}).get("all"),
            "humidity": data.get("main", {}).get("humidity"),
            "weather": data.get("weather", [{}])[0].get("description"),
            "data": data
        }
    except Exception as e:
        return {"success": False, "error": str(e)}