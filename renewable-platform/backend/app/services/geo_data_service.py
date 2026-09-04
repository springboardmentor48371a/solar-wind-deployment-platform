"""
Live Data Access Layer — backs Modules 3 & 4 (Environmental Data Collection
Engine + Geographic Intelligence Engine) with real external datasets instead
of synthetic numbers.

Every function here calls a public, key-free data source and returns plain
dicts/None. Callers (environmental_engine.py, site_intelligence.py) are
responsible for falling back to a deterministic estimate if a call fails —
this module never raises out of its public functions; it logs and returns
None so a single flaky provider can never take the whole prediction pipeline
down.

Data sources used (all free, no API key required):

  - NASA POWER API            -> solar irradiance, temperature, rainfall,
                                  cloud cover, wind speed (climatology,
                                  averaged across the full historical record
                                  NASA POWER has for the point)
  - Open-Elevation API        -> elevation (SRTM-derived) + a 5-point sample
                                  used to derive terrain slope
  - OpenStreetMap Overpass    -> roads, power lines/substations, water,
                                  protected areas, and the land-use parcel
                                  the coordinates fall inside (used to derive
                                  land area + a land-ownership/type label)
  - OpenStreetMap Nominatim   -> reverse geocoding for a human-readable
                                  region name

NOTE: this sandbox has outbound network access disabled, so these calls
cannot be exercised from here. The functions are written against the
providers' real, documented, key-free REST APIs and are exercised by
`app/ml` synthetic tests during development; when this service is deployed
somewhere with internet egress it will work unmodified. See README.md
("Live Data & Offline Fallback") for details.
"""
import logging
import math
from typing import Optional

import requests

logger = logging.getLogger("geo_data_service")

REQUEST_TIMEOUT = 8
OVERPASS_TIMEOUT = 20
USER_AGENT = "SolarWindDeploymentIntelligencePlatform/1.0 (+https://example.com/contact)"

NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/climatology/point"
OPEN_ELEVATION_URL = "https://api.open-elevation.com/api/v1/lookup"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"

# Landuse tags we care about for the "land ownership / land type" label,
# ordered roughly from most to least favorable for renewable deployment.
LANDUSE_LABELS = {
    "farmland": "Agricultural Land (privately/co-operatively farmed)",
    "farmyard": "Agricultural Land (farmstead parcel)",
    "meadow": "Grassland / Meadow (likely private or grazing lease)",
    "grass": "Open Grassland",
    "brownfield": "Brownfield / Previously Developed Land",
    "quarry": "Former Quarry / Extractive Land",
    "forest": "Forested Land (clearance likely required)",
    "industrial": "Industrial Land",
    "residential": "Residential Land (unsuitable for utility-scale siting)",
    "commercial": "Commercial Land (unsuitable for utility-scale siting)",
    "military": "Military Land (restricted access)",
    "reservoir": "Water Body (unsuitable)",
}

# Rough NDVI proxy by landuse when no satellite NDVI provider is configured.
LANDUSE_NDVI_PROXY = {
    "forest": 0.78, "meadow": 0.65, "grass": 0.6, "farmland": 0.45,
    "farmyard": 0.35, "brownfield": 0.15, "quarry": 0.08, "industrial": 0.12,
    "residential": 0.25, "commercial": 0.15, "military": 0.3, "reservoir": 0.05,
}


def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _project_m(lat, lon, origin_lat, origin_lon):
    """Cheap equirectangular projection to meters, accurate enough at the
    <10km scale we operate at for slope/area estimation."""
    m_per_deg_lat = 111_320.0
    m_per_deg_lon = 111_320.0 * math.cos(math.radians(origin_lat))
    return (lon - origin_lon) * m_per_deg_lon, (lat - origin_lat) * m_per_deg_lat


def _polygon_area_hectares(coords, origin_lat, origin_lon) -> float:
    pts = [_project_m(c["lat"], c["lon"], origin_lat, origin_lon) for c in coords]
    area_m2 = 0.0
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        area_m2 += x1 * y2 - x2 * y1
    return abs(area_m2) / 2 / 10_000  # m^2 -> hectares


def _point_in_polygon(px, py, poly) -> bool:
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if ((y1 > py) != (y2 > py)) and (px < (x2 - x1) * (py - y1) / (y2 - y1 + 1e-12) + x1):
            inside = not inside
    return inside


