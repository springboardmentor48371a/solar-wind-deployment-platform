import pytest
from app.services.suitability_engine import suitability_engine
from app.core.config import settings


def test_suitability_scoring_formula():
    """Verify that multi-factor suitability scoring uses exact weights:

    35% Resource, 25% Geographic, 15% Infrastructure, 15% Environmental, 10% Economic
    """
    env_data = {
        "ghi_kwh_m2_day": 6.0,
        "wind_speed_100m": 8.5,
        "protected_zone_distance_km": 15.0,
        "water_body_distance_km": 5.0
    }
    site_data = {
        "slope_deg": 1.5,
        "elevation_m": 400.0,
        "distance_to_grid_km": 2.0,
        "distance_to_road_km": 1.0,
        "distance_to_substation_km": 3.0,
        "land_ownership": "Public Leased"
    }

    res = suitability_engine.calculate_scores(env_data, site_data)

    assert "overall_score" in res
    assert "category" in res
    assert 0.0 <= res["overall_score"] <= 100.0

    # Verify individual score bounds
    assert 0.0 <= res["resource_score"] <= 100.0
    assert 0.0 <= res["geographic_score"] <= 100.0
    assert 0.0 <= res["infrastructure_score"] <= 100.0
    assert 0.0 <= res["environmental_score"] <= 100.0
    assert 0.0 <= res["economic_score"] <= 100.0

    # Verify manual weighted sum calculation matches
    expected_sum = (
        (res["resource_score"] * 0.35) +
        (res["geographic_score"] * 0.25) +
        (res["infrastructure_score"] * 0.15) +
        (res["environmental_score"] * 0.15) +
        (res["economic_score"] * 0.10)
    )
    assert abs(res["overall_score"] - round(expected_sum, 1)) <= 0.2


def test_suitability_categories():
    """Verify threshold category mappings:

    90-100 = Excellent, 75-89 = Highly Suitable, 60-74 = Moderately Suitable, 40-59 = Low Suitability, 0-39 = Unsuitable
    """
    # Unsuitable site (very steep slope, within protected reserve)
    unsuitable_env = {
        "ghi_kwh_m2_day": 2.5,
        "wind_speed_100m": 3.0,
        "protected_zone_distance_km": 0.2,
        "water_body_distance_km": 0.1
    }
    unsuitable_site = {
        "slope_deg": 22.0,
        "elevation_m": 2600.0,
        "distance_to_grid_km": 35.0,
        "distance_to_road_km": 20.0,
        "distance_to_substation_km": 40.0,
        "land_ownership": "Private Restricted"
    }
    res = suitability_engine.calculate_scores(unsuitable_env, unsuitable_site)
    assert res["overall_score"] < 40.0
    assert res["category"] == "Unsuitable"
