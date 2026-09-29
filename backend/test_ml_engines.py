import pytest
from app.ml.solar_engine import solar_ml_engine
from app.ml.wind_engine import wind_ml_engine


def test_solar_prediction_pipeline():
    features = {
        "latitude": 35.15,
        "longitude": -115.50,
        "elevation_m": 700.0,
        "slope_deg": 1.5,
        "cloud_cover_pct": 14.0,
        "temperature_c": 24.0,
        "rainfall_mm": 180.0,
        "ndvi": 0.12,
        "ghi_kwh_m2_day": 6.2
    }
    pred = solar_ml_engine.predict(features, plant_capacity_mw=50.0)

    assert "annual_irradiance_kwh" in pred
    assert "peak_sun_hours" in pred
    assert "expected_mwh_year" in pred
    assert "capacity_factor" in pred
    assert "performance_ratio" in pred
    assert "solar_suitability_score" in pred
    assert "model_metrics" in pred
    assert "feature_importances" in pred

    assert pred["capacity_factor"] > 15.0
    assert pred["expected_mwh_year"] > 50000.0
    assert 0.0 <= pred["solar_suitability_score"] <= 100.0


def test_wind_prediction_pipeline():
    features = {
        "latitude": 35.20,
        "longitude": -101.80,
        "elevation_m": 1000.0,
        "slope_deg": 2.0,
        "temperature_c": 16.0,
        "wind_speed_100m": 8.8
    }
    pred = wind_ml_engine.predict(features, plant_capacity_mw=50.0)

    assert "avg_wind_speed" in pred
    assert "wind_power_density" in pred
    assert "turbulence_intensity" in pred
    assert "capacity_factor" in pred
    assert "expected_mwh_year" in pred
    assert "model_metrics" in pred

    assert pred["capacity_factor"] > 20.0
    assert pred["wind_power_density"] > 200.0
    assert pred["expected_mwh_year"] > 70000.0
