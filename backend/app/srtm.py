import os
import json
import logging
import httpx
import math
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_PATH = os.path.join(APP_DIR, "data", "srtm_cache.json")

def load_srtm_cache() -> Dict[str, Any]:
    if not os.path.exists(CACHE_PATH):
        return {}
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading SRTM cache: {e}")
        return {}

def save_srtm_cache(cache_data: Dict[str, Any]) -> None:
    try:
        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving SRTM cache: {e}")

def fetch_srtm_data(latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
    """
    Fetches SRTM elevation from OpenTopoData API and derives terrain slope.
    Returns:
    {
        "elevation": float,
        "terrain_slope": float,
        "source": "SRTM"
    }
    """
    cache_key = f"{round(latitude, 4)}_{round(longitude, 4)}"
    cache = load_srtm_cache()
    if cache_key in cache:
        logger.info(f"SRTM Cache hit for key {cache_key}")
        return cache[cache_key]

    # Calculate offsets for a 90m grid to calculate slope
    # 1 deg lat = 111.32 km. 90m = 0.000808 deg
    lat_offset = 0.000808
    # 1 deg lon = 111.32 * cos(lat) km.
    lon_offset = 0.09 / (111.32 * math.cos(math.radians(latitude)))

    locations = [
        f"{latitude},{longitude}", # center
        f"{latitude + lat_offset},{longitude}", # north
        f"{latitude - lat_offset},{longitude}", # south
        f"{latitude},{longitude + lon_offset}", # east
        f"{latitude},{longitude - lon_offset}"  # west
    ]
    
    locations_str = "|".join(locations)
    url = f"https://api.opentopodata.org/v1/srtm30m?locations={locations_str}"
    
    try:
        res = httpx.get(url, timeout=15.0)
        res.raise_for_status()
        data = res.json()
        
        results = data.get("results", [])
        if len(results) != 5:
            logger.error(f"Unexpected SRTM result length: {len(results)}")
            return None
            
        elev_center = results[0].get("elevation")
        elev_north = results[1].get("elevation")
        elev_south = results[2].get("elevation")
        elev_east = results[3].get("elevation")
        elev_west = results[4].get("elevation")
        
        if elev_center is None:
            return None
            
        # Slope calculation using finite difference
        # dz/dy (North-South)
        if elev_north is not None and elev_south is not None:
            dz_dy = (elev_north - elev_south) / (2 * 90.0)
        else:
            dz_dy = 0.0
            
        # dz/dx (East-West)
        if elev_east is not None and elev_west is not None:
            dz_dx = (elev_east - elev_west) / (2 * 90.0)
        else:
            dz_dx = 0.0
            
        slope_rad = math.atan(math.sqrt(dz_dx**2 + dz_dy**2))
        slope_deg = math.degrees(slope_rad)
        
        result = {
            "elevation": round(float(elev_center), 1),
            "terrain_slope": round(float(slope_deg), 2),
            "source": "SRTM"
        }
        
        cache[cache_key] = result
        save_srtm_cache(cache)
        return result
        
    except Exception as e:
        logger.warning(f"SRTM query failed: {e}")
        return None
