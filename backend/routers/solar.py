from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from ..core.database import get_db
from ..models.site import Site
from ..models.environmental import EnvironmentalData
from ..models.assessment import SolarAssessment
from ..models.user import User
from ..services.solar_engine import solar_engine
from .auth import get_current_user

router = APIRouter(prefix="/solar", tags=["Solar"])

@router.post("/analyze/{site_id}")
def analyze_solar_potential(
    site_id: int,
    capacity_mw: float = 1.0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Analyze solar potential for a specific site"""
    
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
    
    # Predict solar potential
    result = solar_engine.predict_solar_potential(
        lat=site.latitude,
        lon=site.longitude,
        irradiance=env_data.solar_irradiance or 5.0,
        temperature=env_data.temperature or 25.0,
        cloud_cover=env_data.cloud_cover or 30.0,
        elevation=site.elevation or 0,
        slope=env_data.slope or 0,
        ndvi=env_data.ndvi or 0.2,
        capacity_mw=capacity_mw
    )
    
    # Save to database
    assessment = SolarAssessment(
        site_id=site_id,
        peak_sun_hours=result["peak_sun_hours"],
        solar_energy_potential=result["annual_energy_mwh"],
        capacity_factor=result["capacity_factor"],
        performance_ratio=result["performance_ratio"],
        monthly_generation=str(result["monthly_generation"]),
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
        "message": "Solar potential analysis completed successfully"
    }

@router.get("/assessment/{site_id}")
def get_solar_assessment(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get saved solar assessment for a site"""
    
    assessment = db.query(SolarAssessment).filter(SolarAssessment.site_id == site_id).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solar assessment not found for this site"
        )
    
    return {
        "success": True,
        "site_id": site_id,
        "data": {
            "peak_sun_hours": assessment.peak_sun_hours,
            "annual_energy_mwh": assessment.solar_energy_potential,
            "capacity_factor": assessment.capacity_factor,
            "performance_ratio": assessment.performance_ratio,
            "quality_score": assessment.ml_prediction,
            "created_at": assessment.created_at.isoformat()
        }
    }