"""
Turns a computed SuitabilityScore back into plain-language reasoning by
re-reading the same underlying data the scoring engine (scoring.py) used
— weather averages, terrain, infrastructure distances, environmental
constraints, financial analysis. Used by both the fixed-format PDF/Excel
site-assessment export (routers/reports.py) and the custom Report
Builder (routers/report_templates.py), so a report says *why* a site
scored the way it did, not just what the number is.

Kept as its own service module rather than living inside either router
so neither report format has to import from the other.
"""

import statistics

from sqlalchemy.orm import Session

from app import models

# Same benchmark constants scoring.py uses, duplicated here (not imported)
# on purpose: this module only needs them for human-readable explanation
# text, and importing scoring.py's internals would couple the report
# format to scoring implementation details it doesn't otherwise depend on.
IRRADIANCE_BENCHMARK = 6.5   # kWh/m^2/day
WIND_SPEED_BENCHMARK = 7.5   # m/s


def explain_suitability_score(db: Session, site: models.Site, score: models.SuitabilityScore) -> list[str]:
    reasons = []

    readings = site.weather_readings
    if readings:
        avg_irradiance = round(statistics.mean(r.solar_irradiance for r in readings if r.solar_irradiance is not None), 2) if any(r.solar_irradiance is not None for r in readings) else None
        avg_wind = round(statistics.mean(r.wind_speed_50m or r.wind_speed for r in readings if (r.wind_speed_50m or r.wind_speed) is not None), 2) if any((r.wind_speed_50m or r.wind_speed) is not None for r in readings) else None
        parts = []
        if avg_irradiance is not None:
            comparison = "above" if avg_irradiance >= IRRADIANCE_BENCHMARK else "below"
            parts.append(f"average solar irradiance of {avg_irradiance} kWh/m\u00b2/day ({comparison} the {IRRADIANCE_BENCHMARK} benchmark)")
        if avg_wind is not None:
            comparison = "above" if avg_wind >= WIND_SPEED_BENCHMARK else "below"
            parts.append(f"average wind speed of {avg_wind} m/s ({comparison} the {WIND_SPEED_BENCHMARK} m/s benchmark)")
        if parts:
            reasons.append(f"Resource Availability ({score.resource_score}/100, 35% weight): based on {' and '.join(parts)}.")
        else:
            reasons.append(f"Resource Availability ({score.resource_score}/100, 35% weight): weather data collected but incomplete.")
    else:
        reasons.append(f"Resource Availability ({score.resource_score}/100, 35% weight): no weather data collected yet \u2014 score reflects a neutral default, not measured conditions.")

    geo_parts = []
    if site.land_slope_pct is not None:
        geo_parts.append(f"land slope of {site.land_slope_pct}%")
    if site.elevation_m is not None:
        geo_parts.append(f"elevation of {site.elevation_m}m" + (" (above the 2,000m penalty threshold)" if site.elevation_m > 2000 else ""))
    reasons.append(
        f"Geographic Suitability ({score.geographic_score}/100, 25% weight): "
        + (f"based on {' and '.join(geo_parts)}." if geo_parts else "terrain data not yet collected \u2014 run \u201cRefresh data\u201d to populate this.")
    )

    infra_features = {f.feature_type: f.distance_km for f in site.infrastructure_features}
    if infra_features:
        infra_desc = ", ".join(f"{k.replace('_', ' ')} at {v}km" for k, v in infra_features.items())
        reasons.append(f"Infrastructure Accessibility ({score.infrastructure_score}/100, 15% weight): nearest {infra_desc}.")
    else:
        reasons.append(f"Infrastructure Accessibility ({score.infrastructure_score}/100, 15% weight): no infrastructure data collected yet.")

    env = (
        db.query(models.EnvironmentalConstraint)
        .filter(models.EnvironmentalConstraint.site_id == site.id)
        .order_by(models.EnvironmentalConstraint.fetched_at.desc())
        .first()
    )
    if env:
        env_parts = []
        if env.protected_area_distance_km is not None:
            flag = " (within the 10km caution zone)" if env.protected_area_distance_km < 10 else ""
            env_parts.append(f"nearest protected area {env.protected_area_distance_km}km away{flag}")
        if env.water_body_distance_km is not None:
            flag = " (within 500m \u2014 penalized)" if env.water_body_distance_km < 0.5 else ""
            env_parts.append(f"nearest water body {env.water_body_distance_km}km away{flag}")
        if env.agricultural_land_nearby:
            env_parts.append("agricultural land nearby (penalized)")
        reasons.append(f"Environmental Impact ({score.environmental_score}/100, 15% weight): {'; '.join(env_parts) if env_parts else 'no constraints detected nearby.'}")
    else:
        reasons.append(f"Environmental Impact ({score.environmental_score}/100, 15% weight): environmental data not yet collected.")

    financial = (
        db.query(models.FinancialAnalysis)
        .filter(models.FinancialAnalysis.site_id == site.id)
        .order_by(models.FinancialAnalysis.computed_at.desc())
        .first()
    )
    if financial:
        reasons.append(
            f"Economic Feasibility ({score.economic_score}/100, 10% weight): based on a computed IRR of "
            f"{financial.irr_pct if financial.irr_pct is not None else '\u2014'}% and LCOE of "
            f"${financial.lcoe_usd_per_mwh if financial.lcoe_usd_per_mwh is not None else '\u2014'}/MWh."
        )
    else:
        reasons.append(
            f"Economic Feasibility ({score.economic_score}/100, 10% weight): no financial analysis has been run yet \u2014 "
            "this score is a temporary proxy based on infrastructure proximity, not real cost/revenue assumptions."
        )

    return reasons