def fetch_elevation_profile(lat: float, lon: float) -> Optional[dict]:
    """Open-Elevation lookup at the site plus 4 points ~300m N/S/E/W, used to
    derive both elevation and terrain slope (Module 4: terrain analysis)."""
    try:
        offset_deg = 300 / 111_320.0  # ~300m in degrees latitude
        points = [
            (lat, lon), (lat + offset_deg, lon), (lat - offset_deg, lon),
            (lat, lon + offset_deg), (lat, lon - offset_deg),
        ]
        locations = "|".join(f"{p[0]:.6f},{p[1]:.6f}" for p in points)
        resp = requests.get(
            OPEN_ELEVATION_URL, params={"locations": locations},
            timeout=REQUEST_TIMEOUT, headers={"User-Agent": USER_AGENT},
        )
        resp.raise_for_status()
        results = resp.json()["results"]
        elevations = [r["elevation"] for r in results]
        center = elevations[0]
        max_diff = max(abs(center - e) for e in elevations[1:])
        slope_pct = round(min((max_diff / 300.0) * 100, 45.0), 2)
        return {"elevation_m": round(float(center), 1), "land_slope_pct": slope_pct}
    except Exception as exc:  # noqa: BLE001 - any network/parse failure -> fallback upstream
        logger.warning("Open-Elevation lookup failed for (%s, %s): %s", lat, lon, exc)
        return None


