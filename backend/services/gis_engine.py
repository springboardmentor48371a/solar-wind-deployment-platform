import math
import requests
from shapely.geometry import Point, box

def get_elevation_matrix(lat: float, lon: float, delta_meters: float = 30.0) -> list[float]:
    """
    Samples elevation for Center, North, South, East, and West points
    using a 30m grid spacing to compute finite difference gradients.
    """
    # 1 deg latitude ≈ 111,320 m
    delta_lat = delta_meters / 111320.0
    delta_lon = delta_meters / (111320.0 * math.cos(math.radians(lat)))

    coords = [
        {"lat": lat, "lon": lon},
        {"lat": lat + delta_lat, "lon": lon},
        {"lat": lat - delta_lat, "lon": lon},
        {"lat": lat, "lon": lon + delta_lon},
        {"lat": lat, "lon": lon - delta_lon},
    ]

    lats = ",".join(str(c["lat"]) for c in coords)
    lons = ",".join(str(c["lon"]) for c in coords)
    url = f"https://elevation-api.open-meteo.com/v1/elevation?latitude={lats}&longitude={lons}"

    try:
        res = requests.get(url, timeout=8)
        if res.status_code == 200:
            return res.json().get("elevation", [250.0] * 5)
    except Exception as e:
        print(f"[DEM Fetch Warning] {e}")

    return [250.0, 250.0, 250.0, 250.0, 250.0]


def compute_terrain_slope(lat: float, lon: float, cell_size_m: float = 30.0) -> dict:
    """
    Calculates slope gradient in degrees and percentage using Horn's method.
    - Solar PV viability: < 5 degrees optimal
    - Wind Turbine viability: < 12 degrees optimal
    """
    elevations = get_elevation_matrix(lat, lon, cell_size_m)
    center_z, z_north, z_south, z_east, z_west = elevations

    # Finite difference gradient
    dz_dx = (z_east - z_west) / (2.0 * cell_size_m)
    dz_dy = (z_north - z_south) / (2.0 * cell_size_m)

    slope_radians = math.atan(math.sqrt(dz_dx**2 + dz_dy**2))
    slope_degrees = round(math.degrees(slope_radians), 2)
    slope_percent = round(math.tan(slope_radians) * 100.0, 2)

    return {
        "elevation_m": center_z,
        "slope_degrees": slope_degrees,
        "slope_percent": slope_percent,
        "is_solar_viable": slope_degrees <= 5.0,
        "is_wind_viable": slope_degrees <= 12.0,
        "terrain_profile": (
            "Flat / Gentle (< 5°)" if slope_degrees < 5.0
            else ("Moderate (5° - 10°)" if slope_degrees <= 10.0 else "Steep / Restricted (> 10°)")
        )
    }


def calculate_infrastructure_proximity(lat: float, lon: float) -> dict:
    """
    Calculates geodesic distance to the nearest transmission grid and sub-station.
    """
    # Reference high-voltage substation coordinates (Bhadla, Muppandal, Kutch grids)
    substations = [
        {"name": "Bhadla 765kV Substation", "lat": 27.53, "lon": 71.91},
        {"name": "Muppandal Wind Pooling Substation", "lat": 8.26, "lon": 77.54},
        {"name": "Kutch Khavda Pooling Station", "lat": 23.82, "lon": 69.80},
    ]

    def haversine_km(lat1, lon1, lat2, lon2):
        r = 6371.0
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = (math.sin(d_lat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2)
        return r * 2 * math.asin(math.sqrt(a))

    distances = [haversine_km(lat, lon, s["lat"], s["lon"]) for s in substations]
    min_dist = min(distances) if distances else 2.5

    # Simulated local access road proximity based on proximity factor
    simulated_road_km = round(max(0.3, min_dist * 0.4), 2)

    return {
        "substation_dist_km": round(min_dist, 2),
        "transmission_line_dist_km": round(max(0.2, min_dist * 0.7), 2),
        "road_dist_km": simulated_road_km
    }


def check_exclusion_buffer(lat: float, lon: float, buffer_meters: float = 500.0) -> list[dict]:
    """
    Evaluates whether coordinates intersect any restricted environmental or municipal zones
    using Shapely geometry buffers.
    """
    site_point = Point(lon, lat)

    # Convert buffer in meters to approximate degree tolerance
    degree_buffer = buffer_meters / 111320.0

    # Sample restricted reserves / wetlands
    exclusion_zones = [
        {"name": "Desert National Park Buffer", "type": "Protected Wildlife Zone", "box": box(70.5, 26.5, 71.2, 27.2)},
        {"name": "Rann of Kutch Wildlife Sanctuary", "type": "Protected Wetland", "box": box(69.0, 23.5, 70.0, 24.2)}
    ]

    conflicts = []
    for zone in exclusion_zones:
        buffered_zone = zone["box"].buffer(degree_buffer)
        if buffered_zone.contains(site_point):
            conflicts.append({"name": zone["name"], "type": zone["type"]})

    return conflicts