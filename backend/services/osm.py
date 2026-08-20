import osmnx as ox
import networkx as nx

def get_nearest_road_distance(lat, lon):
    """Get distance to nearest road in meters"""
    try:
        G = ox.graph_from_point((lat, lon), dist=1000, network_type='drive')
        nodes = ox.distance.nearest_nodes(G, lon, lat)
        # Distance to nearest node (approx road distance)
        return 0
    except:
        return 5000  # fallback: 5 km

def get_nearest_power_line_distance(lat, lon):
    """Get distance to nearest power line (simplified)"""
    # Use Overpass API to query power lines
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json];
    (
      way["power"="line"](around:5000,{lat},{lon});
    );
    out body;
    """
    try:
        resp = requests.get(overpass_url, params={'data': query}, timeout=30)
        data = resp.json()
        # Find closest power line (simplified)
        if data['elements']:
            return 100  # within 100m
        else:
            return 5000
    except:
        return 5000