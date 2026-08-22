from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.session import get_db
from app.schemas.site import SiteCreate, SiteResponse
from app.routes.auth import get_current_user
from app.models.user import User
from app.services import prediction_service

router = APIRouter(prefix="/api/sites", tags=["Site Assessment"])

@router.post("/assess", response_model=SiteResponse, status_code=status.HTTP_201_CREATED)
def assess_site(
    site_in: SiteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Assesses a candidate deployment site coordinates using machine learning predictions
    and the milestone suitability score weighting matrix.
    """
    try:
        # Create assessed site model instance using predictions and formulas
        site = prediction_service.assess_site_suitability(
            user_id=current_user.id,
            name=site_in.name,
            latitude=site_in.latitude,
            longitude=site_in.longitude,
            region=site_in.region,
            land_area=site_in.land_area,
            land_ownership=site_in.land_ownership
        )
        
        # Write to database
        db.add(site)
        db.commit()
        db.refresh(site)
        return site
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assess site: {str(e)}"
        )

@router.get("/", response_model=List[SiteResponse])
def get_user_sites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves all previously assessed sites created by the logged-in user.
    """
    from app.models.site import Site
    sites = db.query(Site).filter(Site.user_id == current_user.id).order_by(Site.created_at.desc()).all()
    return sites
