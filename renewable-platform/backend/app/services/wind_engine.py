"""Wind Potential Prediction Engine (Module 6).

Uses standard wind-power-density physics (P = 0.5 * air_density * v^3) with
a Weibull-style capacity factor approximation. Swap in a trained model
(LightGBM/TensorFlow per the tech stack) by replacing `predict_wind`.
"""
AIR_DENSITY = 1.225  # kg/m3 at sea level


def predict_wind(env: dict, land_area_hectares: float = 5.0) -> dict:
    v = env["wind_speed_avg_ms"]

    power_density = round(0.5 * AIR_DENSITY * (v ** 3), 1)  # W/m2
    turbulence_intensity = round(max(6.0, 20 - v), 2)  # rough heuristic: higher speed -> steadier flow

    if v < 3:
        suitability = "Unsuitable"
        capacity_factor = round(min(v * 2, 8), 2)
    elif v < 5.5:
        suitability = "Marginal"
        capacity_factor = round(15 + (v - 3) * 5, 2)
    elif v < 7.5:
        suitability = "Suitable"
        capacity_factor = round(28 + (v - 5.5) * 6, 2)
    else:
        suitability = "Highly Suitable"
        capacity_factor = round(min(40 + (v - 7.5) * 4, 55), 2)

    # Assume 1 turbine (~2.5 MW) per 8 hectares (typical spacing incl. setbacks)
    installed_capacity_mw = round((land_area_hectares / 8.0) * 2.5, 3)
    expected_annual_energy = round(
        installed_capacity_mw * 1000 * (capacity_factor / 100) * 8760 / 1000, 1
    )

    return {
        "avg_wind_speed_ms": v,
        "wind_power_density_w_m2": power_density,
        "turbulence_intensity_pct": turbulence_intensity,
        "turbine_suitability": suitability,
        "capacity_factor_pct": capacity_factor,
        "expected_annual_energy_mwh": expected_annual_energy,
    }
