"""
Energy Forecasting Engine (Module 8) + Investment & Feasibility Analysis
(Module 13 report data).

Projects long-term output with a modest annual degradation rate and derives
a simple CAPEX / revenue / payback estimate. Replace the flat cost
assumptions with live financial-modeling-tool integrations (per the
architecture diagram's "Financial Modeling Tools" external integration)
when available.
"""

SOLAR_DEGRADATION = 0.005   # 0.5%/yr panel degradation
WIND_DEGRADATION = 0.003    # 0.3%/yr turbine degradation

SOLAR_CAPEX_PER_MW_USD = 850_000
WIND_CAPEX_PER_MW_USD = 1_300_000
PRICE_PER_MWH_USD = 55


def forecast_energy(solar: dict, wind: dict, recommended_technology: str, land_area_hectares: float = 5.0) -> dict:
    if recommended_technology == "solar":
        annual_year1 = solar["expected_energy_output_mwh_year"]
        degradation = SOLAR_DEGRADATION
        capacity_mw = round(land_area_hectares / 2.0, 3)
        capex = capacity_mw * SOLAR_CAPEX_PER_MW_USD
    elif recommended_technology == "wind":
        annual_year1 = wind["expected_annual_energy_mwh"]
        degradation = WIND_DEGRADATION
        capacity_mw = round((land_area_hectares / 8.0) * 2.5, 3)
        capex = capacity_mw * WIND_CAPEX_PER_MW_USD
    else:  # hybrid
        annual_year1 = solar["expected_energy_output_mwh_year"] + wind["expected_annual_energy_mwh"]
        degradation = (SOLAR_DEGRADATION + WIND_DEGRADATION) / 2
        capacity_mw = round(land_area_hectares / 2.0, 3) + round((land_area_hectares / 8.0) * 2.5, 3)
        capex = (round(land_area_hectares / 2.0, 3) * SOLAR_CAPEX_PER_MW_USD) + \
                (round((land_area_hectares / 8.0) * 2.5, 3) * WIND_CAPEX_PER_MW_USD)

    def output_at_year(n):
        return round(annual_year1 * ((1 - degradation) ** (n - 1)), 1)

    year1 = output_at_year(1)
    year5 = output_at_year(5)
    year10 = output_at_year(10)
    year25 = output_at_year(25)

    annual_revenue = round(year1 * PRICE_PER_MWH_USD, 2)
    payback_years = round(capex / annual_revenue, 1) if annual_revenue > 0 else None

    return {
        "year1_mwh": year1,
        "year5_mwh": year5,
        "year10_mwh": year10,
        "year25_mwh": year25,
        "estimated_capex_usd": round(capex, 2),
        "estimated_annual_revenue_usd": annual_revenue,
        "payback_period_years": payback_years,
    }
