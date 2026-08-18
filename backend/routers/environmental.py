from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from ..core.database import get_db
from ..models.site import Site
from ..models.environmental import EnvironmentalData
from ..models.user import User
from ..services.nasa_power import fetch_environmental_data
from .auth import get_current_user

router = APIRouter(prefix="/environmental", tags=["Environmental"])

@router.get("/fetch/{site_id}")
def fetch_environmental_data_for_site(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Fetch environmental data for a specific site"""
    
    # Get site
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found"
        )
    
    # Fetch data from NASA POWER
    data = fetch_environmental_data(site.latitude, site.longitude)
    
    if not data["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch environmental data: {data.get('error', 'Unknown error')}"
        )
    
    # Save to database
    env_data = EnvironmentalData(
        site_id=site_id,
        solar_irradiance=data["data"]["solar_irradiance"],
        temperature=data["data"]["temperature"],
        rainfall=data["data"]["rainfall"],
        wind_speed=data["data"]["wind_speed"],
        cloud_cover=data["data"]["cloud_cover"],
        data_source="NASA POWER",
        fetch_date=data["data"]["fetch_date"]
    )
    
    db.add(env_data)
    db.commit()
    db.refresh(env_data)
    
    return {
        "success": True,
        "site_id": site_id,
        "site_name": site.site_name,
        "latitude": site.latitude,
        "longitude": site.longitude,
        "environmental_data": data["data"],
        "message": "Environmental data fetched and saved successfully"
    }

@router.get("/{site_id}")
def get_environmental_data(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get saved environmental data for a site"""
    
    env_data = db.query(EnvironmentalData).filter(EnvironmentalData.site_id == site_id).first()
    if not env_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Environmental data not found for this site"
        )
    
    return {
        "success": True,
        "site_id": site_id,
        "data": {
            "solar_irradiance": env_data.solar_irradiance,
            "temperature": env_data.temperature,
            "rainfall": env_data.rainfall,
            "wind_speed": env_data.wind_speed,
            "wind_direction": env_data.wind_direction,
            "cloud_cover": env_data.cloud_cover,
            "slope": env_data.slope,
            "ndvi": env_data.ndvi,
            "land_cover": env_data.land_cover,
            "data_source": env_data.data_source,
            "fetch_date": env_data.fetch_date.isoformat()
        }
    }