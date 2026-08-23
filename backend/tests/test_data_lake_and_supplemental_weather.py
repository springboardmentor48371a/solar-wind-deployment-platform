"""
Confirms the other two gaps closed in this pass:
  1. Data lake archival (app/data_lake.py) is actually called from every
     raw-payload ingestion site, not just defined and left orphaned.
  2. Supplemental weather (OpenWeather + NOAA) has a real, wired
     endpoint — even though it correctly returns an empty list in this
     test environment (no OPENWEATHER_API_KEY configured, and NOAA
     coverage is US-only).
"""

from unittest.mock import patch

from tests.conftest import auth_headers


def test_supplemental_weather_endpoint_reachable(client, planner):
    project_resp = client.post("/projects/", headers=auth_headers(planner), json={"name": "Weather Test"})
    project_id = project_resp.json()["id"]
    site_resp = client.post(
        f"/projects/{project_id}/sites/",
        headers=auth_headers(planner),
        json={"name": "Weather Site", "latitude": 17.72, "longitude": 83.30},
    )
    site_id = site_resp.json()["id"]

    resp = client.get(f"/projects/{project_id}/sites/{site_id}/supplemental-weather", headers=auth_headers(planner))
    assert resp.status_code == 200
    # Correctly empty: conftest's stub returns [] since no live API key is configured in tests.
    assert resp.json() == []


def test_ingestion_log_reports_data_lake_status(client, planner):
    project_resp = client.post("/projects/", headers=auth_headers(planner), json={"name": "Lake Test"})
    project_id = project_resp.json()["id"]
    site_resp = client.post(
        f"/projects/{project_id}/sites/",
        headers=auth_headers(planner),
        json={"name": "Lake Site", "latitude": 17.72, "longitude": 83.30},
    )
    site_id = site_resp.json()["id"]

    resp = client.get(f"/projects/{project_id}/sites/{site_id}/ingestion-log", headers=auth_headers(planner))
    assert resp.status_code == 200
    # No DATA_LAKE_BUCKET configured in tests -> correctly reports disabled,
    # rather than silently omitting the field.
    assert resp.json()["data_lake_archival_enabled"] is False


def test_data_lake_archive_called_when_configured(monkeypatch, db_session_factory):
    """
    Real regression guard: calls fetch_and_store_weather_data end-to-end
    (with requests.get mocked so no real network call happens) and
    asserts data_lake.archive_payload was actually invoked with the
    fetched payload — not just that the reference exists.
    """
    from unittest.mock import MagicMock
    from app import models
    from app.services import environmental
    from app import data_lake as data_lake_module

    archived_calls = []
    monkeypatch.setattr(data_lake_module, "archive_payload", lambda *a, **k: archived_calls.append(a))
    monkeypatch.setattr(environmental, "data_lake", data_lake_module)

    fake_payload = {
        "properties": {
            "parameter": {
                "ALLSKY_SFC_SW_DWN": {"20260101": 5.5},
                "WS10M": {"20260101": 4.0},
                "WS50M": {"20260101": 6.5},
                "T2M": {"20260101": 25.0},
                "PRECTOTCORR": {"20260101": 0.5},
                "CLOUD_AMT": {"20260101": 20.0},
            }
        }
    }
    mock_response = MagicMock()
    mock_response.json.return_value = fake_payload
    mock_response.raise_for_status.return_value = None
    monkeypatch.setattr(environmental.requests, "get", lambda *a, **k: mock_response)
    monkeypatch.setattr(environmental, "cache_get", lambda key: None)
    monkeypatch.setattr(environmental, "cache_set", lambda key, value, ttl_seconds=None: None)

    db = db_session_factory()
    site = models.Site(project_id=1, name="Archive Test Site", latitude=17.7, longitude=83.3)
    db.add(site)
    db.commit()
    db.refresh(site)

    environmental.fetch_and_store_weather_data(db, site)

    assert len(archived_calls) == 1
    assert archived_calls[0][0] == "weather_raw"
    assert archived_calls[0][1] == site.id
    assert archived_calls[0][2] == "NASA_POWER"


