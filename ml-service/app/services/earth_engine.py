"""
Google Earth Engine feature extraction for land cover prediction.

Initialised once at service startup via init_ee().
extract_features(lat, lon) returns the 8 features the land cover model
was trained on, in the exact order from land_cover_feature_order.json:
  [ndvi, ndbi, elevation, slope_deg, ndvi_seasonal_std,
   ndvi_seasonal_amplitude, ndvi_texture, night_lights_log]

Date-range policy:
  Production uses a rolling 12-month window ending on the day the
  prediction is run (today - 365 days → today). This differs from the
  fixed 2023 window used in training but is the correct production
  behaviour — a site created in 2026 should reflect current land cover,
  not 2023 land cover. The model was trained on globally-sampled data
  and is not sensitive to the specific year of the composite.

Caching:
  Land cover features are cached in the land_cover DB table via the
  ee_features_fetched_at column. extract_features() is only called when
  that column is NULL or older than EE_CACHE_DAYS (default 90 days).
  Land cover changes on a timescale of years, not days — 90 days is
  conservative.
"""

import logging
import os
import math
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

EE_CACHE_DAYS = 90  # re-query Earth Engine at most once per 90 days per site

_ee_ready = False   # set True after successful ee.Initialize()


def init_ee() -> None:
    return  # disabled — model predicts urban for all sites, rule-based fallback is more reliable

    """Initialise Earth Engine with service account credentials.

    Reads two environment variables:
      GEE_SERVICE_ACCOUNT  — service account email
      GEE_KEY_PATH         — absolute path to the JSON key file inside the container
                             (mount the file via Docker volume, never bake it into the image)

    If either variable is missing or initialisation fails, EE is marked
    unavailable and land cover falls back to the rule-based scorer.
    """
    global _ee_ready
    service_account = os.getenv("GEE_SERVICE_ACCOUNT", "")
    key_path = os.getenv("GEE_KEY_PATH", "")

    if not service_account or not key_path:
        logger.warning(
            "GEE_SERVICE_ACCOUNT or GEE_KEY_PATH not set — "
            "Earth Engine unavailable, land cover will use rule-based fallback."
        )
        return

    if not os.path.exists(key_path):
        logger.warning(
            "GEE key file not found at %s — "
            "Earth Engine unavailable, land cover will use rule-based fallback.", key_path
        )
        return

    try:
        import ee
        credentials = ee.ServiceAccountCredentials(service_account, key_path)
        ee.Initialize(credentials, project=os.getenv("GEE_PROJECT", "astral-pipe-508512-s9"))
        _ee_ready = True
        logger.info("Earth Engine initialised with service account %s.", service_account)
    except Exception as exc:
        logger.warning("Earth Engine initialisation failed (%s) — using rule-based fallback.", exc)


def is_ready() -> bool:
    return _ee_ready


def extract_features(lat: float, lon: float) -> dict | None:
    """Extract the 8 land cover features for a single point from Earth Engine.

    Returns a dict with keys:
      ndvi, ndbi, elevation, slope_deg,
      ndvi_seasonal_std, ndvi_seasonal_amplitude, ndvi_texture, night_lights_log

    Returns None if EE is unavailable or the query fails.
    """
    if not _ee_ready:
        return None

    try:
        import ee

        # --- Date window: rolling last 12 months ---
        end_date   = datetime.utcnow().strftime("%Y-%m-%d")
        start_date = (datetime.utcnow() - timedelta(days=365)).strftime("%Y-%m-%d")

        # Quarter boundaries within the window (for seasonal NDVI)
        base = datetime.utcnow() - timedelta(days=365)
        q_starts = [(base + timedelta(days=91 * i)).strftime("%Y-%m-%d") for i in range(4)]
        q_ends   = [(base + timedelta(days=91 * (i + 1))).strftime("%Y-%m-%d") for i in range(4)]

        # --- Cloud masking (Sentinel-2 SCL) ---
        def mask_clouds(image):
            scl = image.select("SCL")
            return image.updateMask(
                scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10))
            )

        # --- DEM + slope (Copernicus GLO-30) ---
        dem_col  = ee.ImageCollection("COPERNICUS/DEM/GLO30_2024_1")
        dem_proj = dem_col.first().select("DEM").projection()
        dem      = dem_col.mosaic().select("DEM").rename("elevation").setDefaultProjection(dem_proj)
        slope    = ee.Terrain.slope(dem).rename("slope_deg")

        # --- Sentinel-2 annual composite ---
        s2 = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
              .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 40))
              .map(mask_clouds))

        annual = s2.filterDate(start_date, end_date).median()
        ndvi_annual = annual.normalizedDifference(["B8", "B4"]).rename("ndvi")
        ndbi        = annual.normalizedDifference(["B11", "B8"]).rename("ndbi")

        # GLCM texture on annual NDVI (contrast band, same as training)
        ndvi_int    = ndvi_annual.multiply(10000).toInt32()
        ndvi_texture = ndvi_int.glcmTexture(size=3).select("ndvi_contrast").rename("ndvi_texture")

        # --- Quarterly NDVI for seasonal stats ---
        q_ndvis = [
            s2.filterDate(q_starts[i], q_ends[i]).median()
              .normalizedDifference(["B8", "B4"]).rename(f"ndvi_q{i+1}")
            for i in range(4)
        ]

        # --- VIIRS night lights ---
        viirs = (ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG")
                 .filterDate(start_date, end_date)
                 .select("avg_rad")
                 .median()
                 .rename("night_lights"))

        # --- Assemble and sample ---
        feature_image = (dem
            .addBands(slope)
            .addBands(ndvi_annual)
            .addBands(ndbi)
            .addBands(q_ndvis[0]).addBands(q_ndvis[1])
            .addBands(q_ndvis[2]).addBands(q_ndvis[3])
            .addBands(ndvi_texture)
            .addBands(viirs))

        point  = ee.Geometry.Point([lon, lat])
        result = feature_image.reduceRegion(
            reducer=ee.Reducer.first(), geometry=point, scale=30
        ).getInfo()

        # --- Compute derived features ---
        q_vals = [result.get(f"ndvi_q{i+1}") for i in range(4)]
        q_vals = [v for v in q_vals if v is not None]

        if len(q_vals) >= 2:
            mean_q = sum(q_vals) / len(q_vals)
            ndvi_seasonal_std       = (sum((v - mean_q) ** 2 for v in q_vals) / len(q_vals)) ** 0.5
            ndvi_seasonal_amplitude = max(q_vals) - min(q_vals)
        else:
            ndvi_seasonal_std       = 0.0
            ndvi_seasonal_amplitude = 0.0

        raw_night_lights = result.get("night_lights") or 0.0
        night_lights_log = math.log1p(raw_night_lights)  # MUST match training transform

        return {
            "ndvi":                    result.get("ndvi")        or 0.0,
            "ndbi":                    result.get("ndbi")        or 0.0,
            "elevation":               result.get("elevation")   or 0.0,
            "slope_deg":               result.get("slope_deg")   or 0.0,
            "ndvi_seasonal_std":       ndvi_seasonal_std,
            "ndvi_seasonal_amplitude": ndvi_seasonal_amplitude,
            "ndvi_texture":            result.get("ndvi_texture") or 0.0,
            "night_lights_log":        night_lights_log,
        }

    except Exception as exc:
        logger.warning("Earth Engine feature extraction failed for (%.4f, %.4f): %s", lat, lon, exc)
        return None
