"""Solar Potential Prediction Engine (Module 5).

Uses standard PV-yield heuristics (peak sun hours * derate factors) rather
than a black-box trained model, so results are transparent and explainable.
Swap in a trained XGBoost/Random Forest regressor (see /Prediction Models in
the tech-stack) by replacing `predict_solar` with a `model.predict(...)` call
-- the surrounding API/DB layers don't need to change.
"""


def predict_solar(env: dict, land_area_hectares: float = 5.0) -> dict:
    irradiance = env["solar_irradiance_kwh_m2_day"]
    cloud_cover = env["cloud_cover_pct"]
    slope = env["land_slope_pct"]
    temp = env["temperature_avg_c"]

    peak_sun_hours = round(irradiance, 2)  # kWh/m2/day ~= peak sun hours
    annual_irradiance = round(irradiance * 365, 1)

    # Panel efficiency derates with heat and steep slope
    base_efficiency = 21.0
    temp_derate = max(0, (temp - 25) * 0.04)
    slope_derate = min(slope * 0.05, 3.0)
    panel_efficiency = round(max(base_efficiency - temp_derate - slope_derate, 12.0), 2)

    shading_loss = round(min(cloud_cover * 0.08, 8.0), 2)
    performance_ratio = round(max(0.85 - (cloud_cover / 1000) - (shading_loss / 200), 0.65), 3)

    capacity_factor = round(min((peak_sun_hours / 24) * performance_ratio * 100, 32.0), 2)

    # Assume ~1 MW installed capacity per 2 hectares of usable land (typical solar farm density)
    installed_capacity_mw = round(land_area_hectares / 2.0, 3)
    expected_output_mwh = round(
        installed_capacity_mw * 1000 * (capacity_factor / 100) * 8760 / 1000, 1
    )

    return {
        "annual_irradiance_kwh_m2": annual_irradiance,
        "peak_sun_hours": peak_sun_hours,
        "panel_efficiency_pct": panel_efficiency,
        "performance_ratio": performance_ratio,
        "capacity_factor_pct": capacity_factor,
        "expected_energy_output_mwh_year": expected_output_mwh,
        "shading_loss_pct": shading_loss,
    }
