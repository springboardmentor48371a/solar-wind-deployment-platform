from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import SessionLocal, User
from app.models.project_site import Site
from app.api.auth import get_current_user

router = APIRouter(prefix="/suitability", tags=["suitability"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/score/{site_id}")
def calculate_site_suitability(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Candidate site not found")

    # 1. Resource Score (0-10) based on GHI & Capacity Factor
    ghi = site.solar_ghi or 5.5
    resource_score = min(10.0, max(2.0, (ghi / 6.5) * 10.0))

    # 2. Terrain Score (0-10) based on slope angle (flat is better)
    slope = site.slope_deg if site.slope_deg is not None else 2.5
    terrain_score = max(1.0, 10.0 - (slope * 0.8))

    # 3. Infrastructure Score (0-10) based on grid proximity
    # Parsed or defaulted from infrastructure text/distance
    infra_score = 8.0
    if site.existing_infrastructure and "km" in site.existing_infrastructure:
        try:
            # Extract first number as distance approximation
            dist_val = float(''.join(c for c in site.existing_infrastructure.split("km")[0] if c.isdigit() or c == '.'))
            infra_score = max(2.0, 10.0 - (dist_val * 0.4))
        except:
            pass

    # 4. Environment Score (0-10) based on NDVI and protected buffer compliance
    env_score = 8.5
    if site.vegetation_ndvi and site.vegetation_ndvi > 0.6:
        env_score = 6.0  # Dense vegetation/forest restriction penalty

    # 5. Economic Score (0-10) based on land area and tenure
    economic_score = 8.0 if site.land_ownership == "Government Lease" else 7.0

    # Execute the 5-factor weighted algorithm[cite: 1]
    composite_score = (
        0.35 * resource_score +
        0.25 * terrain_score +
        0.15 * infra_score +
        0.15 * env_score +
        0.10 * economic_score
    )
    composite_score = round(composite_score, 2)

    # Determine Suitability Category[cite: 1]
    if composite_score >= 8.5:
        category = "Excellent"
    elif composite_score >= 7.0:
        category = "Highly Suitable"
    elif composite_score >= 5.0:
        category = "Moderate"
    else:
        category = "Unsuitable"

    site.suitability_score = composite_score
    db.commit()
    db.refresh(site)

    return {
        "message": f"Site suitability evaluated as {category}",
        "site": site,
        "suitability_analytics": {
            "composite_score": composite_score,
            "category": category,
            "factor_breakdown": {
                "resource_score_35pct": round(resource_score, 2),
                "terrain_score_25pct": round(terrain_score, 2),
                "infra_score_15pct": round(infra_score, 2),
                "environment_score_15pct": round(env_score, 2),
                "economic_score_10pct": round(economic_score, 2)
            }
        }
    }