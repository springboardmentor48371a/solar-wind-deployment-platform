import os
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from typing import Dict, Any

MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
SOLAR_MODEL_PATH = os.path.join(MODEL_DIR, "solar_model.pkl")
WIND_MODEL_PATH = os.path.join(MODEL_DIR, "wind_model.pkl")

class RenewablePredictor:
    def __init__(self):
        self.solar_model = None
        self.wind_model = None
        self._initialize_models()

    def _initialize_models(self):
        """Loads models if they exist, otherwise trains them on synthetic data."""
        if os.path.exists(SOLAR_MODEL_PATH) and os.path.exists(WIND_MODEL_PATH):
            try:
                with open(SOLAR_MODEL_PATH, "rb") as f:
                    self.solar_model = pickle.load(f)
                with open(WIND_MODEL_PATH, "rb") as f:
                    self.wind_model = pickle.load(f)
                print("ML models loaded successfully from disk.")
                return
            except Exception as e:
                print(f"Error loading models: {e}. Retraining...")
        
        self.train_and_save_models()

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

        # Format feature vectors
        solar_features = np.array([[lat, lon, elevation, cloud_cover, temp, rainfall]])
        wind_features = np.array([[lat, lon, elevation, slope, humidity, rainfall]])

        # Run predictions
        predicted_solar_irr = float(self.solar_model.predict(solar_features)[0])
        predicted_wind_spd = float(self.wind_model.predict(wind_features)[0])

        # Calculations:
        # 1. Solar energy output forecast (kWh per kWp installed per year)
        # Solar yield: Irradiance * 365 * system efficiency (typically 75% or 0.75)
        # Expected generation in MWh for a typical 1 MW plant
        solar_capacity_factor = (predicted_solar_irr * 0.75) / 24.0 # Capacity factor estimate
        expected_solar_mwh = predicted_solar_irr * 365.0 * 0.75 * 1.0 # per MWp installed per year

        # 2. Wind energy output forecast
        # Wind capacity factor calculated based on power curve approximation:
        # e.g., CF = (wind_speed ** 3) / (12 ** 3) * 100 for wind_speed <= 12, max out around 45%
        wind_capacity_factor = min(48.0, max(5.0, (predicted_wind_spd ** 2.2) / (9.0 ** 2.2) * 35.0))
        expected_wind_mwh = (wind_capacity_factor / 100.0) * 8760.0 * 1.0 # per MW installed per year

        return {
            "solar_irradiance": round(predicted_solar_irr, 2),
            "wind_speed": round(predicted_wind_spd, 2),
            "solar_capacity_factor": round(solar_capacity_factor, 3),
            "wind_capacity_factor": round(wind_capacity_factor / 100.0, 3), # as a ratio, e.g. 0.28
            "expected_solar_energy": round(expected_solar_mwh, 2),
            "expected_wind_energy": round(expected_wind_mwh, 2),
            "is_synthetic": True # Clearly label as synthetic/demo data
        }

# Singleton instance
predictor = RenewablePredictor()
