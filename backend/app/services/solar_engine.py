"""
Solar Potential Prediction Engine — the sub-models the PDF spec lists
separately from the general suitability score: panel efficiency
prediction, shading analysis, solar resource mapping, and the Solar
Metrics block (annual irradiance, peak sun hours, expected energy
output, capacity factor, performance ratio).

Deterministic PV-physics formulas throughout (temperature de-rating,
horizon-obstruction shading, PVWatts-style output) — explicitly not the
AI/ML prediction layer, same as scoring.py.
"""

from statistics import mean, pstdev

from sqlalchemy.orm import Session

from app import models
from app.services import ml_solar_predictor

# Standard Test Condition reference values
STC_IRRADIANCE_W_M2 = 1000.0
STC_TEMP_C = 25.0
DEFAULT_PANEL_STC_EFFICIENCY_PCT = 20.0  # typical modern monocrystalline module
TEMP_COEFFICIENT_PCT_PER_C = -0.35  # typical silicon panel: -0.35%/°C above 25°C
NOCT_C = 45.0  # nominal operating cell temp, used to estimate cell temp from ambient + irradiance


def _estimate_cell_temperature(ambient_temp_c: float, irradiance_w_m2: float) -> float:
    """Standard NOCT model: cell temp rises above ambient with irradiance."""
    return ambient_temp_c + (irradiance_w_m2 / 800.0) * (NOCT_C - 20.0)


def _panel_efficiency_pct(avg_temp_c: float, avg_irradiance_kwh_m2_day: float) -> float:
    """Temperature-derated panel efficiency vs the STC-rated 20%."""
    irradiance_w_m2 = (avg_irradiance_kwh_m2_day / 5.0) * STC_IRRADIANCE_W_M2  # rough daytime-average proxy
    cell_temp = _estimate_cell_temperature(avg_temp_c, irradiance_w_m2)
    delta_t = cell_temp - STC_TEMP_C
    efficiency = DEFAULT_PANEL_STC_EFFICIENCY_PCT * (1 + (TEMP_COEFFICIENT_PCT_PER_C / 100) * delta_t)
    return round(max(efficiency, 0), 2)


def _shading_loss_pct(site: models.Site) -> float:
    """
    Horizon-obstruction proxy: steeper local slope and higher elevation
    variance around the site increase the chance of terrain self-shading
    in morning/evening sun angles. This is a terrain-based estimate —
    true shading analysis needs a full horizon profile (DEM ray-tracing),
    noted as a future refinement once raster DEM tiles are wired in via
    geo_utils.read_local_dem_elevation.
    """
    slope = site.land_slope_pct or 0.0
    # 0% slope -> ~1% inherent loss (self-shading between rows etc);
    # 25%+ slope -> up to 18% loss from terrain-driven horizon obstruction.
    loss = 1.0 + min(slope, 25.0) * 0.68
    return round(min(loss, 20.0), 2)


def compute_solar_potential(db: Session, site: models.Site) -> models.SolarPotential:
    readings = site.weather_readings
    irradiance_vals = [r.solar_irradiance for r in readings if r.solar_irradiance is not None]
    temp_vals = [r.temperature for r in readings if r.temperature is not None]
    cloud_vals = [r.cloud_cover_pct for r in readings if r.cloud_cover_pct is not None]

    # Real, significant bug found via live testing: defaulting missing
    # irradiance data to 0.0 (like an empty list of readings) silently
    # implies "this site receives literally zero sunlight" — physically
    # absurd for anywhere on Earth, and the value then multiplies
    # through every downstream calculation, cascading into 0 peak sun
    # hours, 0 expected output, 0 capacity factor, and ultimately 0
    # annual energy fed into the financial model — which is why NPV,
    # IRR, LCOE, and Payback all came back nonsensical or null even
    # though the site itself is a real, working solar location. Using
    # a genuinely reasonable global-average fallback (4.5 kWh/m^2/day,
    # a commonly-cited moderate global average) instead of 0.0 matches
    # the same pattern already used for avg_temp/avg_cloud below —
    # neither of those silently zeroes out the whole computation when
    # data is missing, and irradiance shouldn't either.
    avg_daily_irradiance = mean(irradiance_vals) if irradiance_vals else 4.5  # kWh/m^2/day
    avg_temp = mean(temp_vals) if temp_vals else 20.0
    avg_cloud = mean(cloud_vals) if cloud_vals else 30.0

    annual_irradiance = round(avg_daily_irradiance * 365, 1)
    peak_sun_hours = round(avg_daily_irradiance, 2)  # kWh/m^2/day numerically equals PSH

    panel_efficiency = _panel_efficiency_pct(avg_temp, avg_daily_irradiance)
    shading_loss = _shading_loss_pct(site)

    # Soiling/cloud-driven derate on top of temperature de-rating and shading.
    soiling_loss_pct = min(avg_cloud * 0.08, 6.0)
    performance_ratio = round(
        max(0, 100 - (100 - panel_efficiency / DEFAULT_PANEL_STC_EFFICIENCY_PCT * 100) - shading_loss - soiling_loss_pct),
        1,
    )
    # Clamp performance ratio to a realistic PV system band (typically 70-85%)
    performance_ratio = round(min(max(performance_ratio, 40.0), 88.0), 1)

    # PVWatts-style annual yield per installed MWp:
    # Energy (MWh/yr) = irradiance(kWh/m2/yr) * PR * capacity(MW) / STC_irradiance(1 kWh/m2)
    expected_output_mwh_per_mwp = round((annual_irradiance / 1.0) * (performance_ratio / 100), 1)
    capacity_factor = round(min((expected_output_mwh_per_mwp / 8760) * 100, 35.0), 1)

    # ML-Assisted Prediction (Beta) — runs alongside the physics numbers
    # above, never replacing them. Returns None (and the app shows
    # "not trained yet") until someone actually runs
    # scripts/ml/train_solar_model.py against real plant data.
    ml_performance_ratio = ml_solar_predictor.predict_performance_ratio_pct(avg_temp, avg_daily_irradiance)
    ml_expected_output = None
    if ml_performance_ratio is not None:
        ml_expected_output = round((annual_irradiance / 1.0) * (ml_performance_ratio / 100), 1)

    record = models.SolarPotential(
        site_id=site.id,
        annual_irradiance_kwh_m2=annual_irradiance,
        peak_sun_hours=peak_sun_hours,
        panel_efficiency_pct=panel_efficiency,
        shading_loss_pct=shading_loss,
        performance_ratio_pct=performance_ratio,
        expected_energy_output_mwh_yr=expected_output_mwh_per_mwp,
        capacity_factor_pct=capacity_factor,
        ml_performance_ratio_pct=ml_performance_ratio,
        ml_expected_energy_output_mwh_yr=ml_expected_output,
        ml_model_version=ml_solar_predictor.model_version(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
