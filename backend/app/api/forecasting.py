import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.user import SessionLocal, User, UserRole
from app.models.project_site import Site
from app.api.auth import require_roles

router = APIRouter(prefix="/forecasting", tags=["Modules 8 & 9: Forecasting & Optimization"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/run/{site_id}")
def run_energy_forecasting_and_optimization(
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

    # 1. 12-Month Time-Series Generation Modeling (GWh)
    base_solar = site.est_yield_gwh or 145.0
    base_wind = site.annual_wind_yield_gwh or 85.0
    
    # Seasonal variance coefficients (Monsoon vs Summer peaks)
    solar_profile = [round(base_solar / 12 * factor, 2) for factor in [0.85, 0.95, 1.15, 1.25, 1.30, 1.10, 0.75, 0.80, 1.05, 1.10, 0.90, 0.80]]
    wind_profile = [round(base_wind / 12 * factor, 2) for factor in [1.10, 1.05, 0.95, 0.85, 0.90, 1.20, 1.35, 1.30, 1.00, 0.90, 0.95, 1.05]]
    hybrid_profile = [round(s + w, 2) for s, w in zip(solar_profile, wind_profile)]

    # 2. Technology Selection & Financial Modeling (CAPEX & LCOE)
    # Standalone Solar
    capex_solar = site.land_area_sqkm * 1.2 * 0.95  # Million USD approx
    lcoe_solar = 34.50
    
    # Standalone Wind
    capex_wind = site.land_area_sqkm * 1.5 * 1.10
    lcoe_wind = 41.20
    
    # Hybrid Solar-Wind
    capex_hybrid = capex_solar + capex_wind * 0.85
    lcoe_hybrid = 37.10

    # Decision Matrix
    if base_wind > base_solar * 1.2:
        recommended_tech = "Standalone Wind"
        optimal_lcoe = lcoe_wind
        optimal_capex = capex_wind
    elif base_solar > base_wind * 1.3:
        recommended_tech = "Standalone Solar PV"
        optimal_lcoe = lcoe_solar
        optimal_capex = capex_solar
    else:
        recommended_tech = "Hybrid Solar-Wind Microgrid"
        optimal_lcoe = lcoe_hybrid
        optimal_capex = capex_hybrid

    payback_years = round(optimal_capex * 1e6 / (sum(hybrid_profile) * 1e6 * 0.065), 1)

    site.lcoe_usd_mwh = optimal_lcoe
    db.commit()
    db.refresh(site)

    return {
        "message": f"Optimal deployment technology selected: {recommended_tech}",
        "site_id": site.id,
        "forecasting_analytics": {
            "recommended_technology": recommended_tech,
            "lcoe_usd_per_mwh": optimal_lcoe,
            "estimated_capex_million_usd": round(optimal_capex, 2),
            "payback_period_years": payback_years,
            "monthly_generation_gwh": {
                "solar_profile_gwh": solar_profile,
                "wind_profile_gwh": wind_profile,
                "hybrid_combined_gwh": hybrid_profile
            }
        }
    }
