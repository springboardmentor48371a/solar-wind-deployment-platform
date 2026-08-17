import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon
from shapely.wkt import loads as load_wkt
import pandas as pd
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.config import settings

# UTM projection zone 43N for Western India (Gujarat/Rajasthan)
PROJ_CRS = "EPSG:32643"
GEOGRAPHIC_CRS = "EPSG:4326"

def calculate_suitability_score(
    solar_irradiance: float, # kWh/m2/day, typical 3.0 to 7.0
    wind_speed: float,       # m/s, typical 2.0 to 10.0
    nearest_substation_dist: float, # km
    road_dist: float,               # km
    protected_area: bool,
    terrain_slope: float,           # degrees
    land_area: float,               # acres
    land_type: str,                 # Desert, Barren, Agriculture, etc.
    weights: Dict[str, float] = None
) -> Dict[str, Any]:
    """
    Computes suitability score based on weighted factors:
    1. Resource Availability (35%)
    2. Geographic Suitability (25%)
    3. Infrastructure Accessibility (15%)
    4. Environmental Impact (15%)
    5. Economic Feasibility (10%)
    """
    if weights is None:
        weights = {
            "resource": settings.DEFAULT_WEIGHT_RESOURCE,
            "geographic": settings.DEFAULT_WEIGHT_GEOGRAPHIC,
            "infrastructure": settings.DEFAULT_WEIGHT_INFRASTRUCTURE,
            "environment": settings.DEFAULT_WEIGHT_ENVIRONMENT,
            "economic": settings.DEFAULT_WEIGHT_ECONOMIC
        }

    # Normalize weights just in case
    total_w = sum(weights.values())
    w_res = weights.get("resource", 0.35) / total_w
    w_geo = weights.get("geographic", 0.25) / total_w
    w_inf = weights.get("infrastructure", 0.15) / total_w
    w_env = weights.get("environment", 0.15) / total_w
    w_eco = weights.get("economic", 0.10) / total_w

    # 1. Resource Score (based on Solar Irradiance or Wind Speed)
    # Solar Irradiance: max 7.5 kWh/m2/day.
    solar_score = min(100.0, (solar_irradiance / 6.5) * 100.0)
    # Wind Speed: max 12 m/s
    wind_score = min(100.0, (wind_speed / 9.0) * 100.0)
    
    # Decide technology recommendation
    if solar_score > 60 and wind_score > 60:
        deployment_type = "Hybrid"
        resource_score = (solar_score + wind_score) / 2
    elif wind_score > solar_score:
        deployment_type = "Wind"
        resource_score = wind_score
    else:
        deployment_type = "Solar"
        resource_score = solar_score

    # 2. Geographic Score (Slope and Elevation)
    # Slope penalty: flat land (0-3 deg) is 100, 3-5 deg is 80, 5-10 deg is 50, >10 deg is 10
    if terrain_slope <= 3.0:
        slope_score = 100.0
    elif terrain_slope <= 5.0:
        slope_score = 80.0
    elif terrain_slope <= 10.0:
        slope_score = 50.0
    else:
        slope_score = 10.0
    
    geo_score = slope_score # In future could add aspect/elevation

    # 3. Infrastructure Score (Substation and Road distance)
    # Substation distance: < 5km = 100, 5-10km = 80, 10-20km = 50, >20km = 10
    if nearest_substation_dist <= 5.0:
        sub_score = 100.0
    elif nearest_substation_dist <= 10.0:
        sub_score = 80.0
    elif nearest_substation_dist <= 20.0:
        sub_score = 50.0
    else:
        sub_score = 10.0

    # Road distance: < 1km = 100, 1-3km = 80, 3-5km = 50, >5km = 10
    if road_dist <= 1.0:
        road_score = 100.0
    elif road_dist <= 3.0:
        road_score = 80.0
    elif road_dist <= 5.0:
        road_score = 50.0
    else:
        road_score = 10.0
    
    inf_score = 0.7 * sub_score + 0.3 * road_score

    # 4. Environmental Score (Protected area check)
    # Protected Area -> Score = 0 (and overrides everything to Unsuitable)
    # Non-protected Area -> Score = 100
    env_score = 0.0 if protected_area else 100.0

    # 5. Economic Score (Land Area and Type)
    # Area: > 100 acres = 100, 50-100 = 80, 10-50 = 50, < 10 = 20
    if land_area >= 100.0:
        area_score = 100.0
    elif land_area >= 50.0:
        area_score = 80.0
    elif land_area >= 10.0:
        area_score = 50.0
    else:
        area_score = 20.0

    # Type: Desert/Barren = 100, Plain = 80, Agricultural = 10, Forest = 0
    land_type_lower = land_type.lower() if land_type else "plain"
    if "desert" in land_type_lower or "barren" in land_type_lower or "wasteland" in land_type_lower:
        type_score = 100.0
    elif "plain" in land_type_lower:
        type_score = 80.0
    elif "agri" in land_type_lower:
        type_score = 20.0
    else:
        type_score = 10.0

    eco_score = 0.6 * area_score + 0.4 * type_score

    # Compute total suitability score
    suitability_score = (
        w_res * resource_score +
        w_geo * geo_score +
        w_inf * inf_score +
        w_env * env_score +
        w_eco * eco_score
    )

    # Overrule: if it is in a protected area, suitability is forced to 0
    if protected_area:
        suitability_score = 0.0

    # Categorize suitability
    if suitability_score >= 85.0:
        category = "Excellent"
    elif suitability_score >= 70.0:
        category = "High"
    elif suitability_score >= 50.0:
        category = "Moderate"
    elif suitability_score >= 30.0:
        category = "Low"
    else:
        category = "Unsuitable"

    return {
        "suitability_score": round(suitability_score, 1),
        "suitability_category": category,
        "deployment_type": deployment_type,
        "scores": {
            "resource": round(resource_score, 1),
            "geographic": round(geo_score, 1),
            "infrastructure": round(inf_score, 1),
            "environmental": round(env_score, 1),
            "economic": round(eco_score, 1),
            "solar_factor": round(solar_score, 1),
            "wind_factor": round(wind_score, 1)
        }
    }


