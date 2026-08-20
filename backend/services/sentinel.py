import requests
import numpy as np
from datetime import datetime, timedelta

SENTINEL_HUB_API = "https://services.sentinel-hub.com/ogc/wms/your-instance-id"

def get_ndvi(lat, lon):
    """Fetch NDVI from Sentinel Hub (requires instance ID)"""
    # This requires Sentinel Hub account – for now we simulate
    return np.random.uniform(0.1, 0.7)  # fallback