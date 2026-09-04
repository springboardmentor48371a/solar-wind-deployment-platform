"""
Physics-informed baseline formulas for solar yield, wind power, and site
suitability scoring.

These are used in two places:
  1. As the deterministic FALLBACK prediction when the trained ML models
     (see predictor.py) aren't available or fail to load.
  2. As the GROUND-TRUTH GENERATOR for the synthetic training set the ML
     models are trained on (see train.py) -- with noise added so the models
     learn a smoothed, generalizable surrogate rather than memorizing the
     closed-form formula exactly.

Keeping the physics in one place means the fallback path and the training
target are always consistent with each other.
"""
AIR_DENSITY = 1.225  # kg/m3 at sea level


def solar_baseline(env: dict, land_area_hectares: float = 5.0) -> dict:
    irradiance = env["solar_irradiance_kwh_m2_day"]
    cloud_cover = env["cloud_cover_pct"]
    slope = env["land_slope_pct"]
    temp = env["temperature_avg_c"]

    peak_sun_hours = round(irradiance, 2)
    annual_irradiance = round(irradiance * 365, 1)

    base_efficiency = 21.0
    temp_derate = max(0, (temp - 25) * 0.04)
    slope_derate = min(slope * 0.05, 3.0)
    panel_efficiency = round(max(base_efficiency - temp_derate - slope_derate, 12.0), 2)

    shading_loss = round(min(cloud_cover * 0.08, 8.0), 2)
    performance_ratio = round(max(0.85 - (cloud_cover / 1000) - (shading_loss / 200), 0.65), 3)

    capacity_factor = round(min((peak_sun_hours / 24) * performance_ratio * 100, 32.0), 2)

    installed_capacity_mw = round(land_area_hectares / 2.0, 3)
    expected_output_mwh = round(
        installed_capacity_mw * 1000 * (capacity_factor / 100) * 8760 / 1000, 1
    )

    return {
        "annual_irradiance_kwh_m2": annual_irradiance,
        "peak_sun_hours": peak_sun_hours,
        "panel_efficiency_pct": panel_efficiency,
        "performance_ratio": performance_ratio,
        "capacity_factor_pct": capacity_factor,
        "expected_energy_output_mwh_year": expected_output_mwh,
        "shading_loss_pct": shading_loss,
    }


def wind_baseline(env: dict, land_area_hectares: float = 5.0) -> dict:
    v = env["wind_speed_avg_ms"]

    power_density = round(0.5 * AIR_DENSITY * (v ** 3), 1)
    turbulence_intensity = round(max(6.0, 20 - v), 2)

    if v < 3:
        suitability = "Unsuitable"
        capacity_factor = round(min(v * 2, 8), 2)
    elif v < 5.5:
        suitability = "Marginal"
        capacity_factor = round(15 + (v - 3) * 5, 2)
    elif v < 7.5:
        suitability = "Suitable"
        capacity_factor = round(28 + (v - 5.5) * 6, 2)
    else:
        suitability = "Highly Suitable"
        capacity_factor = round(min(40 + (v - 7.5) * 4, 55), 2)

    installed_capacity_mw = round((land_area_hectares / 8.0) * 2.5, 3)
    expected_annual_energy = round(
        installed_capacity_mw * 1000 * (capacity_factor / 100) * 8760 / 1000, 1
    )

    return {
        "avg_wind_speed_ms": v,
        "wind_power_density_w_m2": power_density,
        "turbulence_intensity_pct": turbulence_intensity,
        "turbine_suitability": suitability,
        "capacity_factor_pct": capacity_factor,
        "expected_annual_energy_mwh": expected_annual_energy,
    }


WEIGHTS = {
    "resource": 0.35,
    "geographic": 0.25,
    "infrastructure": 0.15,
    "environmental": 0.15,
    "economic": 0.10,
}


def _clamp(v, lo=0, hi=100):
    return max(lo, min(hi, v))


def category_for_score(overall: float) -> str:
    if overall >= 85:
        return "Excellent"
    if overall >= 70:
        return "Highly Suitable"
    if overall >= 50:
        return "Moderately Suitable"
    if overall >= 30:
        return "Low Suitability"
    return "Unsuitable"


def scoring_baseline(env: dict, solar: dict, wind: dict, land_area_hectares: float = 5.0, site_type: str = "hybrid") -> dict:
    resource_score = _clamp(max(solar["capacity_factor_pct"], wind["capacity_factor_pct"]) * 2.6)

    slope_penalty = min(env["land_slope_pct"] * 3, 60)
    geographic_score = _clamp(100 - slope_penalty - (env["vegetation_index_ndvi"] * 20))

    infra_penalty = (
        env["distance_to_road_km"] * 1.0
        + env["distance_to_transmission_km"] * 0.8
        + env["distance_to_substation_km"] * 0.8
    )
    infrastructure_score = _clamp(100 - infra_penalty)

    environmental_score = _clamp(
        100
        - (40 if env["in_protected_zone"] else 0)
        - max(0, 10 - env["distance_to_water_km"]) * 3
    )

    economic_score = _clamp(
        50 + min(land_area_hectares, 50) * 0.6 - (env["cloud_cover_pct"] * 0.2)
    )

    overall = (
        resource_score * WEIGHTS["resource"]
        + geographic_score * WEIGHTS["geographic"]
        + infrastructure_score * WEIGHTS["infrastructure"]
        + environmental_score * WEIGHTS["environmental"]
        + economic_score * WEIGHTS["economic"]
    )
    overall = round(overall, 2)
    category = category_for_score(overall)

    solar_cf = solar["capacity_factor_pct"]
    wind_cf = wind["capacity_factor_pct"]
    site_type_str = str(site_type).lower() if site_type else "hybrid"

    if site_type_str == "solar":
        if wind_cf > solar_cf + 10:
            recommended_technology = "hybrid"
        else:
            recommended_technology = "solar"
    elif site_type_str == "wind":
        if solar_cf > wind_cf + 10:
            recommended_technology = "hybrid"
        else:
            recommended_technology = "wind"
    else:
        if solar_cf > wind_cf + 2:
            recommended_technology = "solar"
        elif wind_cf > solar_cf + 2:
            recommended_technology = "wind"
        else:
            recommended_technology = "hybrid"

    return {
        "resource_score": round(resource_score, 2),
        "geographic_score": round(geographic_score, 2),
        "infrastructure_score": round(infrastructure_score, 2),
        "environmental_score": round(environmental_score, 2),
        "economic_score": round(economic_score, 2),
        "overall_score": overall,
        "category": category,
        "recommended_technology": recommended_technology,
    }
