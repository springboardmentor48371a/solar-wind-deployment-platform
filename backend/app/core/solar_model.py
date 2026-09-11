import numpy as np
from sklearn.ensemble import RandomForestRegressor
from typing import Dict, Any

class SolarPotentialPredictor:
    def __init__(self):
        # Features: [latitude, elevation_m, solar_ghi, avg_temp, cloud_cover_pct, rainfall_mm]
        # Target: [annual_cf_pct, annual_yield_mwh_per_mw]
        X_train = np.array([
            [27.02, 210.0, 5.75, 28.5, 38.0, 120.0],  # Thar Desert / Rajasthan (High Resource)
            [23.73, 145.0, 5.50, 27.2, 42.0, 350.0],  # Kutch / Gujarat
            [28.45, 172.0, 5.15, 25.8, 52.0, 850.0],  # Northern plains / Bareilly
            [15.31, 600.0, 5.65, 26.0, 44.0, 580.0],  # Deccan plateau / Karnataka
            [24.58, 450.0, 5.35, 26.5, 46.0, 420.0],  # Central plains / MP
            [12.97, 920.0, 5.40, 24.0, 48.0, 900.0],  # High elevation South
            [32.20, 1200.0, 4.80, 18.0, 58.0, 1100.0], # Foothills / Sub-Himalayan
            [26.91, 390.0, 5.80, 29.0, 35.0, 150.0]   # Western desert scrub
        ])
        y_train = np.array([
            [24.8, 2172.0],
            [23.5, 2058.0],
            [21.2, 1857.0],
            [24.1, 2111.0],
            [22.8, 1997.0],
            [23.1, 2023.0],
            [19.5, 1708.0],
            [25.2, 2207.0]
        ])
        
        self.model = RandomForestRegressor(n_estimators=40, random_state=42)
        self.model.fit(X_train, y_train)

    def predict_solar_performance(
        self,
        latitude: float,
        elevation_m: float,
        solar_ghi: float,
        avg_temp: float,
        cloud_cover_pct: float,
        rainfall_mm: float,
        land_area_sqkm: float
    ) -> Dict[str, Any]:
        """
        Module 5: Runs ML Regression + PV Temperature Derating Analysis.
        """
        # 1. Feature normalization and baseline ML inference
        features = np.array([[latitude, elevation_m, solar_ghi, avg_temp, cloud_cover_pct, rainfall_mm]])
        predicted_cf, predicted_specific_yield = self.model.predict(features)[0]

        # 2. PV Temperature Derating Physics (Standard Silicon PV Coefficient: -0.40% per °C above 25°C)
        # NOCT (Nominal Operating Cell Temperature) assumed ~ 45°C
        noct = 45.0
        # Peak irradiance estimate in W/m² derived from daily GHI
        g_peak = min(max(solar_ghi * 175.0, 650.0), 1050.0)
        t_cell = avg_temp + ((noct - 20.0) / 800.0) * g_peak
        
        temp_loss_pct = 0.0
        if t_cell > 25.0:
            temp_loss_pct = round((t_cell - 25.0) * 0.40, 2)

        # Apply derating to capacity factor
        derated_cf = round(max(predicted_cf * (1.0 - (temp_loss_pct / 100.0)), 12.0), 2)

        # 3. Array Sizing & Annual Generation Modeling
        # Ground-Mounted Solar Density: ~35 MW per sq km (with inter-row pitch spacing)
        installable_mw = round(land_area_sqkm * 35.0, 1) if land_area_sqkm > 0 else 50.0
        
        # Annual Yield in GWh = MW * 8760 hours * Capacity Factor
        annual_yield_gwh = round((installable_mw * 8760.0 * (derated_cf / 100.0)) / 1000.0, 1)

        # Performance Ratio (PR)
        pr_pct = round(max(82.5 - (temp_loss_pct * 0.6) - (cloud_cover_pct * 0.12), 70.0), 1)

        return {
            "predicted_capacity_factor": derated_cf,
            "annual_yield_gwh": annual_yield_gwh,
            "installable_capacity_mw": installable_mw,
            "t_cell_celsius": round(t_cell, 1),
            "temp_derate_loss_pct": temp_loss_pct,
            "performance_ratio_pct": pr_pct,
            "specific_yield_kwh_kwp": round(predicted_specific_yield * (1.0 - (temp_loss_pct / 100.0)), 1),
            "model_type": "RandomForestRegressor + Thermal Derating (NOCT 45°C)"
        }

solar_predictor = SolarPotentialPredictor()