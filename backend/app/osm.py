import os
import json
import logging
import httpx
import geopandas as gpd
from shapely.geometry import Point, LineString
import pandas as pd
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# Constants consistent with the backend GIS engine
PROJ_CRS = "EPSG:32643"  # UTM Zone 43N for Western India (Gujarat/Rajasthan)
GEOGRAPHIC_CRS = "EPSG:4326"

# Cache file path
APP_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_PATH = os.path.join(APP_DIR, "data", "osm_cache.json")

# Filter for road classes relevant to motor vehicles
RELEVANT_ROAD_CLASSES = {
    "motorway", "trunk", "primary", "secondary", "tertiary",
    "unclassified", "residential", "service", "motorway_link",
    "trunk_link", "primary_link", "secondary_link", "tertiary_link"
}

def load_osm_cache() -> Dict[str, Any]:
    """Loads the OSM cache from disk."""
    if not os.path.exists(CACHE_PATH):
        return {}
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading OSM cache: {e}")
        return {}

def save_osm_cache(cache_data: Dict[str, Any]) -> None:
    """Saves the OSM cache back to disk."""
    try:
        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving OSM cache: {e}")

def calculate_nearest_geometries(
    site_lat: float, 
    site_lon: float, 
    features: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Vectorized calculation of distances in kilometers to site using EPSG:32643 UTM projection.
    Returns the nearest feature coordinates, calculated distance, and details.
    """
    if not features:
        return {"distance": float('inf'), "name": "None Found", "id": None}

    site_point = Point(site_lon, site_lat)
    site_gdf = gpd.GeoDataFrame(geometry=[site_point], crs=GEOGRAPHIC_CRS).to_crs(PROJ_CRS)
    site_geom_proj = site_gdf.geometry.iloc[0]

    geometries = []
    metadata = []

    for f in features:
        geom = f.get("geometry")
        if not geom:
            continue
        geometries.append(geom)
        metadata.append({
            "id": f.get("id"),
            "name": f.get("name", "Unnamed"),
            "class": f.get("class", "unknown")
        })

    if not geometries:
        return {"distance": float('inf'), "name": "None Found", "id": None}

    # Vectorized GeoPandas projection and calculation
    features_gdf = gpd.GeoDataFrame(geometry=geometries, crs=GEOGRAPHIC_CRS).to_crs(PROJ_CRS)
    distances_m = features_gdf.geometry.distance(site_geom_proj)

    # Find the nearest element
    min_idx = distances_m.idxmin()
    min_distance_km = float(distances_m[min_idx] / 1000.0)
    nearest_meta = metadata[min_idx]

    return {
        "distance": round(min_distance_km, 2),
        "name": nearest_meta["name"],
        "class": nearest_meta["class"],
        "id": nearest_meta["id"]
    }

def fetch_osm_infrastructure(latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
    """
    Queries OpenStreetMap (OSM) via Overpass API to find nearby highways and power substations,
    calculates precise UTM projection distances, and caches results to limit API calls.
    
    Fallback calculations are avoided if the OSM connection fails.
    """
    # 1. Check local cache
    cache_key = f"{round(latitude, 2)}_{round(longitude, 2)}"
    cache = load_osm_cache()
    if cache_key in cache:
        logger.info(f"OSM Cache hit for key {cache_key}")
        return cache[cache_key]

    # 2. Overpass API configuration and endpoints
    endpoints = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter"
    ]
    headers = {
        "User-Agent": "RenewableIQPlatform/1.0 (sanjeev@renewable.in; developer query)",
        "Referer": "https://github.com/sanjeev/AI_Solar_And_Wind"
    }

    # Overpass queries parameterized by radius:
    # Roads Query: radius 20 km (20000 meters)
    road_query = f"""
    [out:json][timeout:30];
    (
      way["highway"](around:20000, {latitude}, {longitude});
    );
    out geom;
    """

    # Substation Query: radius 50 km (50000 meters)
    substation_query = f"""
    [out:json][timeout:30];
    (
      node["power"="substation"](around:50000, {latitude}, {longitude});
      way["power"="substation"](around:50000, {latitude}, {longitude});
    );
    out center;
    """

    road_elements = []
    substation_elements = []
    osm_accessed = False

    # Try query loop
    for url in endpoints:
        logger.info(f"Querying OpenStreetMap infrastructure at: {url}")
        try:
            # Query Substations
            sub_res = httpx.post(url, data={"data": substation_query}, headers=headers, timeout=20.0)
            if sub_res.status_code == 200:
                substation_elements = sub_res.json().get("elements", [])
                
                # Query Roads
                road_res = httpx.post(url, data={"data": road_query}, headers=headers, timeout=20.0)
                if road_res.status_code == 200:
                    road_elements = road_res.json().get("elements", [])
                    osm_accessed = True
                    break
        except Exception as e:
            logger.warning(f"OSM query to {url} failed: {e}")
            continue

    if not osm_accessed:
        logger.error("All global OpenStreetMap Overpass servers failed or timed out.")
        return None

    # 3. Process Roads
    valid_roads = []
    for el in road_elements:
        tags = el.get("tags", {})
        hw_class = tags.get("highway", "")
        # Exclude clearly irrelevant footways, cycleways, tracks, etc.
        if hw_class not in RELEVANT_ROAD_CLASSES:
            continue
            
        geom_points = el.get("geometry", [])
        if len(geom_points) < 2:
            continue
            
        # Construct LineString
        line_coords = [(pt["lon"], pt["lat"]) for pt in geom_points]
        valid_roads.append({
            "id": el.get("id"),
            "name": tags.get("name", tags.get("ref", "Unnamed Road")),
            "class": hw_class,
            "geometry": LineString(line_coords)
        })

    # 4. Process Substations
    valid_substations = []
    for el in substation_elements:
        tags = el.get("tags", {})
        lat_val = el.get("lat") or el.get("center", {}).get("lat")
        lon_val = el.get("lon") or el.get("center", {}).get("lon")
        if not lat_val or not lon_val:
            continue
            
        valid_substations.append({
            "id": el.get("id"),
            "name": tags.get("name", "Unnamed Substation"),
            "class": "substation",
            "geometry": Point(lon_val, lat_val)
        })

    # 5. Distance Calculations
    road_info = calculate_nearest_geometries(latitude, longitude, valid_roads)
    sub_info = calculate_nearest_geometries(latitude, longitude, valid_substations)

    # If nothing found, default distance to standard out-of-range fallbacks
    nearest_road_dist = road_info["distance"] if road_info["distance"] != float('inf') else 999.0
    nearest_sub_dist = sub_info["distance"] if sub_info["distance"] != float('inf') else 999.0

    result = {
        "nearest_substation_distance": nearest_sub_dist,
        "nearest_substation_name": sub_info["name"],
        "road_distance": nearest_road_dist,
        "road_name": road_info["name"],
        "infra_data_source": "OpenStreetMap"
    }

    # 6. Save in Cache
    cache[cache_key] = result
    save_osm_cache(cache)
    logger.info(f"Cached OSM result under key {cache_key}")

    return result

def fetch_osm_protected_areas(latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
    '''
    Queries OpenStreetMap for protected areas near the coordinates.
    '''
    cache_key = f'protected_{round(latitude, 2)}_{round(longitude, 2)}'
    cache = load_osm_cache()
    if cache_key in cache:
        logger.info(f'OSM Protected Area Cache hit for key {cache_key}')
        return cache[cache_key]

    endpoints = [
        'https://overpass-api.de/api/interpreter',
        'https://overpass.kumi.systems/api/interpreter'
    ]
    headers = {
        'User-Agent': 'RenewableIQPlatform/1.0 (sanjeev@renewable.in; developer query)',
        'Referer': 'https://github.com/sanjeev/AI_Solar_And_Wind'
    }

    # Query protected areas within 2 km radius
    query = f'''
    [out:json][timeout:20];
    (
      way['boundary'='protected_area'](around:2000, {latitude}, {longitude});
      relation['boundary'='protected_area'](around:2000, {latitude}, {longitude});
      way['leisure'='nature_reserve'](around:2000, {latitude}, {longitude});
      relation['leisure'='nature_reserve'](around:2000, {latitude}, {longitude});
    );
    out tags;
    '''

    accessed = False
    elements = []
    
    for url in endpoints:
        try:
            res = httpx.post(url, data={'data': query}, headers=headers, timeout=15.0)
            if res.status_code == 200:
                elements = res.json().get('elements', [])
                accessed = True
                break
        except Exception as e:
            logger.warning(f'OSM protected area query to {url} failed: {e}')
            continue

    if not accessed:
        return None

    is_protected = len(elements) > 0
    names = [el.get('tags', {}).get('name', 'Unnamed Protected Area') for el in elements if 'tags' in el]

    result = {
        'is_protected': is_protected,
        'protected_area_names': names,
        'source': 'OpenStreetMap'
    }

    cache[cache_key] = result
    save_osm_cache(cache)
    return result

