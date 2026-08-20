import sqlite3
import numpy as np
import requests
from datetime import datetime, timedelta
from services.elevation import get_elevation, get_slope
from services.osm import get_nearest_road_distance, get_nearest_power_line_distance
from services.sentinel import get_ndvi

NASA_POWER_API = "https://power.larc.nasa.gov/api/power"

def fetch_nasa_data(lat, lon):
    """Fetch environmental data from NASA POWER"""
    end = datetime.now().strftime("%Y%m%d")
    start = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
    params = {
        "request": "execute",
        "parameters": "ALLSKY_SFC_SW_DWN,T2M,PRECTOTCORR,WS10M,CLOUD_AMT",
        "startDate": start,
        "endDate": end,
        "userCommunity": "RE",
        "format": "JSON",
        "latitude": lat,
        "longitude": lon
    }
    try:
        r = requests.get(NASA_POWER_API + "/daily", params=params, timeout=30)
        data = r.json()
        param = data.get("properties", {}).get("parameter", {})
        irradiance = np.mean(list(param.get("ALLSKY_SFC_SW_DWN", {}).values())) if param.get("ALLSKY_SFC_SW_DWN") else 5.0
        temp = np.mean(list(param.get("T2M", {}).values())) if param.get("T2M") else 25.0
        rain = np.mean(list(param.get("PRECTOTCORR", {}).values())) * 365 if param.get("PRECTOTCORR") else 800.0
        wind = np.mean(list(param.get("WS10M", {}).values())) if param.get("WS10M") else 5.0
        cloud = np.mean(list(param.get("CLOUD_AMT", {}).values())) if param.get("CLOUD_AMT") else 30.0
        return {
            "solar_irradiance": irradiance,
            "temperature": temp,
            "rainfall": rain,
            "wind_speed": wind,
            "cloud_cover": cloud
        }
    except:
        return {
            "solar_irradiance": 5.0,
            "temperature": 25.0,
            "rainfall": 800.0,
            "wind_speed": 5.0,
            "cloud_cover": 30.0
        }

def collect_data_for_location(lat, lon):
    """Collect all data for a location"""
    # NASA data
    env = fetch_nasa_data(lat, lon)
    
    # Elevation & slope
    elevation = get_elevation(lat, lon)
    slope = get_slope(lat, lon)
    
    # Infrastructure
    road_dist = get_nearest_road_distance(lat, lon)
    power_dist = get_nearest_power_line_distance(lat, lon)
    
    # NDVI (satellite)
    ndvi = get_ndvi(lat, lon)
    
    # Calculate suitability score using PDF formula
    solar_score = min(env['solar_irradiance'] / 6.0, 1.0) * 100
    wind_score = min(env['wind_speed'] / 10.0, 1.0) * 100
    renewable_score = (solar_score + wind_score) / 2
    
    geo_score = 100 - min(slope, 30) * 2 + (1 - min(elevation / 2000, 1)) * 20
    geo_score = min(geo_score, 100)
    
    infra_score = 100 - (min(road_dist, 50) * 2 + min(power_dist, 50) * 1) / 1.5
    infra_score = max(0, min(infra_score, 100))
    
    env_impact = (1 - ndvi) * 100
    env_impact = min(env_impact, 100)
    
    # Assume land_area = 100 acres (can be improved)
    land_area = 100
    eco_score = min(land_area / 200, 1) * 100
    
    overall = (renewable_score * 0.35 +
               geo_score * 0.25 +
               infra_score * 0.15 +
               env_impact * 0.15 +
               eco_score * 0.10)
    
    return {
        "latitude": lat,
        "longitude": lon,
        "solar_irradiance": env['solar_irradiance'],
        "temperature": env['temperature'],
        "rainfall": env['rainfall'],
        "wind_speed": env['wind_speed'],
        "cloud_cover": env['cloud_cover'],
        "elevation": elevation,
        "slope": slope,
        "ndvi": ndvi,
        "road_distance": road_dist,
        "power_distance": power_dist,
        "land_area": land_area,
        "suitability_score": overall,
        "renewable_score": renewable_score,
        "geo_score": geo_score,
        "infra_score": infra_score,
        "env_score": env_impact,
        "eco_score": eco_score
    }

def collect_dataset(num_samples=200):
    """Collect data for multiple random locations"""
    dataset = []
    for i in range(num_samples):
        lat = np.random.uniform(-60, 60)
        lon = np.random.uniform(-180, 180)
        print(f"Collecting for {lat:.4f}, {lon:.4f} ({i+1}/{num_samples})")
        try:
            data = collect_data_for_location(lat, lon)
            dataset.append(data)
        except Exception as e:
            print(f"Error: {e}")
    return dataset