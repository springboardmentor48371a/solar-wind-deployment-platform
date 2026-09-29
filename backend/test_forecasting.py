import pytest
from app.services.forecasting_engine import forecasting_engine


def test_monthly_forecast_generation():
    res = forecasting_engine.generate_forecast(
        technology="Solar",
        annual_expected_mwh=100000.0,
        forecast_type="monthly",
        electricity_price_per_kwh=0.08
    )

    assert res["forecast_type"] == "monthly"
    assert len(res["items"]) == 12
    assert res["total_expected_mwh"] > 0
    assert res["total_revenue_usd"] > 0

    # Solar should peak in summer months (Jun/Jul)
    june = next(it for it in res["items"] if it["period_label"] == "Jun")
    december = next(it for it in res["items"] if it["period_label"] == "Dec")
    assert june["expected_mwh"] > december["expected_mwh"]


def test_seasonal_forecast_generation():
    res = forecasting_engine.generate_forecast(
        technology="Wind",
        annual_expected_mwh=120000.0,
        forecast_type="seasonal"
    )

    assert res["forecast_type"] == "seasonal"
    assert len(res["items"]) == 4
