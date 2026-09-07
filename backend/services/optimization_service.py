import math

def calculate_hybrid_colocation(land_area_km2: float, site_type: str = "Hybrid (Solar + Wind)") -> dict:
    """
    Module 9: Hybrid Co-Location & Capacity Footprint Optimization.
    IEC Standard: 2.5 MW Turbine (120m rotor diameter).
    Recommended inter-turbine spacing: 5D crosswind x 7D downwind to minimize wake deficit.
    """
    area_km2 = max(0.5, float(land_area_km2))
    st = site_type.lower()

    rotor_diam_m = 120.0
    spacing_crosswind = 5 * rotor_diam_m  # 600m
    spacing_downwind = 7 * rotor_diam_m   # 840m
    turbine_footprint_km2 = (spacing_crosswind * spacing_downwind) / 1e6  # ~0.504 km² per turbine

    if "wind" in st and "solar" not in st:
        max_turbines = math.floor(area_km2 / turbine_footprint_km2)
        wind_capacity_mw = max_turbines * 2.5
        solar_capacity_mw = 0.0
    elif "solar" in st and "wind" not in st:
        max_turbines = 0
        wind_capacity_mw = 0.0
        # Utility Solar PV benchmark: ~4.0 acres per MW = ~50 MW per km²
        solar_capacity_mw = round(area_km2 * 45.0, 1)
    else:
        # Hybrid Co-location: Turbines elevated at 100m, PV panels on the ground between rows
        max_turbines = math.floor((area_km2 * 0.85) / turbine_footprint_km2)
        wind_capacity_mw = max_turbines * 2.5
        # 60% of ground area between turbine rows utilized for ground-mounted bifacial PV
        solar_capacity_mw = round((area_km2 * 0.60) * 45.0, 1)

    total_capacity_mw = wind_capacity_mw + solar_capacity_mw

    return {
        "land_area_km2": area_km2,
        "site_type": site_type,
        "optimal_turbines_count": max_turbines,
        "wind_capacity_mw": wind_capacity_mw,
        "solar_capacity_mw": solar_capacity_mw,
        "total_nameplate_capacity_mw": total_capacity_mw,
        "wake_loss_factor_pct": 4.5 if max_turbines > 1 else 0.0,
        "spacing_spec": "5D x 7D (600m x 840m) Wake Buffer"
    }

def calculate_multicriteria_scoring(
    solar_ghi: float,
    wind_speed_100m: float,
    slope_degrees: float,
    substation_dist_km: float,
    is_exclusion_zone: bool = False,
    tariff_inr_kwh: float = 3.20
) -> dict:
    """
    Module 10: 5-Factor Weighted Multi-Criteria Suitability Scoring (0 - 100).
    Formula:
      Score = (Resource * 35%) + (Geographic * 25%) + (Infrastructure * 15%) + (Environmental * 15%) + (Economic * 10%)
    """
    if is_exclusion_zone:
        return {
            "overall_score": 0,
            "tier": "Unsuitable (Exclusion Conflict)",
            "breakdown": {"resource": 0, "geographic": 0, "infrastructure": 0, "environmental": 0, "economic": 0}
        }

    # 1. Resource Subscore (35%): GHI (optimal >= 6.0 kWh/m2) and Wind (optimal >= 8.5 m/s)
    ghi_score = min(solar_ghi / 6.0, 1.0) * 100.0
    wind_score = min(wind_speed_100m / 8.5, 1.0) * 100.0
    resource_subscore = round((ghi_score * 0.5) + (wind_score * 0.5), 1)

    # 2. Geographic / Slope Subscore (25%): Optimal < 3°, acceptable < 10°
    if slope_degrees <= 3.0:
        geo_subscore = 100.0
    elif slope_degrees <= 6.0:
        geo_subscore = 85.0
    elif slope_degrees <= 10.0:
        geo_subscore = 60.0
    else:
        geo_subscore = max(20.0, 100.0 - (slope_degrees * 7.5))

    # 3. Infrastructure / Grid Proximity Subscore (15%): Optimal < 2 km, decaying to 25 km
    if substation_dist_km <= 2.0:
        infra_subscore = 100.0
    elif substation_dist_km <= 5.0:
        infra_subscore = 85.0
    elif substation_dist_km <= 15.0:
        infra_subscore = 65.0
    else:
        infra_subscore = max(20.0, 100.0 - (substation_dist_km * 3.5))

    # 4. Environmental Subscore (15%): Default high for scrub/wasteland, adjusted for low slope erosion
    env_subscore = 92.0 if slope_degrees <= 5.0 else 75.0

    # 5. Economic Subscore (10%): High capacity yield and favorable grid access
    economic_subscore = round((resource_subscore * 0.6) + (infra_subscore * 0.4), 1)

    # Compute Total Weighted Index
    overall_score = round(
        (resource_subscore * 0.35) +
        (geo_subscore * 0.25) +
        (infra_subscore * 0.15) +
        (env_subscore * 0.15) +
        (economic_subscore * 0.10),
        1
    )
    overall_score = max(10.0, min(overall_score, 99.0))

    # Determine Suitability Tier
    if overall_score >= 90.0:
        tier = "Excellent"
    elif overall_score >= 75.0:
        tier = "Highly Suitable"
    elif overall_score >= 60.0:
        tier = "Moderately Suitable"
    elif overall_score >= 40.0:
        tier = "Low Suitability"
    else:
        tier = "Unsuitable"

    return {
        "overall_suitability_score": int(round(overall_score)),
        "suitability_tier": tier,
        "breakdown": {
            "resource_subscore_35pct": round(resource_subscore, 1),
            "geographic_slope_subscore_25pct": round(geo_subscore, 1),
            "infrastructure_grid_subscore_15pct": round(infra_subscore, 1),
            "environmental_subscore_15pct": round(env_subscore, 1),
            "economic_subscore_10pct": round(economic_subscore, 1)
        }
    }