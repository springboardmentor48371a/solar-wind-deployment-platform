"""
Wind Potential Prediction Engine — the sub-models the PDF spec lists
separately: wind resource assessment, turbine suitability analysis, wind
power estimation, and the Wind Metrics block (average wind speed, wind
power density, turbulence intensity, capacity factor, expected AEP).

Deterministic wind-physics formulas (wind-shear power law, IEC turbulence
class, Rayleigh-distribution AEP approximation) — not the AI/ML layer.
"""

import math
from statistics import mean, pstdev

from sqlalchemy.orm import Session

from app import models
from app.services import ml_wind_predictor

AIR_DENSITY_SEA_LEVEL_KG_M3 = 1.225
HUB_HEIGHT_M = 80.0  # typical modern onshore turbine hub height
WIND_SHEAR_EXPONENT = 1.0 / 7.0  # standard Hellmann exponent for open terrain


def _air_density_at_elevation(elevation_m: float | None) -> float:
    """Barometric-formula approximation of air density falloff with altitude."""
    elevation_m = elevation_m or 0.0
    return round(AIR_DENSITY_SEA_LEVEL_KG_M3 * math.exp(-elevation_m / 8500.0), 4)


def _extrapolate_to_hub_height(speed_50m: float) -> float:
    """
    Power-law extrapolation from the 50m NASA POWER reading to a modern
    80m hub height: v_hub = v_ref * (h_hub / h_ref) ^ alpha
    """
    return speed_50m * (HUB_HEIGHT_M / 50.0) ** WIND_SHEAR_EXPONENT


def _turbine_class(avg_speed_ms: float) -> str:
    """Coarse IEC 61400-1 wind class proxy from mean hub-height wind speed."""
    if avg_speed_ms >= 10.0:
        return "IEC Class I (high wind)"
    if avg_speed_ms >= 8.5:
        return "IEC Class II (medium wind)"
    if avg_speed_ms >= 7.5:
        return "IEC Class III (low wind)"
    return "IEC Class IV / below typical utility-scale threshold"


def _turbine_suitability_score(avg_speed_ms: float, turbulence_pct: float) -> float:
    """0-100: rewards higher mean speed, penalizes high turbulence (fatigue loading risk)."""
    speed_score = min(avg_speed_ms / 11.0, 1.0) * 100
    turbulence_penalty = min(turbulence_pct, 30.0) * 1.2
    return round(max(speed_score - turbulence_penalty, 0), 1)


def compute_wind_potential(db: Session, site: models.Site) -> models.WindPotential:
    readings = site.weather_readings
    speeds_50m = [
        r.wind_speed_50m if r.wind_speed_50m is not None else r.wind_speed
        for r in readings
        if r.wind_speed_50m is not None or r.wind_speed is not None
    ]

    if not speeds_50m:
        avg_hub_speed = 0.0
        turbulence_pct = 0.0
    else:
        hub_speeds = [_extrapolate_to_hub_height(s) for s in speeds_50m]
        avg_hub_speed = round(mean(hub_speeds), 2)
        # Turbulence intensity = std deviation / mean, expressed as %
        std = pstdev(hub_speeds) if len(hub_speeds) > 1 else 0.0
        turbulence_pct = round((std / avg_hub_speed) * 100, 1) if avg_hub_speed else 0.0

    air_density = _air_density_at_elevation(site.elevation_m)
    wind_power_density = round(0.5 * air_density * (avg_hub_speed**3), 1)  # W/m^2

    turbine_class = _turbine_class(avg_hub_speed)
    suitability = _turbine_suitability_score(avg_hub_speed, turbulence_pct)

    # Rayleigh-distribution capacity factor approximation for a modern
    # utility turbine (commonly used first-pass estimate before a full
    # manufacturer power curve is available): CF ≈ 0.087 * v_mean - 0.1frs
    # clamped to a realistic band.
    capacity_factor = round(min(max(0.087 * avg_hub_speed * 100 - 8, 5), 55), 1)
    expected_aep_per_mw = round((capacity_factor / 100) * 8760, 1)  # MWh/yr per installed MW

    avg_wind_speed_50m_raw = mean(speeds_50m) if speeds_50m else 0.0
    ml_capacity_factor = ml_wind_predictor.predict_capacity_factor_pct(avg_wind_speed_50m_raw, site.elevation_m or 0.0)
    ml_expected_aep = None
    if ml_capacity_factor is not None:
        ml_expected_aep = round((ml_capacity_factor / 100) * 8760, 1)

    record = models.WindPotential(
        site_id=site.id,
        average_wind_speed_ms=avg_hub_speed,
        wind_power_density_w_m2=wind_power_density,
        turbulence_intensity_pct=turbulence_pct,
        turbine_suitability_score=suitability,
        turbine_class=turbine_class,
        expected_aep_mwh_yr=expected_aep_per_mw,
        capacity_factor_pct=capacity_factor,
        ml_capacity_factor_pct=ml_capacity_factor,
        ml_expected_aep_mwh_yr=ml_expected_aep,
        ml_model_version=ml_wind_predictor.model_version(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
