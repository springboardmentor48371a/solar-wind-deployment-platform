from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from ..core.database import get_db
from ..models.site import Site
from ..models.assessment import SolarAssessment, WindAssessment
from ..models.suitability import SuitabilityScore
from ..models.user import User
from ..services.suitability_engine import suitability_engine
from .auth import get_current_user

router = APIRouter(prefix="/suitability", tags=["Suitability"])

@router.post("/analyze/{site_id}")
def analyze_suitability(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Analyze overall site suitability"""
    
    # Get site
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found"
        )
    
    # Get solar and wind assessments
    solar = db.query(SolarAssessment).filter(SolarAssessment.site_id == site_id).first()
    wind = db.query(WindAssessment).filter(WindAssessment.site_id == site_id).first()
    
    if not solar or not wind:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solar and/or wind assessments not found. Please run analyses first."
        )
    
    # Calculate scores
    solar_score = solar.ml_prediction or 50.0
    wind_score = wind.ml_prediction or 50.0
    
    # Geographic score (based on elevation, slope, etc.)
    geographic_score = 70.0  # Default, can be enhanced with GIS data
    if site.elevation and site.elevation > 500:
        geographic_score -= 10
    elif site.elevation and site.elevation > 1000:
        geographic_score -= 20
    
    # Infrastructure score (based on existing infrastructure)
    infrastructure_score = 60.0
    if site.existing_infrastructure:
        if "road" in site.existing_infrastructure.lower():
            infrastructure_score += 10
        if "power" in site.existing_infrastructure.lower():
            infrastructure_score += 15
        if "transmission" in site.existing_infrastructure.lower():
            infrastructure_score += 10
    
    # Environmental score
    environmental_score = 75.0
    
    # Economic score (based on land area)
    economic_score = 65.0
    if site.land_area and site.land_area > 50:
        economic_score += 10
    if site.land_area and site.land_area > 100:
        economic_score += 10
    
    # Calculate overall
    result = suitability_engine.calculate_suitability_score(
        solar_score=solar_score,
        wind_score=wind_score,
        geographic_score=geographic_score,
        infrastructure_score=infrastructure_score,
        environmental_score=environmental_score,
        economic_score=economic_score
    )
    
    # Save to database
    suitability = SuitabilityScore(
        site_id=site_id,
        renewable_resource_score=(solar_score + wind_score) / 2,
        geographic_suitability_score=geographic_score,
        infrastructure_accessibility_score=infrastructure_score,
        environmental_impact_score=environmental_score,
        economic_feasibility_score=economic_score,
        overall_score=result["overall_score"],
        category=result["category"],
        recommendations=" | ".join(result["recommendations"])
    )
    
    db.add(suitability)
    db.commit()
    db.refresh(suitability)
    
    return {
        "success": True,
        "site_id": site_id,
        "site_name": site.site_name,
        "analysis": result,
        "message": "Suitability analysis completed successfully"
    }

@router.get("/score/{site_id}")
def get_suitability_score(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get saved suitability score for a site"""
    
    score = db.query(SuitabilityScore).filter(SuitabilityScore.site_id == site_id).first()
    if not score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Suitability score not found for this site"
        )
    
    return {
        "success": True,
        "site_id": site_id,
        "data": {
            "overall_score": score.overall_score,
            "category": score.category,
            "scores": {
                "renewable_resource": score.renewable_resource_score,
                "geographic_suitability": score.geographic_suitability_score,
                "infrastructure": score.infrastructure_accessibility_score,
                "environmental": score.environmental_impact_score,
                "economic": score.economic_feasibility_score
            },
            "recommendations": score.recommendations.split(" | ") if score.recommendations else [],
            "created_at": score.created_at.isoformat()
        }
    }