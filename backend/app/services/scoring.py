"""
Site Suitability Scoring Engine — deterministic weighted formula.

This is explicitly NOT the AI/ML prediction layer (Solar/Wind Prediction
Models). It's the rule-based weighted scoring formula spelled out in your
project spec:

    Deployment Suitability Score =
        Renewable Resource Availability (35%)
      + Geographic Suitability          (25%)
      + Infrastructure Accessibility    (15%)
      + Environmental Impact            (15%)
      + Economic Feasibility            (10%)

Each sub-score is normalized to 0-100 using simple, explainable rules
against the data already collected (weather readings, elevation/slope,
infrastructure distances). Swap any of the `_score_*` functions for a
trained model call next week without touching the weighting logic.
"""

from statistics import mean

from sqlalchemy.orm import Session

from app import models


def _score_resource_availability(site: models.Site) -> float:
    """Higher solar irradiance + wind speed => higher score."""
    readings = site.weather_readings
    if not readings:
        return 0.0

    irradiance_vals = [r.solar_irradiance for r in readings if r.solar_irradiance is not None]
    # Prefer 50m (turbine hub height) wind speed where available — falls
    # back to the 10m surface reading for any older rows fetched before
    # WS50M was added to the ingestion pipeline.
    wind_vals = [
        r.wind_speed_50m if r.wind_speed_50m is not None else r.wind_speed
        for r in readings
        if r.wind_speed_50m is not None or r.wind_speed is not None
    ]

    avg_irradiance = mean(irradiance_vals) if irradiance_vals else 0
    avg_wind = mean(wind_vals) if wind_vals else 0

    # Normalize: ~6.5 kWh/m^2/day is excellent solar, ~7.5 m/s is excellent wind
    irradiance_score = min(avg_irradiance / 6.5, 1.0) * 100
    wind_score = min(avg_wind / 7.5, 1.0) * 100

    return round((irradiance_score + wind_score) / 2, 1)


def _score_geographic_suitability(site: models.Site) -> float:
    """Lower slope and moderate elevation score higher (easier to build on)."""
    score = 100.0
    if site.land_slope_pct is not None:
        # Slope over 15% becomes increasingly unsuitable for large installations
        score -= min(site.land_slope_pct * 4, 60)
    if site.elevation_m is not None and site.elevation_m > 2000:
        # Very high elevation adds construction/logistics difficulty
        score -= 15
    return round(max(score, 0), 1)


def _score_infrastructure_accessibility(site: models.Site) -> float:
    """Closer to substations/roads/transmission lines scores higher."""
    features = {f.feature_type: f.distance_km for f in site.infrastructure_features}
    if not features:
        # Fall back to the manually entered distance if OSM data isn't available yet
        if site.distance_to_substation_km is not None:
            return round(max(100 - site.distance_to_substation_km * 5, 0), 1)
        return 50.0  # neutral default when nothing is known

    scores = []
    weights = {"substation": 0.5, "road": 0.3, "transmission_line": 0.2}
    for feature_type, weight in weights.items():
        distance = features.get(feature_type)
        if distance is None:
            continue
        # 0km = 100 score, 20km+ = 0 score
        feature_score = max(100 - distance * 5, 0)
        scores.append(feature_score * weight)

    return round(sum(scores) / sum(weights.values()), 1) if scores else 50.0


def _score_environmental_impact(db: Session, site: models.Site) -> float:
    """
    Real rule, now that land_data.py provides it: penalize proximity to
    protected areas (real siting risk — permitting friction, ecological
    impact) and moderately penalize proximity to water bodies. Falls back
    to the cloud-cover heuristic only if no EnvironmentalConstraint row
    exists yet for this site (e.g. refresh-data hasn't run since this
    feature was added).
    """
    constraint = (
        db.query(models.EnvironmentalConstraint)
        .filter(models.EnvironmentalConstraint.site_id == site.id)
        .order_by(models.EnvironmentalConstraint.fetched_at.desc())
        .first()
    )
    if constraint is None:
        readings = site.weather_readings
        if not readings:
            return 70.0  # neutral-ish default
        cloud_vals = [r.cloud_cover_pct for r in readings if r.cloud_cover_pct is not None]
        avg_cloud = mean(cloud_vals) if cloud_vals else 0
        return round(max(100 - (avg_cloud * 0.5), 0), 1)

    score = 100.0
    # Under 2km from a protected area is a serious siting/permitting risk;
    # scales back to no penalty by 10km out.
    if constraint.protected_area_distance_km is not None:
        score -= max(0, (10 - constraint.protected_area_distance_km)) * 6
    # Under 500m from a water body carries a smaller, but real, ecological
    # and permitting penalty.
    if constraint.water_body_distance_km is not None and constraint.water_body_distance_km < 0.5:
        score -= 10
    return round(max(score, 0), 1)


def _score_economic_feasibility(db: Session, site: models.Site) -> float:
    """
    Uses the most recent real FinancialAnalysis for this site (LCOE and
    IRR — the two metrics an investor actually screens projects on) if
    one has been run. Falls back to the infrastructure-proximity proxy
    (grid connection cost dominates early-stage economics before a real
    capex/opex model exists) when no financial analysis has been computed yet.
    """
    analysis = (
        db.query(models.FinancialAnalysis)
        .filter(models.FinancialAnalysis.site_id == site.id)
        .order_by(models.FinancialAnalysis.computed_at.desc())
        .first()
    )
    if analysis is None:
        return _score_infrastructure_accessibility(site)

    score = 50.0  # neutral baseline, adjusted by whichever metrics are available
    if analysis.irr_pct is not None:
        # 0% IRR -> 0, 20%+ IRR -> full marks on this half of the score
        score += min(max(analysis.irr_pct, 0), 20) / 20 * 40 - 20
    if analysis.lcoe_usd_per_mwh is not None:
        # $30/MWh (cheap) -> full marks, $120/MWh (expensive) -> zero
        lcoe_score = max(0, min(1, (120 - analysis.lcoe_usd_per_mwh) / 90)) * 40
        score += lcoe_score - 20
    return round(max(min(score, 100), 0), 1)


CATEGORY_THRESHOLDS = [
    (85, "Excellent"),
    (70, "Highly Suitable"),
    (55, "Moderately Suitable"),
    (35, "Low Suitability"),
    (0, "Unsuitable"),
]


def _category_for_score(score: float) -> str:
    for threshold, label in CATEGORY_THRESHOLDS:
        if score >= threshold:
            return label
    return "Unsuitable"


def compute_site_suitability(db: Session, site: models.Site) -> models.SuitabilityScore:
    resource = _score_resource_availability(site)
    geographic = _score_geographic_suitability(site)
    infrastructure = _score_infrastructure_accessibility(site)
    environmental = _score_environmental_impact(db, site)
    economic = _score_economic_feasibility(db, site)

    overall = round(
        resource * 0.35
        + geographic * 0.25
        + infrastructure * 0.15
        + environmental * 0.15
        + economic * 0.10,
        1,
    )

    score = models.SuitabilityScore(
        site_id=site.id,
        resource_score=resource,
        geographic_score=geographic,
        infrastructure_score=infrastructure,
        environmental_score=environmental,
        economic_score=economic,
        overall_score=overall,
        category=_category_for_score(overall),
    )
    db.add(score)
    db.commit()
    db.refresh(score)
    return score
