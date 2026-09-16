from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.user import SessionLocal, User, UserRole
from app.models.project_site import Site
from app.api.auth import require_roles
import math

router = APIRouter(prefix="/forecasting", tags=["Forecasting & Optimization"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/run/{site_id}")
@router.post("/optimize/{site_id}")
def run_forecasting_optimization(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([
        UserRole.PLANNER.value,
        UserRole.PROJECT_MANAGER.value,
        UserRole.ADMIN.value,
        UserRole.GIS_ANALYST.value
    ]))
):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Candidate site not found")

    base_yield = site.est_yield_gwh or 1450.0

    # 12-month generation profile
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    monthly_solar = [round((base_yield * 0.5) / 12 * (1 + 0.3 * math.sin(i * math.pi / 6)), 2) for i in range(12)]
    monthly_wind = [round((base_yield * 0.5) / 12 * (1 - 0.2 * math.cos(i * math.pi / 6)), 2) for i in range(12)]
    hybrid_combined = [round(s + w, 2) for s, w in zip(monthly_solar, monthly_wind)]

    # Economics & recommendation
    if site.suitability_score and site.suitability_score >= 7.5:
        recommended_tech = "Hybrid Solar-Wind Farm"
        lcoe = 34.2
        capex = 290.0
        payback = 5.4
    elif site.capacity_factor and site.capacity_factor > 20:
        recommended_tech = " Wind Farm"
        lcoe = 41.0
        capex = 185.0
        payback = 6.8
    else:
        recommended_tech = "Solar Farm "
        lcoe = 36.5
        capex = 145.0
        payback = 6.2

    site.lcoe_usd_mwh = lcoe
    db.commit()
    db.refresh(site)

    return {
        "message": f"Optimization model executed: Recommended {recommended_tech}",
        "site": site,
        "forecasting_analytics": {
            "recommended_technology": recommended_tech,
            "lcoe_usd_per_mwh": lcoe,
            "estimated_capex_million_usd": capex,
            "payback_period_years": payback,
            "monthly_generation_gwh": {
                "months": months,
                "solar_gwh": monthly_solar,
                "wind_gwh": monthly_wind,
                "hybrid_combined_gwh": hybrid_combined
            }
        }
    }