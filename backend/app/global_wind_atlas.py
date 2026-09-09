import os
import logging
import rasterio
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Paths to the local cropped WGS84 GeoTIFF files
APP_DIR = os.path.dirname(os.path.abspath(__file__))
WIND_SPEED_PATH = os.path.join(APP_DIR, "data", "gujarat_rajasthan_wind_speed_100m.tif")
POWER_DENSITY_PATH = os.path.join(APP_DIR, "data", "gujarat_rajasthan_power_density_100m.tif")

def fetch_gwa_point_data(latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
    """
    Extracts the mean wind speed and wind power density from the cropped GWA rasters
    for the specified latitude and longitude coordinate using Rasterio's affine geotransform indexing.
    
    Returns a dictionary of GWA parameters or None if the coordinate falls outside the bounding box
    or the files are not available.
    """
    # Check if the cropped raster files exist
    if not os.path.exists(WIND_SPEED_PATH) or not os.path.exists(POWER_DENSITY_PATH):
        logger.warning("Cropped GWA rasters not found locally. Fallback will be triggered.")
        return None

    try:
        # 1. Read wind speed at 100m
        with rasterio.open(WIND_SPEED_PATH) as ws_src:
            bounds = ws_src.bounds
            # Check if coordinate lies within the raster geographic box
            if not (bounds.left <= longitude <= bounds.right and bounds.bottom <= latitude <= bounds.top):
                logger.warning(f"Coordinates ({latitude}, {longitude}) are outside the GWA cropped raster bounds.")
                return None
                
            # Perform index lookup using the affine geotransform matrix
            # index expects (x, y) where x is longitude (Easting) and y is latitude (Northing)
            row, col = ws_src.index(longitude, latitude)
            
            # Read pixel value (band 1)
            ws_val = float(ws_src.read(1)[row, col])
            
            # Handle nodata fallback
            if ws_val < 0.0 or ws_val > 100.0:
                logger.warning(f"GWA wind speed lookup returned invalid or nodata value: {ws_val}")
                return None

        # 2. Read wind power density at 100m
        with rasterio.open(POWER_DENSITY_PATH) as pd_src:
            row, col = pd_src.index(longitude, latitude)
            pd_val = float(pd_src.read(1)[row, col])
            
            # Handle nodata fallback
            if pd_val < 0.0 or pd_val > 25000.0:
                logger.warning(f"GWA power density lookup returned invalid or nodata value: {pd_val}")
                return None

        # 3. Classify wind resource category (NREL classes at 50/100m)
        if ws_val < 5.6:
            res_class = "Class 1 (Poor)"
        elif ws_val < 6.4:
            res_class = "Class 2 (Marginal)"
        elif ws_val < 7.0:
            res_class = "Class 3 (Fair)"
        elif ws_val < 7.5:
            res_class = "Class 4 (Good)"
        elif ws_val < 8.0:
            res_class = "Class 5 (Excellent)"
        elif ws_val < 8.8:
            res_class = "Class 6 (Outstanding)"
        else:
            res_class = "Class 7 (Superb)"

        return {
            "wind_speed": round(ws_val, 2),
            "wind_power_density": round(pd_val, 2),
            "wind_resource": f"Derived Wind Resource Class: {res_class}",
            "wind_data_source": "Global Wind Atlas"
        }

    except Exception as e:
        logger.error(f"Error reading GWA GeoTIFFs using rasterio: {e}")
        return None
