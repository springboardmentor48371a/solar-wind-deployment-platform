import numpy as np
import pandas as pd
from typing import Dict, Any, List
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import joblib
import os

class WindPredictionEngine:
    def __init__(self):
        self.model = None
        self.model_path = "models/wind_model.pkl"
        self.load_model()
    
    def load_model(self):
        """Load trained model if exists"""
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                print("✅ Wind model loaded successfully")
            except:
                print("⚠️ Failed to load wind model, using fallback")
                self.model = None
        else:
            print("ℹ️ No wind model found, using fallback calculations")
            self.model = None
    
    def calculate_wind_power_density(self, wind_speed: float, air_density: float = 1.225) -> float:
        """Calculate wind power density (W/m²)"""
        return 0.5 * air_density * (wind_speed ** 3)
    
    def calculate_wind_energy(
        self,
        wind_speed: float,
        rotor_diameter: float = 100,
        capacity_mw: float = 2.0,
        efficiency: float = 0.45
    ) -> Dict[str, Any]:
        """Calculate wind energy generation potential"""
        swept_area = np.pi * (rotor_diameter / 2) ** 2
        power_density = self.calculate_wind_power_density(wind_speed)
        
        # Theoretical power (MW)
        theoretical_power = (power_density * swept_area) / 1_000_000
        
        # Annual energy with efficiency factor
        annual_energy = theoretical_power * 8760 * efficiency
        
        # Capacity factor
        capacity_factor = (annual_energy / (capacity_mw * 8760)) * 100
        
        # Monthly generation with seasonal variation
        monthly_generation = []
        for month in range(1, 13):
            seasonal_factor = 0.6 + 0.6 * np.sin((month - 1) * np.pi / 6)
            monthly_energy = (annual_energy / 12) * seasonal_factor
            monthly_generation.append({
                "month": month,
                "energy_mwh": round(monthly_energy, 2)
            })
        
        return {
            "annual_energy_mwh": round(annual_energy, 2),
            "capacity_factor": round(capacity_factor, 2),
            "power_density": round(power_density, 2),
            "theoretical_power_mw": round(theoretical_power, 3),
            "monthly_generation": monthly_generation,
            "efficiency": efficiency
        }
    
    def predict_wind_potential(
        self,
        lat: float,
        lon: float,
        wind_speed: float,
        temperature: float,
        elevation: float,
        terrain: str = "flat",
        capacity_mw: float = 2.0
    ) -> Dict[str, Any]:
        """Predict wind potential"""
        
        # Calculate energy
        energy = self.calculate_wind_energy(wind_speed, capacity_mw=capacity_mw)
        
        # Quality score (0-100)
        quality_score = 0
        quality_score += min(wind_speed / 10.0, 1.0) * 0.5
        
        # Terrain bonus
        terrain_bonus = {
            "flat": 0.2,
            "hilly": 0.15,
            "coastal": 0.25,
            "mountain": 0.1
        }
        quality_score += terrain_bonus.get(terrain, 0.2)
        
        # Temperature impact
        quality_score += min(1 / (1 + abs(temperature - 15) / 25), 1.0) * 0.2
        
        # Elevation impact
        quality_score += min(1 / (1 + elevation / 1000), 1.0) * 0.1
        
        quality_score *= 100
        
        # Determine suitability
        if quality_score >= 80:
            suitability = "Excellent"
        elif quality_score >= 60:
            suitability = "Good"
        elif quality_score >= 40:
            suitability = "Moderate"
        else:
            suitability = "Poor"
        
        return {
            "lat": lat,
            "lon": lon,
            "capacity_mw": capacity_mw,
            "avg_wind_speed": round(wind_speed, 2),
            "power_density": energy["power_density"],
            "annual_energy_mwh": energy["annual_energy_mwh"],
            "capacity_factor": energy["capacity_factor"],
            "theoretical_power_mw": energy["theoretical_power_mw"],
            "quality_score": round(quality_score, 2),
            "suitability": suitability,
            "monthly_generation": energy["monthly_generation"],
            "recommendations": self.get_recommendations(quality_score, wind_speed, terrain)
        }
    
    def get_recommendations(self, quality_score: float, wind_speed: float, terrain: str) -> List[str]:
        """Generate recommendations"""
        recommendations = []
        
        if quality_score < 40:
            recommendations.append("⚠️ Site has low wind potential. Consider other locations.")
        
        if wind_speed < 4.0:
            recommendations.append("💡 Low wind speed. Consider solar or hybrid options.")
        
        if wind_speed > 8.0:
            recommendations.append("💨 High wind speed. Consider turbine load management.")
        
        if terrain == "hilly" and quality_score < 50:
            recommendations.append("🏔️ Hilly terrain may increase turbulence. Consider site-specific assessment.")
        
        if terrain == "coastal":
            recommendations.append("🌊 Coastal site. Consider corrosion-resistant turbines.")
        
        if quality_score >= 80:
            recommendations.append("✅ Excellent site for wind deployment.")
        elif quality_score >= 60:
            recommendations.append("👍 Good site for wind deployment with some considerations.")
        
        if not recommendations:
            recommendations.append("Site shows good potential for wind energy.")
        
        return recommendations
    
    def train_model(self, data: pd.DataFrame):
        """Train ML model for wind prediction"""
        # Features
        X = data[['wind_speed', 'temperature', 'elevation', 'terrain_factor']].values
        y = data['energy_output'].values
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Train model
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.model.fit(X_train, y_train)
        
        # Save model
        os.makedirs("models", exist_ok=True)
        joblib.dump(self.model, self.model_path)
        
        # Calculate accuracy
        score = self.model.score(X_test, y_test)
        
        return {
            "message": "Model trained successfully",
            "accuracy_score": round(score * 100, 2)
        }

# Singleton instance
wind_engine = WindPredictionEngine()