"""Single source of truth for ML feature ordering. train.py builds the
training matrices in this order; predictor.py builds inference vectors in
this order. Never reorder these lists without retraining."""

SOLAR_FEATURES = [
    "solar_irradiance_kwh_m2_day",
    "cloud_cover_pct",
    "land_slope_pct",
    "temperature_avg_c",
    "land_area_hectares",
]
SOLAR_TARGETS = [
    "annual_irradiance_kwh_m2",
    "peak_sun_hours",
    "panel_efficiency_pct",
    "performance_ratio",
    "capacity_factor_pct",
    "expected_energy_output_mwh_year",
    "shading_loss_pct",
]

WIND_FEATURES = [
    "wind_speed_avg_ms",
    "land_slope_pct",
    "elevation_m",
    "land_area_hectares",
]
WIND_TARGETS = [
    "wind_power_density_w_m2",
    "turbulence_intensity_pct",
    "capacity_factor_pct",
    "expected_annual_energy_mwh",
]

SUITABILITY_FEATURES = [
    "solar_irradiance_kwh_m2_day",
    "wind_speed_avg_ms",
    "land_slope_pct",
    "vegetation_index_ndvi",
    "distance_to_road_km",
    "distance_to_transmission_km",
    "distance_to_substation_km",
    "distance_to_water_km",
    "cloud_cover_pct",
    "land_area_hectares",
    "in_protected_zone",
    "solar_capacity_factor_pct",
    "wind_capacity_factor_pct",
]
SUITABILITY_SCORE_TARGETS = [
    "resource_score",
    "geographic_score",
    "infrastructure_score",
    "environmental_score",
    "economic_score",
    "overall_score",
]
SUITABILITY_CLASS_TARGET = "category"

TECHNOLOGY_CLASSES = ["solar", "wind", "hybrid"]
CATEGORY_CLASSES = ["Unsuitable", "Low Suitability", "Moderately Suitable", "Highly Suitable", "Excellent"]
