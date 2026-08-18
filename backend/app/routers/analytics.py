import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app import models, schemas, auth, authz
from app.database import get_db
from app.config import settings
from app.warehouse import refresh_warehouse
from app.security import log_action

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=schemas.DashboardSummaryOut)
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Aggregate stats for the Overview screen — mirrors the Portfolio capacity /
    Avg. suitability / Active projects / Data freshness cards in the app.
    """
    if current_user.role in authz.READ_ALL_ROLES:
        projects = db.query(models.Project).all()
    else:
        projects = (
            db.query(models.Project).filter(models.Project.owner_id == current_user.id).all()
        )
    project_ids = [p.id for p in projects]

    sites = (
        db.query(models.Site).filter(models.Site.project_id.in_(project_ids)).all()
        if project_ids
        else []
    )

    scores = []
    sites_by_category = {
        "Excellent": 0,
        "Highly Suitable": 0,
        "Moderately Suitable": 0,
        "Low Suitability": 0,
        "Unsuitable": 0,
    }
    for site in sites:
        latest = (
            db.query(models.SuitabilityScore)
            .filter(models.SuitabilityScore.site_id == site.id)
            .order_by(models.SuitabilityScore.computed_at.desc())
            .first()
        )
        if latest:
            scores.append(latest.overall_score)
            sites_by_category[latest.category] = sites_by_category.get(latest.category, 0) + 1

    avg_score = round(sum(scores) / len(scores), 1) if scores else None

    # Data freshness: % of sites with a weather reading in the last 3 days
    fresh_cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=3)
    fresh_count = 0
    for site in sites:
        latest_reading = (
            db.query(models.WeatherReading)
            .filter(models.WeatherReading.site_id == site.id)
            .order_by(models.WeatherReading.reading_date.desc())
            .first()
        )
        if latest_reading and latest_reading.reading_date >= fresh_cutoff:
            fresh_count += 1
    freshness_pct = round((fresh_count / len(sites)) * 100, 1) if sites else 100.0

    return {
        "portfolio_capacity_note": "Capacity estimation requires the Energy Forecasting Engine (AI phase, next week).",
        "active_projects": len(projects),
        "total_sites": len(sites),
        "average_suitability": avg_score,
        "sites_by_category": sites_by_category,
        "data_freshness_pct": freshness_pct,
    }


@router.get("/warehouse", response_model=list[schemas.SiteRollupOut])
def list_warehouse_rollup(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Data Warehouse read path — the denormalized SiteRollup table, built
    for whole-portfolio BI queries (see app/warehouse.py) instead of
    joining six operational tables per dashboard load. Same visibility
    rule as the rest of the app: full portfolio for oversight roles,
    own projects only for a Planner.
    """
    if current_user.role in authz.READ_ALL_ROLES:
        rows = db.query(models.SiteRollup).all()
    else:
        owned_project_ids = [
            p.id for p in db.query(models.Project).filter(models.Project.owner_id == current_user.id)
        ]
        rows = (
            db.query(models.SiteRollup)
            .filter(models.SiteRollup.project_id.in_(owned_project_ids))
            .all()
            if owned_project_ids
            else []
        )
    return rows


@router.post("/warehouse/refresh", response_model=schemas.WarehouseRefreshOut)
def trigger_warehouse_refresh(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Recomputes the warehouse rollup for every site (Admin/PM — portfolio-wide operation)."""
    if current_user.role not in authz.FULL_ACCESS_ROLES:
        raise HTTPException(status_code=403, detail="Only Administrators and Project Managers can refresh the warehouse")
    count = refresh_warehouse(db)
    log_action(db, current_user.id, "refresh_warehouse", f"rows:{count}", request.client.host)
    return {
        "rows_refreshed": count,
        "refreshed_at": datetime.datetime.utcnow(),
        "parquet_export_enabled": bool(settings.warehouse_export_dir),
    }
