"""
Tests the rule-based Site Suitability Scoring Engine (app/services/scoring.py)
— the weighted formula from the project spec (35/25/15/15/10) — both as a
pure unit (constructing models.Site/WeatherReading/InfrastructureFeature
objects directly, no HTTP) and end-to-end through the API using the
deterministic connector stubs from conftest.py.
"""

import datetime

from app import models
from app.services.scoring import compute_site_suitability, _category_for_score
from tests.conftest import auth_headers


def test_category_thresholds():
    assert _category_for_score(90) == "Excellent"
    assert _category_for_score(85) == "Excellent"
    assert _category_for_score(84.9) == "Highly Suitable"
    assert _category_for_score(70) == "Highly Suitable"
    assert _category_for_score(55) == "Moderately Suitable"
    assert _category_for_score(35) == "Low Suitability"
    assert _category_for_score(0) == "Unsuitable"


def test_scoring_weights_sum_to_overall(client, planner):
    """The overall score must equal the documented weighted sum exactly —
    this is the number the PDF's spec is graded against, so a drift here
    is a real regression, not a rounding nitpick."""
    project_resp = client.post(
        "/projects/", headers=auth_headers(planner), json={"name": "Scoring Test"}
    )
    project_id = project_resp.json()["id"]

    site_resp = client.post(
        f"/projects/{project_id}/sites/",
        headers=auth_headers(planner),
        json={"name": "Scoring Site", "latitude": 17.72, "longitude": 83.30},
    )
    site_id = site_resp.json()["id"]

    score_resp = client.get(
        f"/projects/{project_id}/sites/{site_id}/suitability", headers=auth_headers(planner)
    )
    assert score_resp.status_code == 200, score_resp.text
    score = score_resp.json()

    expected_overall = round(
        score["resource_score"] * 0.35
        + score["geographic_score"] * 0.25
        + score["infrastructure_score"] * 0.15
        + score["environmental_score"] * 0.15
        + score["economic_score"] * 0.10,
        1,
    )
    assert score["overall_score"] == expected_overall
    assert score["category"] == _category_for_score(expected_overall)


def test_excellent_site_scores_high(db_session_factory):
    """A site with ideal readings on every dimension should land in the
    top category — a pure unit test against the scoring function, with
    no HTTP/API layer involved."""
    db = db_session_factory()
    site = models.Site(project_id=1, name="Ideal Site", latitude=17.7, longitude=83.3, land_slope_pct=1.0)
    db.add(site)
    db.commit()
    db.refresh(site)

    db.add(
        models.WeatherReading(
            site_id=site.id,
            reading_date=datetime.datetime.utcnow(),
            solar_irradiance=6.8,
            wind_speed_50m=8.0,
            cloud_cover_pct=5.0,
        )
    )
    db.add(models.InfrastructureFeature(site_id=site.id, feature_type="substation", distance_km=0.5))
    db.commit()
    db.refresh(site)

    score = compute_site_suitability(db, site)
    assert score.overall_score >= 85
    assert score.category == "Excellent"


def test_poor_site_scores_low(db_session_factory):
    db = db_session_factory()
    site = models.Site(
        project_id=1, name="Poor Site", latitude=10.0, longitude=10.0, land_slope_pct=45.0, elevation_m=3200
    )
    db.add(site)
    db.commit()
    db.refresh(site)

    db.add(
        models.WeatherReading(
            site_id=site.id,
            reading_date=datetime.datetime.utcnow(),
            solar_irradiance=1.0,
            wind_speed_50m=1.0,
            cloud_cover_pct=95.0,
        )
    )
    db.commit()
    db.refresh(site)

    score = compute_site_suitability(db, site)
    assert score.overall_score < 40
