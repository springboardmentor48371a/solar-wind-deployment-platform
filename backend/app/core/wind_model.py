import math
from typing import Dict, Any

class WindPotentialPredictor:
    def predict_wind_performance(
        self,
        latitude: float,
        longitude: float,
        elevation_m: float,
        wind_speed_50m: float,
        land_area_sqkm: float
    ) -> Dict[str, Any]:
        """
        Module 6: Wind Potential Prediction Engine.
        - Extrapolates 50m wind speed to 100m hub height via Hellman Power Law (alpha = 0.143).
        - Calculates Wind Power Density (W/m²).
        - Estimates annual wind generation (GWh) for utility-scale wind farms.
        """
        # 1. Hub-height wind speed extrapolation (50m to 100m)
        alpha = 0.143  # Standard open terrain power-law exponent
        wind_speed_100m = wind_speed_50m * ((100.0 / 50.0) ** alpha)

        # 2. Air density correction based on elevation (ISA model)
        # Standard sea-level air density = 1.225 kg/m³
        air_density = 1.225 * math.exp(-elevation_m / 8500.0)

        # 3. Wind Power Density (WPD) = 0.5 * rho * v^3 (W/m²)
        wpd = 0.5 * air_density * (wind_speed_100m ** 3)

        # 4. Wind Turbine Capacity Factor Estimation based on WPD and IEC Class standards
        # Assuming modern 3.4MW utility wind turbines with 130m rotor diameters
        if wpd >= 500:
            capacity_factor = 42.5
        elif wpd >= 350:
            capacity_factor = 34.0
        elif wpd >= 200:
            capacity_factor = 26.5
        else:
            capacity_factor = 18.0

        # 5. Installable Wind Capacity & Annual Yield Generation
        # Standard wind farm spacing density: ~7 MW per sq km
        installable_mw = round(land_area_sqkm * 7.0, 1) if land_area_sqkm > 0 else 35.0
        
        # Annual Yield (GWh) = MW * 8760 hours * Capacity Factor / 1000
        annual_yield_gwh = round((installable_mw * 8760.0 * (capacity_factor / 100.0)) / 1000.0, 1)

        # Turbulence Intensity estimate based on latitude/terrain heuristic
        turbulence_intensity_pct = round(10.5 + abs(latitude % 5.0) * 0.4, 1)

        return {
            "wind_speed_50m": round(wind_speed_50m, 2),
            "wind_speed_100m": round(wind_speed_100m, 2),
            "air_density_kg_m3": round(air_density, 3),
            "wind_power_density_w_m2": round(wpd, 1),
            "predicted_capacity_factor": capacity_factor,
            "installable_capacity_mw": installable_mw,
            "annual_yield_gwh": annual_yield_gwh,
            "turbulence_intensity_pct": turbulence_intensity_pct,
            "turbine_class": "IEC Class II/III (3.4 MW Utility Scale)"
        }

wind_predictor = WindPotentialPredictor()