import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

NASA_POWER_API = "https://power.larc.nasa.gov/api/power"

def fetch_environmental_data(lat: float, lon: float) -> Dict[str, Any]:
    """
    Fetch complete environmental data from NASA POWER API
    """
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
    
    result = {
        "success": False,
        "data": {},
        "error": None
    }
    
    try:
        # Fetch solar irradiance
        irradiance = fetch_solar_irradiance(lat, lon, start_date, end_date)
        if not irradiance["success"]:
            result["error"] = irradiance.get("error", "Failed to fetch irradiance")
            return result
        
        # Fetch temperature
        temp = fetch_temperature(lat, lon, start_date, end_date)
        if not temp["success"]:
            result["error"] = temp.get("error", "Failed to fetch temperature")
            return result
        
        # Fetch precipitation
        precip = fetch_precipitation(lat, lon, start_date, end_date)
        if not precip["success"]:
            result["error"] = precip.get("error", "Failed to fetch precipitation")
            return result
        
        # Fetch wind speed
        wind = fetch_wind_speed(lat, lon, start_date, end_date)
        if not wind["success"]:
            result["error"] = wind.get("error", "Failed to fetch wind speed")
            return result
        
        # Fetch cloud cover
        cloud = fetch_cloud_cover(lat, lon, start_date, end_date)
        if not cloud["success"]:
            result["error"] = cloud.get("error", "Failed to fetch cloud cover")
            return result
        
        result["success"] = True
        result["data"] = {
            "solar_irradiance": round(irradiance["avg_value"], 2),  # kWh/m²/day
            "temperature": round(temp["avg_value"], 2),  # °C
            "rainfall": round(precip["avg_value"], 2),  # mm
            "wind_speed": round(wind["avg_value"], 2),  # m/s
            "cloud_cover": round(cloud["avg_value"], 2),  # %
            "lat": lat,
            "lon": lon,
            "fetch_date": datetime.now().isoformat()
        }
        
        return result
        
    except Exception as e:
        result["error"] = str(e)
        return result

def fetch_solar_irradiance(lat: float, lon: float, start_date: str, end_date: str) -> Dict[str, Any]:
    """Fetch solar irradiance from NASA POWER API"""
    try:
        url = f"{NASA_POWER_API}/daily"
        params = {
            "request": "execute",
            "parameters": "ALLSKY_SFC_SW_DWN",
            "startDate": start_date,
            "endDate": end_date,
            "userCommunity": "RE",
            "format": "JSON",
            "latitude": lat,
            "longitude": lon
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        values = data.get("properties", {}).get("parameter", {}).get("ALLSKY_SFC_SW_DWN", {})
        if values:
            avg_value = sum(values.values()) / len(values)
            return {"success": True, "avg_value": avg_value}
        
        return {"success": False, "error": "No data found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def fetch_temperature(lat: float, lon: float, start_date: str, end_date: str) -> Dict[str, Any]:
    """Fetch temperature from NASA POWER API"""
    try:
        url = f"{NASA_POWER_API}/daily"
        params = {
            "request": "execute",
            "parameters": "T2M",
            "startDate": start_date,
            "endDate": end_date,
            "userCommunity": "RE",
            "format": "JSON",
            "latitude": lat,
            "longitude": lon
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        values = data.get("properties", {}).get("parameter", {}).get("T2M", {})
        if values:
            avg_value = sum(values.values()) / len(values)
            return {"success": True, "avg_value": avg_value}
        
        return {"success": False, "error": "No data found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def fetch_precipitation(lat: float, lon: float, start_date: str, end_date: str) -> Dict[str, Any]:
    """Fetch precipitation from NASA POWER API"""
    try:
        url = f"{NASA_POWER_API}/daily"
        params = {
            "request": "execute",
            "parameters": "PRECTOTCORR",
            "startDate": start_date,
            "endDate": end_date,
            "userCommunity": "RE",
            "format": "JSON",
            "latitude": lat,
            "longitude": lon
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        values = data.get("properties", {}).get("parameter", {}).get("PRECTOTCORR", {})
        if values:
            avg_value = sum(values.values()) / len(values) * 365  # Convert to mm/year
            return {"success": True, "avg_value": avg_value}
        
        return {"success": False, "error": "No data found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def fetch_wind_speed(lat: float, lon: float, start_date: str, end_date: str) -> Dict[str, Any]:
    """Fetch wind speed from NASA POWER API"""
    try:
        url = f"{NASA_POWER_API}/daily"
        params = {
            "request": "execute",
            "parameters": "WS10M",
            "startDate": start_date,
            "endDate": end_date,
            "userCommunity": "RE",
            "format": "JSON",
            "latitude": lat,
            "longitude": lon
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        values = data.get("properties", {}).get("parameter", {}).get("WS10M", {})
        if values:
            avg_value = sum(values.values()) / len(values)
            return {"success": True, "avg_value": avg_value}
        
        return {"success": False, "error": "No data found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def fetch_cloud_cover(lat: float, lon: float, start_date: str, end_date: str) -> Dict[str, Any]:
    """Fetch cloud cover from NASA POWER API"""
    try:
        url = f"{NASA_POWER_API}/daily"
        params = {
            "request": "execute",
            "parameters": "CLOUD_AMT",
            "startDate": start_date,
            "endDate": end_date,
            "userCommunity": "RE",
            "format": "JSON",
            "latitude": lat,
            "longitude": lon
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        values = data.get("properties", {}).get("parameter", {}).get("CLOUD_AMT", {})
        if values:
            avg_value = sum(values.values()) / len(values)
            return {"success": True, "avg_value": avg_value}
        
        return {"success": False, "error": "No data found"}
    except Exception as e:
        return {"success": False, "error": str(e)}