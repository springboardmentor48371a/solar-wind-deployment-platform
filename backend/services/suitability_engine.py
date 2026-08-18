from typing import Dict, Any, List

class SuitabilityEngine:
    def __init__(self):
        self.weights = {
            "renewable_resource": 0.35,
            "geographic_suitability": 0.25,
            "infrastructure": 0.15,
            "environmental": 0.15,
            "economic": 0.10
        }
    
    def calculate_suitability_score(
        self,
        solar_score: float,
        wind_score: float,
        geographic_score: float,
        infrastructure_score: float,
        environmental_score: float,
        economic_score: float
    ) -> Dict[str, Any]:
        """Calculate overall suitability score"""
        
        # Weighted average
        overall_score = (
            solar_score * 0.35 +  # Renewable resource
            wind_score * 0.35 +   # Renewable resource
            geographic_score * 0.25 +
            infrastructure_score * 0.15 +
            environmental_score * 0.15 +
            economic_score * 0.10
        )
        
        # Normalize to 0-100
        overall_score = min(max(overall_score, 0), 100)
        
        # Determine category
        if overall_score >= 90:
            category = "Excellent"
            color = "#4CAF50"
        elif overall_score >= 80:
            category = "Highly Suitable"
            color = "#8BC34A"
        elif overall_score >= 65:
            category = "Moderately Suitable"
            color = "#FFC107"
        elif overall_score >= 40:
            category = "Low Suitability"
            color = "#FF9800"
        else:
            category = "Unsuitable"
            color = "#f44336"
        
        return {
            "overall_score": round(overall_score, 2),
            "category": category,
            "color": color,
            "scores": {
                "renewable_resource": round((solar_score + wind_score) / 2, 2),
                "geographic_suitability": round(geographic_score, 2),
                "infrastructure": round(infrastructure_score, 2),
                "environmental": round(environmental_score, 2),
                "economic": round(economic_score, 2)
            },
            "recommendations": self.generate_recommendations(overall_score, solar_score, wind_score)
        }
    
    def generate_recommendations(
        self,
        overall_score: float,
        solar_score: float,
        wind_score: float
    ) -> List[str]:
        """Generate recommendations"""
        recommendations = []
        
        if overall_score < 40:
            recommendations.append("❌ Site has low overall suitability. Consider alternative locations.")
        
        if solar_score < 40:
            recommendations.append("☀️ Low solar potential. Consider focusing on wind or hybrid options.")
        
        if wind_score < 40:
            recommendations.append("💨 Low wind potential. Consider focusing on solar or hybrid options.")
        
        if solar_score > 70 and wind_score > 70:
            recommendations.append("⚡ Excellent potential for hybrid solar-wind deployment.")
        
        if solar_score > wind_score + 20:
            recommendations.append("☀️ Solar significantly outperforms wind. Prioritize solar deployment.")
        
        if wind_score > solar_score + 20:
            recommendations.append("💨 Wind significantly outperforms solar. Prioritize wind deployment.")
        
        if overall_score >= 80:
            recommendations.append("✅ This site is highly recommended for deployment.")
        
        if not recommendations:
            recommendations.append("Site shows balanced potential for renewable energy deployment.")
        
        return recommendations

# Singleton instance
suitability_engine = SuitabilityEngine()