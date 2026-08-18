from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from ..core.database import get_db
from ..models.site import Site
from ..models.environmental import EnvironmentalData
from ..models.assessment import WindAssessment
from ..models.user import User
from ..services.wind_engine import wind_engine
from .auth import get_current_user

router = APIRouter(prefix="/wind", tags=["Wind"])

@router.post("/analyze/{site_id}")
def analyze_wind_potential(
    site_id: int,
    capacity_mw: float = 2.0,
    terrain: str = "flat",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Analyze wind potential for a specific site"""
    
    # Get site
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found"
        )
    
    # Get environmental data
    env_data = db.query(EnvironmentalData).filter(EnvironmentalData.site_id == site_id).first()
    if not env_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Environmental data not found. Please fetch environmental data first."
        )
    
    # Predict wind potential
    result = wind_engine.predict_wind_potential(
        lat=site.latitude,
        lon=site.longitude,
        wind_speed=env_data.wind_speed or 5.0,
        temperature=env_data.temperature or 25.0,
        elevation=site.elevation or 0,
        terrain=terrain,
        capacity_mw=capacity_mw
    )
    
    # Save to database
    assessment = WindAssessment(
        site_id=site_id,
        avg_wind_speed=result["avg_wind_speed"],
        wind_power_density=result["power_density"],
        capacity_factor=result["capacity_factor"],
        annual_energy_production=result["annual_energy_mwh"],
        turbine_suitability=str(result["recommendations"]),
        ml_prediction=result["quality_score"],
        prediction_confidence=0.85
    )
    
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    
    return {
        "success": True,
        "site_id": site_id,
        "site_name": site.site_name,
        "analysis": result,
        "message": "Wind potential analysis completed successfully"
    }

@router.get("/assessment/{site_id}")
def get_wind_assessment(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get saved wind assessment for a site"""
    
    assessment = db.query(WindAssessment).filter(WindAssessment.site_id == site_id).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wind assessment not found for this site"
        )
    
    return {
        "success": True,
        "site_id": site_id,
        "data": {
            "avg_wind_speed": assessment.avg_wind_speed,
            "power_density": assessment.wind_power_density,
            "annual_energy_mwh": assessment.annual_energy_production,
            "capacity_factor": assessment.capacity_factor,
            "quality_score": assessment.ml_prediction,
            "created_at": assessment.created_at.isoformat()
        }
    }