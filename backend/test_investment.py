import pytest
from app.services.investment_engine import investment_engine


def test_investment_financial_modeling():
    res = investment_engine.calculate_investment(
        site_name="Test Solar Site",
        technology="Solar",
        capacity_mw=50.0,
        annual_expected_mwh=90000.0,
        distance_to_grid_km=4.0,
        electricity_price_per_kwh=0.075,
        discount_rate_pct=6.5,
        project_lifespan_years=25
    )

    assert "capex_usd" in res
    assert "annual_revenue_usd" in res
    assert "lcoe_per_mwh" in res
    assert "npv_usd" in res
    assert "irr_pct" in res
    assert "payback_years" in res
    assert "recommendation" in res
    assert "cash_flow_projection" in res

    assert res["capex_usd"] > 0
    assert res["annual_revenue_usd"] > 0
    assert res["payback_years"] < 20.0
    assert len(res["cash_flow_projection"]) == 25
    assert res["recommendation"] in ["Highly Recommended", "Recommended", "Moderate", "Not Recommended"]
