import os
import json
import logging
import httpx
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_PATH = os.path.join(APP_DIR, "data", "landcover_cache.json")

# Esri Sentinel-2 10m Land Cover Classes
# Based on the official classification schema
LAND_COVER_CLASS_MAP = {
    1: "Water",
    2: "Forest",
    4: "Flooded Vegetation",
    5: "Agriculture",
    7: "Built Area",
    8: "Desert/Barren",
    9: "Snow/Ice",
    10: "Clouds",
    11: "Rangeland/Scrub"
}

def load_landcover_cache() -> Dict[str, Any]:
    if not os.path.exists(CACHE_PATH):
        return {}
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading Land Cover cache: {e}")
        return {}

def save_landcover_cache(cache_data: Dict[str, Any]) -> None:
    try:
        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving Land Cover cache: {e}")

def fetch_esri_landcover(latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
    """
    Fetches land cover class from Esri Sentinel-2 10m Land Cover ImageServer using the identify operation.
    """
    cache_key = f"{round(latitude, 4)}_{round(longitude, 4)}"
    cache = load_landcover_cache()
    if cache_key in cache:
        logger.info(f"Land Cover Cache hit for key {cache_key}")
        return cache[cache_key]

    url = "https://ic.imagery1.arcgis.com/arcgis/rest/services/Sentinel2_10m_LandCover/ImageServer/identify"
    
    # We use inSR=4326 for WGS84 lat/lon
    params = {
        "geometry": json.dumps({
            "x": longitude,
            "y": latitude,
            "spatialReference": {"wkid": 4326}
        }),
        "geometryType": "esriGeometryPoint",
        "f": "json"
    }

    try:
        res = httpx.get(url, params=params, timeout=15.0)
        res.raise_for_status()
        data = res.json()
        
        pixel_value_str = data.get("value")
        if not pixel_value_str or pixel_value_str == "NoData":
            return None
            
        try:
            pixel_value = int(pixel_value_str)
        except ValueError:
            return None
            
        mapped_type = LAND_COVER_CLASS_MAP.get(pixel_value, "Plain")
        
        result = {
            "class_value": pixel_value,
            "mapped_land_type": mapped_type,
            "source": "Esri Sentinel-2 10m Land Cover, derived from Copernicus Sentinel-2 imagery"
        }
        
        cache[cache_key] = result
        save_landcover_cache(cache)
        return result
        
    except Exception as e:
        logger.warning(f"Esri Land Cover query failed: {e}")
        return None