def fetch_nasa_power_climatology(lat: float, lon: float) -> Optional[dict]:
    """NASA POWER long-term climatology for irradiance/wind/temp/rain/cloud
    (Module 3: weather + climate data integration)."""
    try:
        params = {
            "parameters": "ALLSKY_SFC_SW_DWN,WS50M,T2M,PRECTOTCORR,CLOUD_AMT",
            "community": "RE",
            "longitude": lon,
            "latitude": lat,
            "format": "JSON",
        }
        resp = requests.get(NASA_POWER_URL, params=params, timeout=REQUEST_TIMEOUT,
                             headers={"User-Agent": USER_AGENT})
        resp.raise_for_status()
        data = resp.json()["properties"]["parameter"]

        def annual(param):
            vals = data[param]
            if "ANN" in vals and vals["ANN"] not in (-999, None):
                return vals["ANN"]
            monthly = [v for k, v in vals.items() if k != "ANN" and v not in (-999, None)]
            return sum(monthly) / len(monthly) if monthly else None

        irradiance = annual("ALLSKY_SFC_SW_DWN")
        wind = annual("WS50M")
        temp = annual("T2M")
        rain = annual("PRECTOTCORR")
        cloud = annual("CLOUD_AMT")
        if None in (irradiance, wind, temp, rain, cloud):
            return None

        return {
            "solar_irradiance_kwh_m2_day": round(irradiance, 2),
            "wind_speed_avg_ms": round(wind, 2),
            "temperature_avg_c": round(temp, 1),
            "rainfall_mm_year": round(rain * 365, 0),
            "cloud_cover_pct": round(min(cloud, 100.0), 1),
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("NASA POWER lookup failed for (%s, %s): %s", lat, lon, exc)
        return None


def fetch_osm_context(lat: float, lon: float, radius_m: int = 6000) -> Optional[dict]:
    """Overpass query for infrastructure proximity, protected areas, water,
    and the land-use parcel containing the point (Module 4 geographic
    features + land area / ownership inputs for Module 2 site info)."""
    query = f"""
    [out:json][timeout:{OVERPASS_TIMEOUT}];
    (
      way(around:{radius_m},{lat},{lon})[highway];
      way(around:{radius_m},{lat},{lon})[power~"^(line|minor_line)$"];
      node(around:{radius_m},{lat},{lon})[power=substation];
      way(around:{radius_m},{lat},{lon})[power=substation];
      way(around:{radius_m},{lat},{lon})[landuse];
      way(around:{radius_m},{lat},{lon})[natural=water];
      way(around:{radius_m},{lat},{lon})[waterway];
      way(around:{radius_m},{lat},{lon})[boundary=protected_area];
      way(around:{radius_m},{lat},{lon})[leisure=nature_reserve];
    );
    out geom;
    """
    try:
        resp = requests.post(OVERPASS_URL, data={"data": query},
                              timeout=OVERPASS_TIMEOUT + 5, headers={"User-Agent": USER_AGENT})
        resp.raise_for_status()
        elements = resp.json().get("elements", [])
    except Exception as exc:  # noqa: BLE001
        logger.warning("Overpass lookup failed for (%s, %s): %s", lat, lon, exc)
        return None

    def centroid_km(geometry):
        if not geometry:
            return None
        clat = sum(p["lat"] for p in geometry) / len(geometry)
        clon = sum(p["lon"] for p in geometry) / len(geometry)
        return _haversine_km(lat, lon, clat, clon)

    nearest = {"road": None, "power_line": None, "substation": None, "water": None, "protected": None}
    landuse_ways = []

    for el in elements:
        tags = el.get("tags", {})
        geometry = el.get("geometry")
        if el["type"] == "node" and tags.get("power") == "substation":
            d = _haversine_km(lat, lon, el["lat"], el["lon"])
            nearest["substation"] = d if nearest["substation"] is None else min(nearest["substation"], d)
            continue
        if not geometry:
            continue
        d = centroid_km(geometry)
        if d is None:
            continue
        if "highway" in tags:
            nearest["road"] = d if nearest["road"] is None else min(nearest["road"], d)
        if tags.get("power") in ("line", "minor_line"):
            nearest["power_line"] = d if nearest["power_line"] is None else min(nearest["power_line"], d)
        if tags.get("power") == "substation":
            nearest["substation"] = d if nearest["substation"] is None else min(nearest["substation"], d)
        if tags.get("natural") == "water" or "waterway" in tags:
            nearest["water"] = d if nearest["water"] is None else min(nearest["water"], d)
        if tags.get("boundary") == "protected_area" or tags.get("leisure") == "nature_reserve":
            nearest["protected"] = d if nearest["protected"] is None else min(nearest["protected"], d)
        if "landuse" in tags:
            landuse_ways.append((tags["landuse"], geometry, d))

    # Land parcel: prefer one whose polygon contains the point, else nearest.
    land_area_ha, landuse_tag, urban_distance_km = None, None, None
    containing = None
    for tag, geometry, d in landuse_ways:
        poly = [_project_m(p["lat"], p["lon"], lat, lon) for p in geometry]
        if _point_in_polygon(0.0, 0.0, poly):
            containing = (tag, geometry)
            break
    chosen = containing or (min(landuse_ways, key=lambda t: t[2])[:2] if landuse_ways else None)
    if chosen:
        landuse_tag, geometry = chosen
        try:
            land_area_ha = round(_polygon_area_hectares(geometry, lat, lon), 2)
        except Exception:  # noqa: BLE001
            land_area_ha = None

    # "Urban distance" proxy: nearest residential/commercial landuse polygon.
    urban_candidates = [(tag, d) for tag, _, d in landuse_ways if tag in ("residential", "commercial")]
    if urban_candidates:
        urban_distance_km = round(min(d for _, d in urban_candidates), 2)

    return {
        "distance_to_road_km": round(nearest["road"], 2) if nearest["road"] is not None else None,
        "distance_to_transmission_km": round(nearest["power_line"], 2) if nearest["power_line"] is not None else None,
        "distance_to_substation_km": round(nearest["substation"], 2) if nearest["substation"] is not None else None,
        "distance_to_water_km": round(nearest["water"], 2) if nearest["water"] is not None else None,
        "distance_to_urban_km": urban_distance_km,
        "in_protected_zone": nearest["protected"] is not None and nearest["protected"] < 2.0,
        "land_area_hectares": land_area_ha,
        "landuse_tag": landuse_tag,
    }


def reverse_geocode_region(lat: float, lon: float) -> Optional[str]:
    """Nominatim reverse geocode -> a human-readable region string
    (state/county + country), used for Module 2's 'Region' site field."""
    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={"lat": lat, "lon": lon, "format": "json", "zoom": 8, "addressdetails": 1},
            timeout=REQUEST_TIMEOUT, headers={"User-Agent": USER_AGENT},
        )
        resp.raise_for_status()
        addr = resp.json().get("address", {})
        parts = [
            addr.get("state") or addr.get("region") or addr.get("county"),
            addr.get("country"),
        ]
        parts = [p for p in parts if p]
        return ", ".join(parts) if parts else None
    except Exception as exc:  # noqa: BLE001
        logger.warning("Nominatim reverse geocode failed for (%s, %s): %s", lat, lon, exc)
        return None


def landuse_label(tag: Optional[str]) -> Optional[str]:
    if not tag:
        return None
    return LANDUSE_LABELS.get(tag, f"Land classified as '{tag}' (OpenStreetMap)")


def landuse_ndvi_proxy(tag: Optional[str], default: float = 0.4) -> float:
    if not tag:
        return default
    return LANDUSE_NDVI_PROXY.get(tag, default)