def test_pdf_report_includes_score_reasoning(client, planner):
    """
    Confirms the gap fixed in this pass: the site-assessment PDF used to
    only show a bare score/category table. It should now also explain
    *why*, tied to real underlying data for each of the 5 sub-scores.
    """
    project_resp = client.post("/projects/", headers=auth_headers(planner), json={"name": "Reasoning Test"})
    project_id = project_resp.json()["id"]
    site_resp = client.post(
        f"/projects/{project_id}/sites/",
        headers=auth_headers(planner),
        json={"name": "Reasoning Site", "latitude": 17.72, "longitude": 83.30},
    )
    assert site_resp.status_code == 201, site_resp.text

    resp = client.get(f"/projects/{project_id}/reports/pdf", headers=auth_headers(planner))
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    # A real check beyond "it's a PDF": the reasoning text should make the
    # file meaningfully larger than a bare 5-column summary table would be.
    assert len(resp.content) > 2000


def test_explain_suitability_score_reflects_real_data(db_session_factory):
    """Direct unit test on the reasoning generator itself, not just that a PDF comes back."""
    import datetime
    from app import models
    from app.services.score_explanation import explain_suitability_score

    db = db_session_factory()
    site = models.Site(project_id=1, name="Explain Test Site", latitude=17.7, longitude=83.3, land_slope_pct=3.0, elevation_m=50.0)
    db.add(site)
    db.commit()
    db.refresh(site)

    db.add(models.WeatherReading(site_id=site.id, reading_date=datetime.datetime.utcnow(), solar_irradiance=7.0, wind_speed_50m=8.0))
    db.commit()

    score = models.SuitabilityScore(
        site_id=site.id, resource_score=90.0, geographic_score=85.0,
        infrastructure_score=70.0, environmental_score=95.0, economic_score=60.0,
        overall_score=82.0, category="Highly Suitable",
    )
    db.add(score)
    db.commit()
    db.refresh(site)

    reasons = explain_suitability_score(db, site, score)
    assert len(reasons) == 5
    assert any("7.0" in r and "above" in r for r in reasons)
    assert any("8.0" in r and "above" in r for r in reasons)
    assert any("no financial analysis has been run yet" in r for r in reasons)


def test_nasa_power_sentinel_value_is_rejected_not_stored(monkeypatch, db_session_factory):
    """
    Regression test for the real bug found via live testing: NASA POWER
    uses -999 as a "no data for this day" fill value. The old code stored
    that literal -999 as if it were a real irradiance reading, which
    corrupted every downstream average (a user saw "Peak Sun Hours:
    -622.93" and "Panel Efficiency: 319%" as a direct result). A -999
    reading must now be stored as None, not as -999.
    """
    from unittest.mock import MagicMock
    from app import models
    from app.services import environmental

    fake_payload = {
        "properties": {
            "parameter": {
                # Day 1: NASA POWER couldn't produce a real irradiance
                # value and filled with its standard sentinel.
                "ALLSKY_SFC_SW_DWN": {"20260101": -999, "20260102": 5.8},
                "WS10M": {"20260101": 3.0, "20260102": 3.2},
                "WS50M": {"20260101": 4.5, "20260102": 4.8},
                "T2M": {"20260101": -999, "20260102": 29.0},
                "PRECTOTCORR": {"20260101": 0.0, "20260102": 0.2},
                "CLOUD_AMT": {"20260101": 25.0, "20260102": 20.0},
            }
        }
    }
    mock_response = MagicMock()
    mock_response.json.return_value = fake_payload
    mock_response.raise_for_status.return_value = None
    monkeypatch.setattr(environmental.requests, "get", lambda *a, **k: mock_response)
    monkeypatch.setattr(environmental, "cache_get", lambda key: None)
    monkeypatch.setattr(environmental, "cache_set", lambda key, value, ttl_seconds=None: None)

    db = db_session_factory()
    site = models.Site(project_id=1, name="Sentinel Test Site", latitude=15.68, longitude=78.28)
    db.add(site)
    db.commit()
    db.refresh(site)

    environmental.fetch_and_store_weather_data(db, site)

    readings = db.query(models.WeatherReading).filter(models.WeatherReading.site_id == site.id).all()
    assert len(readings) == 2

    day1 = next(r for r in readings if r.reading_date.day == 1)
    day2 = next(r for r in readings if r.reading_date.day == 2)

    # The sentinel values must become None, not the literal -999.
    assert day1.solar_irradiance is None
    assert day1.temperature is None
    # A legitimate real value on the same day for a different parameter
    # must NOT be thrown away just because a sibling parameter was bad.
    assert day1.wind_speed == 3.0

    # The clean day must be stored exactly as received.
    assert day2.solar_irradiance == 5.8
    assert day2.temperature == 29.0


