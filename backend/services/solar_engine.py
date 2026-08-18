import numpy as np
import pandas as pd
from typing import Dict, Any, List
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import joblib
import os

class SolarPredictionEngine:
    def __init__(self):
        self.model = None
        self.model_path = "models/solar_model.pkl"
        self.load_model()
    
    def load_model(self):
        """Load trained model if exists"""
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                print("✅ Solar model loaded successfully")
            except:
                print("⚠️ Failed to load solar model, using fallback")
                self.model = None
        else:
            print("ℹ️ No solar model found, using fallback calculations")
            self.model = None
    
    def calculate_peak_sun_hours(self, irradiance: float) -> float:
        """Calculate Peak Sun Hours from daily solar irradiance"""
        return irradiance  # kWh/m²/day
    
    def calculate_solar_energy(
        self,
        capacity_mw: float,
        irradiance: float,
        performance_ratio: float = 0.80,
        days: int = 365
    ) -> Dict[str, Any]:
        """Calculate solar energy generation potential"""
        peak_sun_hours = self.calculate_peak_sun_hours(irradiance)
        
        # Annual energy (MWh)
        annual_energy = capacity_mw * peak_sun_hours * days * performance_ratio
        
        # Capacity factor
        capacity_factor = (annual_energy / (capacity_mw * 8760)) * 100
        
        # Monthly generation
        monthly_generation = []
        for month in range(1, 13):
            seasonal_factor = 0.7 + 0.6 * np.sin((month - 3) * np.pi / 6)
            monthly_energy = (annual_energy / 12) * seasonal_factor
            monthly_generation.append({
                "month": month,
                "energy_mwh": round(monthly_energy, 2)
            })
        
        return {
            "annual_energy_mwh": round(annual_energy, 2),
            "capacity_factor": round(capacity_factor, 2),
            "performance_ratio": performance_ratio,
            "peak_sun_hours": round(peak_sun_hours, 2),
            "monthly_generation": monthly_generation
        }
    
    def predict_solar_potential(
        self,
        lat: float,
        lon: float,
        irradiance: float,
        temperature: float,
        cloud_cover: float,
        elevation: float,
        slope: float,
        ndvi: float,
        capacity_mw: float = 1.0
    ) -> Dict[str, Any]:
        """Predict solar potential using ML model"""
        
        # Calculate basic metrics
        energy = self.calculate_solar_energy(capacity_mw, irradiance)
        
        # Quality score (0-100)
        quality_score = 0
        quality_score += min(irradiance / 6.0, 1.0) * 0.4
        quality_score += min(1 / (1 + abs(temperature - 25) / 20), 1.0) * 0.2
        quality_score += min(1 / (1 + cloud_cover / 50), 1.0) * 0.2
        quality_score += min(1 / (1 + slope / 30), 1.0) * 0.1
        quality_score += min(1 / (1 + ndvi * 2), 1.0) * 0.1
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
            "annual_energy_mwh": energy["annual_energy_mwh"],
            "capacity_factor": energy["capacity_factor"],
            "peak_sun_hours": energy["peak_sun_hours"],
            "performance_ratio": energy["performance_ratio"],
            "quality_score": round(quality_score, 2),
            "suitability": suitability,
            "monthly_generation": energy["monthly_generation"],
            "recommendations": self.get_recommendations(quality_score, irradiance, temperature)
        }
    
    def get_recommendations(self, quality_score: float, irradiance: float, temperature: float) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        if quality_score < 40:
            recommendations.append("⚠️ Site has low solar potential. Consider other locations.")
        
        if irradiance < 4.0:
            recommendations.append("💡 Low solar irradiance. Consider wind or hybrid options.")
        
        if temperature > 40:
            recommendations.append("🌡️ High temperature may reduce panel efficiency.")
        
        if temperature < 10:
            recommendations.append("❄️ Low temperature may affect battery performance.")
        
        if quality_score >= 80:
            recommendations.append("✅ Excellent site for solar deployment.")
        elif quality_score >= 60:
            recommendations.append("👍 Good site for solar deployment with some considerations.")
        
        if not recommendations:
            recommendations.append("Site shows good potential for solar energy.")
        
        return recommendations
    
    def train_model(self, data: pd.DataFrame):
        """Train ML model for solar prediction"""
        # Features
        X = data[['irradiance', 'temperature', 'cloud_cover', 'elevation', 'slope', 'ndvi']].values
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
            "accuracy_score": round(score * 100, 2),
            "features": list(X.columns)
        }

# Singleton instance
solar_engine = SolarPredictionEngine()