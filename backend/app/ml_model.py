import os
import pickle
import joblib
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from typing import Dict, Any, Tuple

MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
SOLAR_MODEL_PATH = os.path.join(MODEL_DIR, "solar_model.pkl")
WIND_MODEL_PATH = os.path.join(MODEL_DIR, "wind_model.pkl")
REAL_MODELS_DIR = os.path.join(os.path.dirname(MODEL_DIR), "models")
REAL_SOLAR_MODEL_PATH = os.path.join(REAL_MODELS_DIR, "solar_model_real.joblib")
REAL_WIND_MODEL_PATH = os.path.join(REAL_MODELS_DIR, "wind_model_real.joblib")
REAL_SOLAR_META_PATH = os.path.join(REAL_MODELS_DIR, "solar_model_real_meta.json")
REAL_WIND_META_PATH = os.path.join(REAL_MODELS_DIR, "wind_model_real_meta.json")

class RenewablePredictor:
    def __init__(self):
        self.solar_model = None
        self.wind_model = None
        self.real_solar_model = None
        self.real_wind_model = None
        self.real_solar_meta = None
        self.real_wind_meta = None
        self._initialize_models()

    def _initialize_models(self):
        """Loads models if they exist, otherwise trains them on synthetic data."""
        # Load synthetic fallback models
        if os.path.exists(SOLAR_MODEL_PATH) and os.path.exists(WIND_MODEL_PATH):
            try:
                with open(SOLAR_MODEL_PATH, "rb") as f:
                    self.solar_model = pickle.load(f)
                with open(WIND_MODEL_PATH, "rb") as f:
                    self.wind_model = pickle.load(f)
                print("Synthetic ML models loaded successfully from disk.")
            except Exception as e:
                print(f"Error loading synthetic models: {e}. Retraining...")
                self.train_and_save_models()
        else:
            self.train_and_save_models()
            
        # Load real models and metadata
        try:
            if os.path.exists(REAL_SOLAR_MODEL_PATH) and os.path.exists(REAL_SOLAR_META_PATH):
                self.real_solar_model = joblib.load(REAL_SOLAR_MODEL_PATH)
                with open(REAL_SOLAR_META_PATH, "r") as f:
                    self.real_solar_meta = json.load(f)
                print("Real Solar model loaded successfully.")
                
            if os.path.exists(REAL_WIND_MODEL_PATH) and os.path.exists(REAL_WIND_META_PATH):
                self.real_wind_model = joblib.load(REAL_WIND_MODEL_PATH)
                with open(REAL_WIND_META_PATH, "r") as f:
                    self.real_wind_meta = json.load(f)
                print("Real Wind model loaded successfully.")
        except Exception as e:
            print(f"Error loading real models: {e}")

    def train_and_save_models(self):
        """Generates synthetic data and trains Scikit-learn RandomForest models."""
        print("Training synthetic ML models for Indian Renewable Energy prediction...")
        np.random.seed(42)
        n_samples = 200

        # Generate synthetic input variables for Western/Southern India (Gujarat/Rajasthan/Tamil Nadu)
        # Rajasthan/Gujarat bounds: Lat 20 to 30, Lon 68 to 78
        lats = np.random.uniform(20.0, 30.0, n_samples)
        lons = np.random.uniform(68.0, 78.0, n_samples)
        elevations = np.random.uniform(10.0, 1000.0, n_samples)
        cloud_covers = np.random.uniform(5.0, 45.0, n_samples) # Annual average percentage
        temperatures = np.random.uniform(20.0, 38.0, n_samples)
        humidities = np.random.uniform(15.0, 70.0, n_samples)
        rainfalls = np.random.uniform(100.0, 1200.0, n_samples)
        slopes = np.random.uniform(0.0, 15.0, n_samples)

        # ----------------- Target 1: Solar Potential (kWh/m²/day) -----------------
        # Solar increases with lower latitude (closer to equator), lower cloud cover, and higher elevation
        solar_irradiance = 7.0 - (lats - 20.0)*0.1 - (cloud_covers * 0.04) + (elevations * 0.0005) - (rainfalls * 0.0003)
        solar_irradiance = np.clip(solar_irradiance, 3.5, 7.5) # limit between 3.5 and 7.5 kWh/m2/day
        
        # ----------------- Target 2: Wind Speed (m/s) -----------------
        # Wind speed increases with elevation and terrain slope (hilly/coastal areas), and specific coastal coordinates
        wind_speed = 4.0 + (elevations * 0.003) + (slopes * 0.1) - (lons - 73.0)*0.15
        wind_speed = np.clip(wind_speed, 2.5, 11.0) # limit between 2.5 and 11.0 m/s

        # Train Solar model
        # Inputs: [latitude, longitude, elevation, cloud_cover, temperature, rainfall]
        X_solar = np.column_stack((lats, lons, elevations, cloud_covers, temperatures, rainfalls))
        y_solar = solar_irradiance
        self.solar_model = RandomForestRegressor(n_estimators=50, random_state=42)
        self.solar_model.fit(X_solar, y_solar)

        # Train Wind model
        # Inputs: [latitude, longitude, elevation, slope, humidity, rainfall]
        X_wind = np.column_stack((lats, lons, elevations, slopes, humidities, rainfalls))
        y_wind = wind_speed
        self.wind_model = RandomForestRegressor(n_estimators=50, random_state=42)
        self.wind_model.fit(X_wind, y_wind)

        # Save to disk
        try:
            with open(SOLAR_MODEL_PATH, "wb") as f:
                pickle.dump(self.solar_model, f)
            with open(WIND_MODEL_PATH, "wb") as f:
                pickle.dump(self.wind_model, f)
            print("Synthetic ML models successfully trained and serialized.")
        except Exception as e:
            print(f"Error saving trained models: {e}")

    def predict_resource_potential(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs prediction for Solar Irradiance (kWh/m2/day) and Wind Speed (m/s)
        based on geographical and climate conditions.
        """
        lat = inputs.get("latitude")
        lon = inputs.get("longitude")
        elevation = inputs.get("elevation", 150.0)
        cloud_cover = inputs.get("cloud_cover", 20.0)
        temp = inputs.get("temperature", 28.0)
        humidity = inputs.get("humidity", 40.0)
        rainfall = inputs.get("rainfall", 450.0)
        slope = inputs.get("terrain_slope", 2.0)
        wind_speed_input = inputs.get("wind_speed", 5.0)
        wind_direction_input = inputs.get("wind_direction", 180.0)
        solar_irr_input = inputs.get("solar_irradiance", 5.5)

        solar_model_source = "Synthetic Fallback — Required Feature Unavailable"
        wind_model_source = "Synthetic Fallback"

        # SOLAR PREDICTION
        # The real model requires "AMBIENT_TEMPERATURE", "MODULE_TEMPERATURE", "IRRADIATION"
        # Since MODULE_TEMPERATURE is missing, we must fallback.
        # Run synthetic model for Solar
        solar_features = np.array([[lat, lon, elevation, cloud_cover, temp, rainfall]])
        predicted_solar_irr = float(self.solar_model.predict(solar_features)[0])

        # WIND PREDICTION
        predicted_wind_power_kw = None
        predicted_wind_spd = float(self.wind_model.predict(np.array([[lat, lon, elevation, slope, humidity, rainfall]]))[0])
        
        if self.real_wind_model and self.real_wind_meta:
            expected_features = self.real_wind_meta.get("features", [])
            # Must strictly match: ["Wind speed (m/s)", "Wind direction (\\u00b0)", "Nacelle ambient temperature (\\u00b0C)"]
            if expected_features == ["Wind speed (m/s)", "Wind direction (\u00b0)", "Nacelle ambient temperature (\u00b0C)"]:
                wind_features = np.array([[wind_speed_input, wind_direction_input, temp]])
                predicted_wind_power_kw = float(self.real_wind_model.predict(wind_features)[0])
                # Ensure physical limits
                predicted_wind_power_kw = max(0.0, predicted_wind_power_kw)
                wind_model_source = "Real Historical ML Model \u2014 Kelmarsh SCADA (Not validated for Gujarat/Rajasthan)"

        # Calculations:
        # 1. Solar energy output forecast (kWh per kWp installed per year)
        # Solar yield: Irradiance * 365 * system efficiency (typically 75% or 0.75)
        # Expected generation in MWh for a typical 1 MW plant
        solar_capacity_factor = (predicted_solar_irr * 0.75) / 24.0 # Capacity factor estimate
        expected_solar_mwh = predicted_solar_irr * 365.0 * 0.75 * 1.0 # per MWp installed per year

        # 2. Wind energy output forecast
        if predicted_wind_power_kw is not None:
            # The real Random Forest model predicts active power in kW for a Senvion MM92 (2050 kW rated).
            # Mathematical Conversion:
            # 1. Capacity Factor (CF) = predicted_power_kw / 2050.0 kW
            # 2. Annual Energy (MWh) per 1 MW installed = CF * 8760 hours * 1 MW
            wind_capacity_factor = min(1.0, max(0.0, predicted_wind_power_kw / 2050.0))
            expected_wind_mwh = wind_capacity_factor * 8760.0 * 1.0 # MWh per year per 1 MW installed
        else:
            wind_capacity_factor = min(48.0, max(5.0, (predicted_wind_spd ** 2.2) / (9.0 ** 2.2) * 35.0)) / 100.0
            expected_wind_mwh = wind_capacity_factor * 8760.0 * 1.0 # per MW installed per year

        return {
            "solar_irradiance": round(solar_irr_input if solar_irr_input else predicted_solar_irr, 2),
            "wind_speed": round(wind_speed_input if wind_speed_input else predicted_wind_spd, 2),
            "solar_capacity_factor": round(solar_capacity_factor, 3),
            "wind_capacity_factor": round(wind_capacity_factor, 3), # as a ratio, e.g. 0.28
            "expected_solar_energy": round(expected_solar_mwh, 2),
            "expected_wind_energy": round(expected_wind_mwh, 2),
            "is_synthetic": (wind_model_source == "Synthetic Fallback"), # Deprecated logically, kept for backwards compat
            "is_hybrid_mode": ("Real" in wind_model_source and "Synthetic" in solar_model_source),
            "solar_model_source": solar_model_source,
            "wind_model_source": wind_model_source
        }

# Singleton instance
predictor = RenewablePredictor()