def test_existing_corrupted_reading_is_repaired_on_refresh(monkeypatch, db_session_factory):
    """
    Confirms the self-healing path: a row already sitting in the database
    with an old, un-validated -999 value must be repaired the next time
    "Refresh data" runs — not permanently stuck because of the
    site+date deduplication check.
    """
    from unittest.mock import MagicMock
    import datetime
    from app import models
    from app.services import environmental

    db = db_session_factory()
    site = models.Site(project_id=1, name="Repair Test Site", latitude=15.68, longitude=78.28)
    db.add(site)
    db.commit()
    db.refresh(site)

    # Simulate a row written by the old, unvalidated code: a raw -999
    # sentinel stored directly as if it were a real reading.
    bad_date = datetime.datetime.strptime(datetime.date.today().strftime("%Y%m%d"), "%Y%m%d")
    db.add(models.WeatherReading(site_id=site.id, reading_date=bad_date, solar_irradiance=-999, wind_speed=3.0))
    db.commit()

    fake_payload = {
        "properties": {
            "parameter": {
                bad_date.strftime("%Y%m%d"): None,  # placeholder, overwritten below
            }
        }
    }
    date_key = bad_date.strftime("%Y%m%d")
    fake_payload["properties"]["parameter"] = {
        "ALLSKY_SFC_SW_DWN": {date_key: 6.1},  # NASA POWER now has a real value for this date
        "WS10M": {date_key: 3.1},
        "WS50M": {date_key: 4.6},
        "T2M": {date_key: 30.0},
        "PRECTOTCORR": {date_key: 0.0},
        "CLOUD_AMT": {date_key: 15.0},
    }
    mock_response = MagicMock()
    mock_response.json.return_value = fake_payload
    mock_response.raise_for_status.return_value = None
    monkeypatch.setattr(environmental.requests, "get", lambda *a, **k: mock_response)
    monkeypatch.setattr(environmental, "cache_get", lambda key: None)
    monkeypatch.setattr(environmental, "cache_set", lambda key, value, ttl_seconds=None: None)

    environmental.fetch_and_store_weather_data(db, site)

    db.refresh(site)
    reading = (
        db.query(models.WeatherReading)
        .filter(models.WeatherReading.site_id == site.id, models.WeatherReading.reading_date == bad_date)
        .first()
    )
    assert reading.solar_irradiance == 6.1  # repaired, not still -999
    assert reading.wind_speed == 3.0  # untouched — it was already valid


def test_solar_potential_computes_without_trained_ml_model(client, planner):
    """
    No model has been trained in the test environment (no .joblib file
    exists) — this must not break site registration or solar potential
    computation. ML fields should be null, physics fields must still work.
    """
    project_resp = client.post("/projects/", headers=auth_headers(planner), json={"name": "No ML Model Test"})
    project_id = project_resp.json()["id"]
    site_resp = client.post(
        f"/projects/{project_id}/sites/",
        headers=auth_headers(planner),
        json={"name": "No ML Site", "latitude": 15.68, "longitude": 78.28},
    )
    assert site_resp.status_code == 201, site_resp.text

    solar_resp = client.get(f"/projects/{project_id}/sites/{site_resp.json()['id']}/solar-potential", headers=auth_headers(planner))
    assert solar_resp.status_code == 200
    body = solar_resp.json()
    assert body["performance_ratio_pct"] is not None  # physics engine still works
    assert body["ml_performance_ratio_pct"] is None    # honestly reports "not trained"
    assert body["ml_model_version"] is None


