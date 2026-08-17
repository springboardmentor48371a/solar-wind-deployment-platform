"""
Site Suitability Intelligence Engine (Module 7) + Site Scoring Engine
(Module 10).

Implements the exact weighted scoring model from the spec:

    Deployment Suitability Score =
        Renewable Resource Availability   35%
        Geographic Suitability            25%
        Infrastructure Accessibility      15%
        Environmental Impact              15%
        Economic Feasibility              10%
"""

WEIGHTS = {
    "resource": 0.35,
    "geographic": 0.25,
    "infrastructure": 0.15,
    "environmental": 0.15,
    "economic": 0.10,
}


def _clamp(v, lo=0, hi=100):
    return max(lo, min(hi, v))


def score_site(env: dict, solar: dict, wind: dict, land_area_hectares: float = 5.0) -> dict:
    # 1. Renewable Resource Availability (35%) — best of solar or wind capacity factor
    resource_score = _clamp(max(solar["capacity_factor_pct"], wind["capacity_factor_pct"]) * 2.6)

    # 2. Geographic Suitability (25%) — flatter land & lower vegetation density score higher
    slope_penalty = min(env["land_slope_pct"] * 3, 60)
    geographic_score = _clamp(100 - slope_penalty - (env["vegetation_index_ndvi"] * 20))

    # 3. Infrastructure Accessibility (15%) — closer to roads/grid is better
    infra_penalty = (
        env["distance_to_road_km"] * 1.0
        + env["distance_to_transmission_km"] * 0.8
        + env["distance_to_substation_km"] * 0.8
    )
    infrastructure_score = _clamp(100 - infra_penalty)

    # 4. Environmental Impact (15%) — protected zones and proximity to water/urban areas penalized
    environmental_score = _clamp(
        100
        - (40 if env["in_protected_zone"] else 0)
        - max(0, 10 - env["distance_to_water_km"]) * 3
    )

    # 5. Economic Feasibility (10%) — larger usable land & lower cloud cover (less variance) favored
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

    if overall >= 85:
        category = "Excellent"
    elif overall >= 70:
        category = "Highly Suitable"
    elif overall >= 50:
        category = "Moderately Suitable"
    elif overall >= 30:
        category = "Low Suitability"
    else:
        category = "Unsuitable"

    if solar["capacity_factor_pct"] > wind["capacity_factor_pct"] + 8:
        recommended_technology = "solar"
    elif wind["capacity_factor_pct"] > solar["capacity_factor_pct"] + 8:
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
