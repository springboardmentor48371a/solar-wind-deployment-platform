"""
Deployment Optimization Engine + the forecasting parts of the Energy
Forecasting Engine not already covered by solar_engine.py/wind_engine.py.

Covers the PDF spec's Milestone 3 modules:
  - Deployment Optimization Engine: Optimal location recommendation
    (already covered by the Suitability Scoring Engine + GIS comparison
    view), Technology selection, Capacity planning, Hybrid solar-wind
    recommendations, Expansion planning
  - Energy Forecasting Engine: Grid contribution forecasting (Seasonal
    generation prediction lives in environmental.py's climatology fetch;
    Long-term energy estimation and Revenue prediction are already
    covered by solar_engine.py/wind_engine.py's annual figures and
    financial.py's NPV/IRR model respectively)

All deterministic, formula-based — consistent with the rest of this
codebase's approach (see solar_engine.py/wind_engine.py's own docstrings
on why): explainable now, swappable for a trained model later without
touching the calling code.
"""

# NREL, "Land-Use Requirements for Solar Power Plants in the United
# States" (2013): capacity-weighted average of 8.9 acres/MW(AC) total
# land use across the full national sample this study analyzed.
# 8.9 acres = 3.6 hectares.
SOLAR_HECTARES_PER_MW = 3.6

# NREL wind land-use estimate: ~85 acres/MW of capacity (total project
# area including turbine spacing, not the small disturbed footprint —
# most of this land remains usable for agriculture/grazing between
# turbines, worth noting to anyone comparing the two numbers directly).
# 85 acres = 34.4 hectares.
WIND_HECTARES_PER_MW = 34.4

# A capacity-factor gap below this (percentage points) is treated as
# "close enough to consider both" rather than a clear winner — the
# threshold for recommending Hybrid instead of a single technology.
HYBRID_THRESHOLD_PCT = 8.0

# Rough global average persons-per-household, used only to translate a
# per-capita electricity figure into a "homes powered" estimate for
# grid-contribution communication — an approximation, not a precise
# demographic figure for any specific country.
ASSUMED_HOUSEHOLD_SIZE = 4.0


def estimate_capacity_mw(land_area_hectares: float, technology: str) -> float:
    """
    How much installed capacity a site's land area could realistically
    support, using published NREL land-use intensity figures rather
    than a guess.
    """
    if land_area_hectares is None or land_area_hectares <= 0:
        return 0.0
    if technology == "wind":
        return round(land_area_hectares / WIND_HECTARES_PER_MW, 2)
    if technology == "hybrid":
        # Co-located hybrid sites don't need double the land — wind
        # turbines are sparse enough that solar arrays can often occupy
        # the ground between them. Conservative approximation: treat
        # 70% of the land as available for solar under/around the
        # turbines, and size wind capacity off the full area as usual.
        wind_mw = round(land_area_hectares / WIND_HECTARES_PER_MW, 2)
        solar_mw = round((land_area_hectares * 0.7) / SOLAR_HECTARES_PER_MW, 2)
        return round(wind_mw + solar_mw, 2)
    return round(land_area_hectares / SOLAR_HECTARES_PER_MW, 2)  # default: solar


def recommend_technology(solar_capacity_factor_pct: float | None, wind_capacity_factor_pct: float | None, land_area_hectares: float | None) -> dict:
    """
    Technology Selection + Hybrid Solar-Wind Recommendations, in one
    call since they're the same decision. Compares the two engines'
    already-computed capacity factors (not a new prediction — this
    reads what solar_engine.py/wind_engine.py already calculated) and
    recommends Solar, Wind, or Hybrid with a specific capacity split.
    """
    if solar_capacity_factor_pct is None and wind_capacity_factor_pct is None:
        return {
            "recommendation": "Insufficient data",
            "reasoning": "Neither solar nor wind potential has been computed for this site yet — run \u201cRefresh data\u201d first.",
            "suggested_capacity_mw": {},
        }

    solar_cf = solar_capacity_factor_pct or 0.0
    wind_cf = wind_capacity_factor_pct or 0.0
    gap = abs(solar_cf - wind_cf)

    if gap <= HYBRID_THRESHOLD_PCT and solar_cf > 0 and wind_cf > 0:
        capacity = estimate_capacity_mw(land_area_hectares, "hybrid") if land_area_hectares else None
        return {
            "recommendation": "Hybrid",
            "reasoning": f"Solar ({solar_cf}% capacity factor) and wind ({wind_cf}% capacity factor) are close enough (within {HYBRID_THRESHOLD_PCT} points) that neither clearly dominates \u2014 a hybrid deployment captures both resources and smooths output across day/night and seasonal wind patterns.",
            "suggested_capacity_mw": {"solar_mw": estimate_capacity_mw((land_area_hectares or 0) * 0.7, "solar") if land_area_hectares else None, "wind_mw": estimate_capacity_mw(land_area_hectares, "wind") if land_area_hectares else None},
        }
    elif solar_cf >= wind_cf:
        return {
            "recommendation": "Solar",
            "reasoning": f"Solar capacity factor ({solar_cf}%) clearly exceeds wind ({wind_cf}%) at this site.",
            "suggested_capacity_mw": {"solar_mw": estimate_capacity_mw(land_area_hectares, "solar") if land_area_hectares else None},
        }
    else:
        return {
            "recommendation": "Wind",
            "reasoning": f"Wind capacity factor ({wind_cf}%) clearly exceeds solar ({solar_cf}%) at this site.",
            "suggested_capacity_mw": {"wind_mw": estimate_capacity_mw(land_area_hectares, "wind") if land_area_hectares else None},
        }


def estimate_grid_contribution(expected_annual_output_mwh: float | None, electricity_consumption_kwh_per_capita: float | None) -> dict | None:
    """
    Grid Contribution Forecasting: translates an annual output figure
    (already computed by solar_engine.py/wind_engine.py — this doesn't
    predict anything new) into a "homes powered" estimate, using the
    real World Bank per-capita electricity consumption figure for the
    site's own country rather than a generic global constant.
    """
    if expected_annual_output_mwh is None or not electricity_consumption_kwh_per_capita or electricity_consumption_kwh_per_capita <= 0:
        return None
    annual_kwh_per_household = electricity_consumption_kwh_per_capita * ASSUMED_HOUSEHOLD_SIZE
    if annual_kwh_per_household <= 0:
        return None
    homes_powered = round((expected_annual_output_mwh * 1000) / annual_kwh_per_household)
    return {
        "homes_powered_equivalent": homes_powered,
        "basis": f"Based on {electricity_consumption_kwh_per_capita:.0f} kWh/capita/year (World Bank, this site's country) \u00d7 an assumed {ASSUMED_HOUSEHOLD_SIZE:.0f}-person household \u2014 an approximation, not a precise local grid-demand study.",
    }
