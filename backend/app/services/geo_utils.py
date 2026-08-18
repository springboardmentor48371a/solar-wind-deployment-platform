"""
GIS & Remote Sensing utilities — Shapely + GeoPandas + PyProj.

Two things live here:
1. `site_point_wkt` — builds the WKT used to populate Site.geom (PostGIS).
2. `nearest_features_km` — replaces hand-rolled haversine math with a
   proper GeoPandas/Shapely/PyProj distance calculation: points are
   projected into an equal-area CRS (via pyproj) before measuring, which
   is the correct way to get real distances in kilometers instead of the
   flat-earth approximation a raw haversine formula gives you.
"""

from typing import Iterable, Optional

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from geoalchemy2.shape import from_shape


def site_point_wkt(latitude: float, longitude: float):
    """Returns a GeoAlchemy2 WKBElement for Site.geom (SRID 4326)."""
    return from_shape(Point(longitude, latitude), srid=4326)


def nearest_features_km(
    site_lat: float,
    site_lon: float,
    features: Iterable[dict],
) -> pd.DataFrame:
    """
    features: iterable of {"feature_type": str, "name": str|None,
                            "lat": float, "lon": float}

    Returns a DataFrame with an added `distance_km` column, computed by
    reprojecting both the site and every feature into World Mollweide
    (an equal-area projection, EPSG:54009) before measuring — accurate
    at any latitude, unlike a flat lat/long delta.
    """
    rows = list(features)
    if not rows:
        return pd.DataFrame(columns=["feature_type", "name", "lat", "lon", "distance_km"])

    site_gdf = gpd.GeoDataFrame(
        {"id": [0]}, geometry=[Point(site_lon, site_lat)], crs="EPSG:4326"
    ).to_crs("ESRI:54009")
    site_point = site_gdf.geometry.iloc[0]

    feat_gdf = gpd.GeoDataFrame(
        rows,
        geometry=[Point(r["lon"], r["lat"]) for r in rows],
        crs="EPSG:4326",
    ).to_crs("ESRI:54009")

    feat_gdf["distance_km"] = feat_gdf.geometry.apply(lambda g: site_point.distance(g) / 1000.0)
    return feat_gdf.drop(columns="geometry")


def read_local_dem_elevation(tif_path: str, latitude: float, longitude: float) -> Optional[float]:
    """
    Reads elevation directly from a local GeoTIFF DEM tile using Rasterio
    (GDAL under the hood) — for deployments that have downloaded real SRTM
    tiles instead of relying on the Open-Elevation HTTP API. Returns None
    if the point falls outside the tile or the file isn't present; callers
    should fall back to services/terrain.py's API-based lookup in that case.
    """
    import rasterio  # imported lazily: GDAL is a heavy system dependency,
    # and most deployments will use the Open-Elevation API path instead.

    try:
        with rasterio.open(tif_path) as dataset:
            row, col = dataset.index(longitude, latitude)
            if row < 0 or col < 0 or row >= dataset.height or col >= dataset.width:
                return None
            band = dataset.read(1)
            value = band[row, col]
            nodata = dataset.nodata
            if nodata is not None and value == nodata:
                return None
            return float(value)
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: local DEM read failed for {tif_path}: {exc}")
        return None