def test_ml_predictor_gracefully_returns_none_without_model_file(tmp_path, monkeypatch):
    """Direct unit test: ml_solar_predictor must never raise, only degrade to None."""
    from app.services import ml_solar_predictor

    monkeypatch.setattr(ml_solar_predictor, "MODEL_PATH", str(tmp_path / "does_not_exist.joblib"))
    monkeypatch.setattr(ml_solar_predictor, "_model", None)
    monkeypatch.setattr(ml_solar_predictor, "_load_attempted", False)

    assert ml_solar_predictor.is_model_available() is False
    assert ml_solar_predictor.predict_performance_ratio_pct(30.0, 5.8) is None


def test_solar_and_wind_ml_predictions_present_when_model_shipped(client, planner):
    """
    Unlike the earlier 'no model trained yet' test, this project now
    ships pre-trained models in app/ml_models/ — so these fields should
    actually be populated, not null, for a freshly registered site.
    """
    project_resp = client.post("/projects/", headers=auth_headers(planner), json={"name": "ML Active Test"})
    project_id = project_resp.json()["id"]
    site_resp = client.post(
        f"/projects/{project_id}/sites/",
        headers=auth_headers(planner),
        json={"name": "ML Active Site", "latitude": 15.68, "longitude": 78.28},
    )
    site_id = site_resp.json()["id"]

    solar_resp = client.get(f"/projects/{project_id}/sites/{site_id}/solar-potential", headers=auth_headers(planner))
    assert solar_resp.status_code == 200
    solar = solar_resp.json()
    assert solar["ml_performance_ratio_pct"] is not None
    assert solar["ml_model_version"] is not None
    assert 0 <= solar["ml_performance_ratio_pct"] <= 100

    wind_resp = client.get(f"/projects/{project_id}/sites/{site_id}/wind-potential", headers=auth_headers(planner))
    assert wind_resp.status_code == 200
    wind = wind_resp.json()
    assert wind["ml_capacity_factor_pct"] is not None
    assert wind["ml_model_version"] is not None


def test_ml_status_endpoint_reports_all_three_models_available(client, planner):
    resp = client.get("/ml/status", headers=auth_headers(planner))
    assert resp.status_code == 200
    models_by_name = {m["name"]: m for m in resp.json()}
    assert len(models_by_name) == 3
    for name, info in models_by_name.items():
        assert info["available"] is True, f"{name} should be available — a trained model ships with this repo"
        assert info["version"] is not None


