def predict_suitability(
    solar_score: float | None,
    wind_score: float | None,
    land_cover_score: float | None,
    elevation: float | None,
    energy_type: str,
) -> dict:
    """
    Weighted suitability score based on project spec formula:
        Resource Availability   × 35%
        Geographic Suitability  × 25%
        Infrastructure          × 15%  (placeholder until OSM integration)
        Environmental Impact    × 15%
        Economic Feasibility    × 10%  (placeholder)
    """
    if solar_score is None and wind_score is None:
        return {
            "suitability_score": None, "suitability_category": None,
            "resource_score": None, "geographic_score": None,
            "infrastructure_score": None, "environmental_score": None,
            "economic_score": None,
        }

    # Resource score — based on energy type
    if energy_type == "solar":
        resource_score = solar_score or 0.0
    elif energy_type == "wind":
        resource_score = wind_score or 0.0
    else:  # hybrid
        resource_score = ((solar_score or 0.0) + (wind_score or 0.0)) / 2

    # Geographic score — based on elevation and slope
    if elevation is not None:
        # flat low elevation land is ideal for solar, moderate for wind
        elev_score = max(0, 100 - (elevation / 30))
        geographic_score = min(elev_score, 100.0)
    else:
        geographic_score = 50.0  # neutral if unknown

    # Land cover score feeds into environmental score
    environmental_score = land_cover_score if land_cover_score is not None else 50.0

    # Placeholders until OSM infrastructure data is integrated (Module 4)
    infrastructure_score = 50.0
    economic_score = 50.0

    final_score = round(
        resource_score      * 0.35 +
        geographic_score    * 0.25 +
        infrastructure_score * 0.15 +
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
        "geographic_score": round(geographic_score, 2),
        "infrastructure_score": infrastructure_score,
        "environmental_score": round(environmental_score, 2),
        "economic_score": economic_score,
    }