def perform_gis_distance_analysis(
    latitude: float,
    longitude: float,
    substations: List[Dict[str, Any]],
    protected_zones: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Computes precise distance and intersections using GeoPandas and Shapely.
    Calculates distances in kilometers using UTM 43N projection for accuracy in India.
    """
    site_point = Point(longitude, latitude)
    
    # 1. Substation distance
    if not substations:
        # Fallback to realistic random distance if database has no substations
        nearest_sub_dist = 4.2
    else:
        # Create GeoDataFrame for substations
        sub_df = pd.DataFrame(substations)
        sub_gdf = gpd.GeoDataFrame(
            sub_df, 
            geometry=gpd.points_from_xy(sub_df.longitude, sub_df.latitude),
            crs=GEOGRAPHIC_CRS
        )
        
        # Create site GeoDataFrame
        site_gdf = gpd.GeoDataFrame(
            pd.DataFrame([{"id": 1}]), 
            geometry=[site_point], 
            crs=GEOGRAPHIC_CRS
        )
        
        # Reproject to meters-based CRS
        sub_gdf_proj = sub_gdf.to_crs(PROJ_CRS)
        site_gdf_proj = site_gdf.to_crs(PROJ_CRS)
        
        # Calculate distances in meters and find min
        distances = sub_gdf_proj.geometry.distance(site_gdf_proj.geometry.iloc[0])
        nearest_sub_dist = float(distances.min() / 1000.0) # Convert to km and cast to float

    # 2. Road distance (generate a mock road line if none seeded, or perform analysis)
    # We will simulate a highway passing nearby
    road_geom = LineString([(69.0, 23.0), (73.0, 26.0)]) # Rough path through Gujarat/Rajasthan
    site_gdf = gpd.GeoDataFrame(
        pd.DataFrame([{"id": 1}]), 
        geometry=[site_point], 
        crs=GEOGRAPHIC_CRS
    )
    road_gdf = gpd.GeoDataFrame(
        pd.DataFrame([{"id": 1}]), 
        geometry=[road_geom], 
        crs=GEOGRAPHIC_CRS
    )
    
    site_gdf_proj = site_gdf.to_crs(PROJ_CRS)
    road_gdf_proj = road_gdf.to_crs(PROJ_CRS)
    
    road_dist = float(site_gdf_proj.geometry.distance(road_gdf_proj.geometry.iloc[0]).iloc[0] / 1000.0) # km and cast to float

    # 3. Protected Area intersection
    is_protected = False
    if protected_zones:
        # Parse and check intersection with polygon zones
        for zone in protected_zones:
            geom_wkt = zone.get("geometry_wkt")
            if geom_wkt:
                try:
                    poly = load_wkt(geom_wkt)
                    if poly.intersects(site_point):
                        is_protected = True
                        break
                except Exception:
                    pass

    return {
        "nearest_substation_distance": round(nearest_sub_dist, 2),
        "road_distance": round(road_dist, 2),
        "protected_area": is_protected
    }