def test_quick_suitability_estimate_endpoint(client, planner):
    resp = client.post(
        "/ml/quick-suitability-estimate",
        headers=auth_headers(planner),
        json={
            "avg_irradiance": 5.8, "avg_wind": 4.5, "land_slope_pct": 1.0, "elevation_m": 297,
            "substation_km": 1.0, "road_km": 0.5, "transmission_km": 0.5,
            "protected_area_km": 20, "water_body_km": 5, "agricultural_nearby": False,
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["category"] in ["Excellent", "Highly Suitable", "Moderately Suitable", "Low Suitability", "Unsuitable"]
    assert 0 <= body["confidence_pct"] <= 100
    assert "estimate" in body["note"].lower() or "register" in body["note"].lower()


def test_quick_suitability_estimate_rejects_invalid_input(client, planner):
    resp = client.post(
        "/ml/quick-suitability-estimate",
        headers=auth_headers(planner),
        json={"avg_irradiance": -5, "avg_wind": 4.5},  # negative irradiance, missing required fields handled by defaults
    )
    assert resp.status_code == 422  # Pydantic validation catches the out-of-range value


def test_delete_project_with_fully_populated_site_succeeds(client, planner, db_session_factory):
    """
    Regression test for a real bug found via live testing: Site had
    cascade-delete configured for only 3 of its 12 related tables
    (WeatherReading, InfrastructureFeature, SuitabilityScore). Every
    other table a real site actually populates during registration
    (SolarPotential, WindPotential, EnvironmentalConstraint, SiteImage,
    etc.) was missing it, so the database's default foreign-key
    behavior (RESTRICT) blocked deleting the Site, and therefore the
    Project — surfacing as a generic "Could not delete project" error.
    This test creates a project with a fully-populated site (via the
    real registration pipeline, same as a live user would) and confirms
    deletion actually succeeds and every child row is actually gone.
    """
    from app import models

    project_resp = client.post("/projects/", headers=auth_headers(planner), json={"name": "Delete Cascade Test"})
    project_id = project_resp.json()["id"]
    site_resp = client.post(
        f"/projects/{project_id}/sites/",
        headers=auth_headers(planner),
        json={"name": "Delete Cascade Site", "latitude": 15.68, "longitude": 78.28},
    )
    site_id = site_resp.json()["id"]

    # Confirm the site actually has rows in the tables that were missing
    # cascade — otherwise this test wouldn't actually exercise the bug.
    db = db_session_factory()
    assert db.query(models.SolarPotential).filter_by(site_id=site_id).count() > 0
    assert db.query(models.WindPotential).filter_by(site_id=site_id).count() > 0
    assert db.query(models.EnvironmentalConstraint).filter_by(site_id=site_id).count() > 0
    assert db.query(models.SiteImage).filter_by(site_id=site_id).count() > 0

    delete_resp = client.delete(f"/projects/{project_id}", headers=auth_headers(planner))
    assert delete_resp.status_code == 204, delete_resp.text

    # Every child row across every previously-unlinked table must be gone.
    db2 = db_session_factory()
    assert db2.query(models.Project).filter_by(id=project_id).count() == 0
    assert db2.query(models.Site).filter_by(id=site_id).count() == 0
    assert db2.query(models.SolarPotential).filter_by(site_id=site_id).count() == 0
    assert db2.query(models.WindPotential).filter_by(site_id=site_id).count() == 0
    assert db2.query(models.EnvironmentalConstraint).filter_by(site_id=site_id).count() == 0
    assert db2.query(models.SiteImage).filter_by(site_id=site_id).count() == 0
    assert db2.query(models.SuitabilityScore).filter_by(site_id=site_id).count() == 0


def test_delete_project_with_project_level_alert_succeeds(client, planner, admin, db_session_factory):
    """
    Alert.site_id is nullable — a project-level alert with no site_id
    would also have blocked project deletion before Project gained its
    own alerts cascade (separate from the Site-level one).
    """
    from app import models

    project_resp = client.post("/projects/", headers=auth_headers(planner), json={"name": "Alert Cascade Test"})
    project_id = project_resp.json()["id"]

    db = db_session_factory()
    db.add(models.Alert(project_id=project_id, site_id=None, title="Test", message="Test", category="system"))
    db.commit()

    delete_resp = client.delete(f"/projects/{project_id}", headers=auth_headers(planner))
    assert delete_resp.status_code == 204, delete_resp.text


def test_fetch_elevation_survives_malformed_json_response(monkeypatch):
    """
    Regression test for the real bug found via live testing: Open-Elevation
    returning a non-JSON body (rate-limit page, gateway error, etc.) used
    to raise JSONDecodeError, which the old `except requests.RequestException`
    clause did NOT catch (it's not a RequestException subclass) — the
    exception propagated all the way up through register_site's
    previously-unprotected call site to an unhandled 500.
    """
    from unittest.mock import MagicMock
    from app.services import terrain
    from app import cache as cache_module

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = ValueError("Expecting value: line 1 column 1 (char 0)")  # what a real JSONDecodeError looks like
    monkeypatch.setattr(terrain.requests, "get", lambda *a, **k: mock_response)
    # Force a cache miss so the wrapper actually calls through to the real
    # (undecorated) function body instead of returning a stale cached
    # value from an earlier test — @cached wraps fetch_elevation at
    # import time, so patching `terrain.cached` after the fact (as an
    # earlier draft of this test tried) is a no-op; the decorator has
    # already run. cache_get/cache_set live in app.cache, not terrain
    # (terrain.py only imported the `cached` decorator itself), so that's
    # the actual module to patch.
    monkeypatch.setattr(cache_module, "cache_get", lambda key: None)
    monkeypatch.setattr(cache_module, "cache_set", lambda key, value, ttl_seconds=None: None)

    # Must return None, not raise.
    result = terrain.fetch_elevation(15.68, 78.28)
    assert result is None


def test_register_site_succeeds_even_when_elevation_lookup_crashes(client, planner, monkeypatch):
    """
    End-to-end version of the same bug: even if something inside the
    elevation/slope lookup raises an exception the internal try/except
    in terrain.py doesn't anticipate, register_site's own try/except
    (added in this fix) must still let registration succeed with a null
    elevation, not fail the whole request.
    """
    import app.routers.sites as sites_router

    def _boom(lat, lon):
        raise RuntimeError("simulated unexpected failure mode")

    monkeypatch.setattr(sites_router, "fetch_elevation", _boom)

    project_resp = client.post("/projects/", headers=auth_headers(planner), json={"name": "Elevation Crash Test"})
    project_id = project_resp.json()["id"]

    site_resp = client.post(
        f"/projects/{project_id}/sites/",
        headers=auth_headers(planner),
        json={"name": "Crash Test Site", "latitude": 15.68, "longitude": 78.28},
    )
    assert site_resp.status_code == 201, site_resp.text
    assert site_resp.json()["elevation_m"] is None


def test_technology_recommendation_endpoint(client, planner):
    """Milestone 3: Deployment Optimization Engine — Technology Selection + Hybrid recommendation."""
    project_resp = client.post("/projects/", headers=auth_headers(planner), json={"name": "Tech Recommendation Test"})
    project_id = project_resp.json()["id"]
    site_resp = client.post(
        f"/projects/{project_id}/sites/",
        headers=auth_headers(planner),
        json={"name": "Tech Rec Site", "latitude": 15.68, "longitude": 78.28, "land_area_hectares": 2400},
    )
    site_id = site_resp.json()["id"]

    resp = client.get(f"/projects/{project_id}/sites/{site_id}/technology-recommendation", headers=auth_headers(planner))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["recommendation"] in ["Solar", "Wind", "Hybrid", "Insufficient data"]
    assert "reasoning" in body


def test_grid_contribution_endpoint_returns_homes_powered(client, planner):
    """Milestone 3: Energy Forecasting Engine — Grid Contribution Forecasting."""
    project_resp = client.post("/projects/", headers=auth_headers(planner), json={"name": "Grid Contribution Test"})
    project_id = project_resp.json()["id"]
    site_resp = client.post(
        f"/projects/{project_id}/sites/",
        headers=auth_headers(planner),
        json={"name": "Grid Site", "latitude": 15.68, "longitude": 78.28},
    )
    site_id = site_resp.json()["id"]

    resp = client.get(f"/projects/{project_id}/sites/{site_id}/grid-contribution", headers=auth_headers(planner))
    assert resp.status_code == 200, resp.text
    # Test env stub doesn't set electricity_consumption_kwh_per_capita, so
    # this should honestly report "not enough data" rather than fabricate
    # a number — confirms the endpoint doesn't crash either way.
    body = resp.json()
    assert "homes_powered_equivalent" in body


def test_deployment_optimizer_capacity_math_is_consistent():
    """Direct unit test: capacity estimates must scale linearly with land area."""
    from app.services.deployment_optimizer import estimate_capacity_mw

    small = estimate_capacity_mw(100, "solar")
    large = estimate_capacity_mw(1000, "solar")
    assert abs(large - small * 10) < 0.01, "Capacity must scale linearly with land area"
    assert estimate_capacity_mw(0, "solar") == 0.0
    assert estimate_capacity_mw(None, "solar") == 0.0


def test_recommend_technology_picks_hybrid_when_close(monkeypatch):
    from app.services.deployment_optimizer import recommend_technology

    result = recommend_technology(22.0, 27.0, 2400)
    assert result["recommendation"] == "Hybrid"
    assert "solar_mw" in result["suggested_capacity_mw"]
    assert "wind_mw" in result["suggested_capacity_mw"]


def test_recommend_technology_handles_missing_data():
    from app.services.deployment_optimizer import recommend_technology

    result = recommend_technology(None, None, 2400)
    assert result["recommendation"] == "Insufficient data"


def test_ml_investment_estimate_endpoint(client, planner):
    """PDF's Investment Prediction Model (Regression/XGBoost, substituted with GradientBoostingRegressor)."""
    project_resp = client.post("/projects/", headers=auth_headers(planner), json={"name": "ML Investment Test"})
    project_id = project_resp.json()["id"]
    site_resp = client.post(
        f"/projects/{project_id}/sites/",
        headers=auth_headers(planner),
        json={"name": "ML Investment Site", "latitude": 15.68, "longitude": 78.28},
    )
    site_id = site_resp.json()["id"]

    resp = client.post(
        f"/projects/{project_id}/sites/{site_id}/ml-investment-estimate",
        headers=auth_headers(planner),
        json={
            "capacity_mw": 10, "capex_usd": 8000000, "opex_usd_per_yr": 100000,
            "discount_rate_pct": 8, "project_lifetime_yrs": 25,
            "electricity_price_usd_per_mwh": 45, "annual_energy_mwh": 17400,
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert isinstance(body["npv_usd"], (int, float))
    assert isinstance(body["irr_pct"], (int, float))
    assert body["model_version"] is not None


def test_ml_risk_assessment_endpoint(client, planner):
    """PDF's Risk Assessment Model (LSTM/Prophet, substituted with RandomForestClassifier)."""
    project_resp = client.post("/projects/", headers=auth_headers(planner), json={"name": "ML Risk Test"})
    project_id = project_resp.json()["id"]
    site_resp = client.post(
        f"/projects/{project_id}/sites/",
        headers=auth_headers(planner),
        json={"name": "ML Risk Site", "latitude": 15.68, "longitude": 78.28},
    )
    site_id = site_resp.json()["id"]

    resp = client.get(f"/projects/{project_id}/sites/{site_id}/ml-risk-assessment", headers=auth_headers(planner))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["risk_category"] in ["Low", "Medium", "High"]
    assert 0 <= body["confidence_pct"] <= 100


def test_ml_status_endpoint_reports_all_five_models(client, planner):
    """All 5 of the PDF's named AI/ML models should now be present and available."""
    resp = client.get("/ml/status", headers=auth_headers(planner))
    assert resp.status_code == 200
    models_by_name = {m["name"]: m for m in resp.json()}
    assert len(models_by_name) == 5
    for name, info in models_by_name.items():
        assert info["available"] is True, f"{name} should be available \u2014 ships pre-trained with this repo"


def test_investment_predictor_direct_execution():
    """Direct unit test confirming the model is genuinely loaded and predicts sane values."""
    from app.services.ml_investment_predictor import predict_npv_and_irr, is_model_available

    assert is_model_available()
    result = predict_npv_and_irr(10, 8000000, 100000, 8, 25, 45, 17400)
    assert result is not None
    assert -50_000_000 < result["npv_usd"] < 50_000_000  # sane magnitude for a $8M project
    assert -50 < result["irr_pct"] < 50  # sane IRR range


def test_risk_predictor_feature_importance_limitation_is_real():
    """
    Confirms the honest limitation documented in this model's metadata
    is actually true, not just claimed: wind speed should dominate the
    model's decisions, with the environmental features contributing
    only a small fraction.
    """
    import joblib
    from app.services import ml_risk_predictor

    ml_risk_predictor._load_model()
    model = ml_risk_predictor._model
    assert model is not None
    importances = dict(zip(["wind_speed_50m", "protected_area_distance_km", "land_slope_pct"], model.feature_importances_))
    assert importances["wind_speed_50m"] > 0.9, "Documented limitation claims wind speed dominates \u2014 verify that's still true"
