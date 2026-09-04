"""
Environmental Data Provider Abstraction (Sections 7, 8, 25).

Defines an abstract provider interface `EnvironmentalDataProvider` and three implementations:
  1. `DatasetEnvironmentalProvider`: Deterministic environmental extraction for validation/demonstration.
  2. `NASAEnvironmentalProvider`: Live API data integration (NASA POWER, Open-Elevation, OSM Overpass).
  3. `HybridEnvironmentalProvider`: Live-first provider with transparent fallback to dataset data.
"""
from abc import ABC, abstractmethod
import math
import hashlib
from typing import Dict, Any, Optional

from . import geo_data_service as geo


def _stable_rand(seed_key: str, low: float, high: float) -> float:
    h = hashlib.sha256(seed_key.encode()).hexdigest()
    frac = int(h[:8], 16) / 0xFFFFFFFF
    return low + frac * (high - low)


class EnvironmentalDataProvider(ABC):
    @abstractmethod
    def get_environmental_data(
        self, latitude: float, longitude: float, site_id: Optional[int] = None, **kwargs
    ) -> Dict[str, Any]:
        """Returns a normalized environmental data dictionary matching the canonical schema."""
        pass


class DatasetEnvironmentalProvider(EnvironmentalDataProvider):
    """Controlled, deterministic dataset-based environmental data provider."""

    def get_environmental_data(
        self, latitude: float, longitude: float, site_id: Optional[int] = None, **kwargs
    ) -> Dict[str, Any]:
        seed = f"{site_id or 0}:{latitude:.4f}:{longitude:.4f}"
        lat_factor = math.cos(math.radians(min(abs(latitude), 65)))

        base_irradiance = 3.2 + lat_factor * 3.8
        irradiance = round(base_irradiance + _stable_rand(seed + "irr", -0.3, 0.3), 2)
        wind_speed = round(_stable_rand(seed + "wind", 3.0, 9.0), 2)
        wind_dir = round(_stable_rand(seed + "wdir", 0, 359), 1)
        temp = round(30.0 - (abs(latitude) * 0.45) + _stable_rand(seed + "temp", -2, 2), 1)
        rainfall = round(_stable_rand(seed + "rain", 250, 1800), 0)
        cloud_cover = round(_stable_rand(seed + "cloud", 12, 65), 1)
        slope = round(_stable_rand(seed + "slope", 1.0, 15.0), 2)
        ndvi = round(_stable_rand(seed + "ndvi", 0.2, 0.75), 2)

        dist_road = round(_stable_rand(seed + "road", 0.5, 20.0), 2)
        dist_trans = round(_stable_rand(seed + "trans", 1.0, 35.0), 2)
        dist_sub = round(_stable_rand(seed + "sub", 1.0, 30.0), 2)
        dist_urban = round(_stable_rand(seed + "urban", 2.0, 50.0), 2)
        dist_water = round(_stable_rand(seed + "water", 0.5, 18.0), 2)
        protected = _stable_rand(seed + "protected", 0, 1) > 0.85

        return {
            "solar_irradiance_kwh_m2_day": irradiance,
            "wind_speed_avg_ms": wind_speed,
            "wind_direction_deg": wind_dir,
            "temperature_avg_c": temp,
            "rainfall_mm_year": rainfall,
            "cloud_cover_pct": cloud_cover,
            "land_slope_pct": slope,
            "vegetation_index_ndvi": ndvi,
            "distance_to_road_km": dist_road,
            "distance_to_transmission_km": dist_trans,
            "distance_to_substation_km": dist_sub,
            "distance_to_urban_km": dist_urban,
            "distance_to_water_km": dist_water,
            "in_protected_zone": protected,
            "data_source": "dataset",
        }


class NASAEnvironmentalProvider(EnvironmentalDataProvider):
    """Live API environmental data provider calling NASA POWER, Open-Elevation, OSM Overpass."""

    def get_environmental_data(
        self, latitude: float, longitude: float, site_id: Optional[int] = None, **kwargs
    ) -> Dict[str, Any]:
        climatology = geo.fetch_nasa_power_climatology(latitude, longitude)
        elevation_info = geo.fetch_elevation_profile(latitude, longitude)
        osm_info = geo.fetch_osm_context(latitude, longitude)

        if not climatology or not elevation_info or not osm_info:
            raise RuntimeError("One or more live environmental APIs were unreachable.")

        landuse_tag = osm_info.get("landuse_tag")
        ndvi = geo.landuse_ndvi_proxy(landuse_tag) if landuse_tag else 0.45

        return {
            "solar_irradiance_kwh_m2_day": climatology["solar_irradiance_kwh_m2_day"],
            "wind_speed_avg_ms": climatology["wind_speed_avg_ms"],
            "wind_direction_deg": 180.0,
            "temperature_avg_c": climatology["temperature_avg_c"],
            "rainfall_mm_year": climatology["rainfall_mm_year"],
            "cloud_cover_pct": climatology["cloud_cover_pct"],
            "land_slope_pct": elevation_info["land_slope_pct"],
            "vegetation_index_ndvi": ndvi,
            "distance_to_road_km": osm_info["distance_to_road_km"],
            "distance_to_transmission_km": osm_info["distance_to_transmission_km"],
            "distance_to_substation_km": osm_info["distance_to_substation_km"],
            "distance_to_urban_km": osm_info["distance_to_urban_km"],
            "distance_to_water_km": osm_info["distance_to_water_km"],
            "in_protected_zone": osm_info["in_protected_zone"],
            "data_source": "live",
        }


class HybridEnvironmentalProvider(EnvironmentalDataProvider):
    """Hybrid provider: attempts live APIs first, falling back gracefully to dataset values."""

    def __init__(self):
        self.live_provider = NASAEnvironmentalProvider()
        self.dataset_provider = DatasetEnvironmentalProvider()

    def get_environmental_data(
        self, latitude: float, longitude: float, site_id: Optional[int] = None, **kwargs
    ) -> Dict[str, Any]:
        try:
            return self.live_provider.get_environmental_data(latitude, longitude, site_id, **kwargs)
        except Exception:
            data = self.dataset_provider.get_environmental_data(latitude, longitude, site_id, **kwargs)
            data["data_source"] = "synthetic_fallback"
            return data
