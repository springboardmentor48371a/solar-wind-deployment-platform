def _geographic_score(elevation: float | None, slope_deg: float | None, aspect_deg: float | None, energy_type: str) -> float:
    """
    Geographic suitability (0-100):
      slope_score     (50%) — flat land is easiest to build on
      elevation_score (30%) — lower elevation = easier access, milder conditions
      aspect_score    (20%) — south-facing benefits solar; neutral for wind
    """
    # Slope: 0° = 100, ≥15° = 0
    if slope_deg is not None:
        slope_score = max(0.0, 100.0 - (slope_deg / 15.0) * 100.0)
    else:
        slope_score = 50.0

    # Elevation: 0m = 100, ≥2000m = 0
    if elevation is not None:
        elevation_score = max(0.0, 100.0 - (elevation / 2000.0) * 100.0)
    else:
        elevation_score = 50.0

    # Aspect: only meaningful for solar; wind and hybrid get neutral 70
    if aspect_deg is not None and energy_type == "solar":
        # South-facing (135°–225°) = 100, north-facing (315°–360° or 0°–45°) = 20, east/west = 60
        if 135 <= aspect_deg <= 225:
            aspect_score = 100.0
        elif aspect_deg <= 45 or aspect_deg >= 315:
            aspect_score = 20.0
        else:
            aspect_score = 60.0
    else:
        aspect_score = 70.0  # neutral for wind/hybrid or unknown

    return round(slope_score * 0.5 + elevation_score * 0.3 + aspect_score * 0.2, 2)


def _economic_score(land_ownership: str | None, elevation: float | None, slope_deg: float | None, resource_score: float) -> float:
    """
    Economic feasibility (0-100) — based on development cost factors known at site creation.

    Land ownership (40pts): determines acquisition cost and permitting ease
    Terrain cost (40pts):   flat low-elevation land = cheap to develop
    Resource ROI (20pts):   strong resource score = strong revenue case
    """
    ownership_pts = {"government": 40, "community": 30, "private": 20, "unknown": 10}.get(land_ownership or "unknown", 10)

    # Terrain cost: penalise steep and high-altitude land (expensive earthworks + logistics)
    slope_penalty = min((slope_deg or 0) / 15.0, 1.0) * 20   # up to 20pt penalty for steep
    elev_penalty  = min((elevation or 0) / 2000.0, 1.0) * 20  # up to 20pt penalty for high altitude
    terrain_pts   = max(0.0, 40.0 - slope_penalty - elev_penalty)

    resource_pts = round((resource_score / 100.0) * 20.0, 2)

    return min(round(ownership_pts + terrain_pts + resource_pts, 2), 100.0)


def predict_suitability(
    solar_score: float | None,
    wind_score: float | None,
    land_cover_score: float | None,
    elevation: float | None,
    energy_type: str,
    infrastructure_score: float | None = None,
    land_ownership: str | None = None,
    slope_deg: float | None = None,
    aspect_deg: float | None = None,
) -> dict:
    """
    Weighted suitability score:
        Resource Availability   × 35%
        Geographic Suitability  × 25%
        Infrastructure          × 15%
        Environmental Impact    × 15%
        Economic Feasibility    × 10%
    """
    if solar_score is None and wind_score is None:
        return {
            "suitability_score": None, "suitability_category": None,
            "resource_score": None, "geographic_score": None,
            "infrastructure_score": None, "environmental_score": None,
            "economic_score": None,
        }

    # Resource score
    if energy_type == "solar":
        resource_score = solar_score or 0.0
    elif energy_type == "wind":
        resource_score = wind_score or 0.0
    else:
        resource_score = ((solar_score or 0.0) + (wind_score or 0.0)) / 2

    geographic_score    = _geographic_score(elevation, slope_deg, aspect_deg, energy_type)
    infra_score         = infrastructure_score if infrastructure_score is not None else 50.0
    environmental_score = land_cover_score if land_cover_score is not None else 50.0
    economic_score      = _economic_score(land_ownership, elevation, slope_deg, resource_score)

    final_score = round(
        resource_score      * 0.35 +
        geographic_score    * 0.25 +
        infra_score         * 0.15 +
        environmental_score * 0.15 +
        economic_score      * 0.10,
        2
    )

    if final_score >= 80:
        category = "Excellent"
    elif final_score >= 65:
        category = "Highly Suitable"
    elif final_score >= 50:
        category = "Moderately Suitable"
    elif final_score >= 35:
        category = "Low Suitability"
    else:
        category = "Unsuitable"

    return {
        "suitability_score": final_score,
        "suitability_category": category,
        "resource_score": round(resource_score, 2),
        "geographic_score": geographic_score,
        "infrastructure_score": round(infra_score, 2),
        "environmental_score": round(environmental_score, 2),
        "economic_score": round(economic_score, 2),
    }
