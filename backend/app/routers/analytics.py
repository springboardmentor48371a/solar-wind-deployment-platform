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
    site_ids = [s.id for s in sites]

    # Performance optimization: this used to run one SuitabilityScore
    # query and one WeatherReading query PER SITE (a real N+1 pattern —
    # 2 extra queries per site, so 201 total queries for a 100-site
    # portfolio instead of 3). Fetches every relevant row for the whole
    # portfolio in 2 queries total, then does the "latest per site"
    # reduction in Python — portable across Postgres/SQLite without
    # needing a database-specific window-function query.
    if site_ids:
        all_scores = (
            db.query(models.SuitabilityScore)
            .filter(models.SuitabilityScore.site_id.in_(site_ids))
            .order_by(models.SuitabilityScore.computed_at.desc())
            .all()
        )
    else:
        all_scores = []

    latest_score_by_site = {}
    for score in all_scores:
        if score.site_id not in latest_score_by_site:  # first hit per site_id is the latest, since already ordered desc
            latest_score_by_site[score.site_id] = score

    for latest in latest_score_by_site.values():
        scores.append(latest.overall_score)
        sites_by_category[latest.category] = sites_by_category.get(latest.category, 0) + 1

    avg_score = round(sum(scores) / len(scores), 1) if scores else None

    # Data freshness: % of sites with a weather reading in the last 3 days
    fresh_cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=3)
    if site_ids:
        fresh_site_ids = {
            row[0]
            for row in db.query(models.WeatherReading.site_id)
            .filter(models.WeatherReading.site_id.in_(site_ids), models.WeatherReading.reading_date >= fresh_cutoff)
            .distinct()
            .all()
        }
    else:
        fresh_site_ids = set()
    fresh_count = len(fresh_site_ids)
    freshness_pct = round((fresh_count / len(sites)) * 100, 1) if sites else 100.0

    return {
        "portfolio_capacity_note": "See /projects/{id}/sites/{id}/technology-recommendation for real capacity planning (NREL land-use based), and /analytics/deployment-progress for portfolio-wide status.",
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


@router.get("/deployment-timeline", response_model=list[schemas.DeploymentStatusHistoryOut])
def portfolio_deployment_timeline(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Project Manager Dashboard's "Deployment timelines" sub-item — a
    portfolio-wide feed of recent status changes across every visible
    site, not just one (the per-site version lives at
    /projects/{id}/sites/{id}/deployment-history). Same visibility rule
    as the rest of analytics.py: full portfolio for oversight roles,
    own projects only for a Planner.
    """
    query = db.query(models.DeploymentStatusHistory).join(models.Site)
    if current_user.role not in authz.READ_ALL_ROLES:
        owned_project_ids = [
            p.id for p in db.query(models.Project).filter(models.Project.owner_id == current_user.id)
        ]
        query = query.filter(models.Site.project_id.in_(owned_project_ids))
    return (
        query.order_by(models.DeploymentStatusHistory.changed_at.desc())
        .limit(limit)
        .all()
    )


@router.get("/deployment-progress")
def portfolio_deployment_progress(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Project Manager Dashboard's "Project progress" sub-item — a count of
    visible sites in each deployment lifecycle stage, for an at-a-glance
    portfolio progress view.
    """
    if current_user.role in authz.READ_ALL_ROLES:
        sites = db.query(models.Site).all()
    else:
        owned_project_ids = [
            p.id for p in db.query(models.Project).filter(models.Project.owner_id == current_user.id)
        ]
        sites = db.query(models.Site).filter(models.Site.project_id.in_(owned_project_ids)).all()

    counts = {}
    for site in sites:
        status = site.deployment_status or "Prospecting"
        counts[status] = counts.get(status, 0) + 1
    return counts


@router.get("/platform-stats")
def platform_stats(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Admin Dashboard's "Platform analytics" sub-item — user counts by
    role, previously missing entirely (every other platform-wide stat
    was about sites/projects, none about the user base itself).
    Administrator-only, since this is account/user data, not project data.
    """
    if current_user.role != models.RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Only Administrators can view platform-wide user statistics.")

    users_by_role = {}
    for role in models.RoleEnum:
        users_by_role[role.value] = db.query(models.User).filter(models.User.role == role).count()

    return {
        "total_users": db.query(models.User).count(),
        "active_users": db.query(models.User).filter(models.User.is_active == True).count(),  # noqa: E712
        "users_by_role": users_by_role,
        "total_projects": db.query(models.Project).count(),
        "total_sites": db.query(models.Site).count(),
    }


@router.get("/recommended-sites")
def recommended_sites(
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Planner Dashboard's "Recommended Deployment Sites" — a REAL bug fix,
    found via live testing: this section previously read from the
    SiteRollup data warehouse table, which is only populated by a
    separate, manual "Refresh Data Warehouse" action restricted to
    Admin/Project Manager roles (see /analytics/warehouse/refresh's
    role check). A Planner registering their own sites had no way to
    trigger that refresh themselves, so this section would silently
    stay empty even with real, fully-scored sites sitting right there.
    This endpoint instead computes live, directly from the same tables
    a site's own detail view reads, with no manual refresh step ever
    required. Uses the same batched-query pattern as dashboard_summary
    to avoid an N+1 query per site.
    """
    if current_user.role in authz.READ_ALL_ROLES:
        projects = db.query(models.Project).all()
    else:
        projects = db.query(models.Project).filter(models.Project.owner_id == current_user.id).all()
    project_ids = [p.id for p in projects]
    project_names = {p.id: p.name for p in projects}

    sites = db.query(models.Site).filter(models.Site.project_id.in_(project_ids)).all() if project_ids else []
    site_ids = [s.id for s in sites]

    def _latest_by_site(model, order_col):
        if not site_ids:
            return {}
        rows = db.query(model).filter(model.site_id.in_(site_ids)).order_by(order_col.desc()).all()
        latest = {}
        for row in rows:
            if row.site_id not in latest:
                latest[row.site_id] = row
        return latest

    scores = _latest_by_site(models.SuitabilityScore, models.SuitabilityScore.computed_at)
    solar = _latest_by_site(models.SolarPotential, models.SolarPotential.computed_at)
    wind = _latest_by_site(models.WindPotential, models.WindPotential.computed_at)
    financial = _latest_by_site(models.FinancialAnalysis, models.FinancialAnalysis.computed_at)

    results = []
    for site in sites:
        score = scores.get(site.id)
        if not score:
            continue  # not yet scored — nothing meaningful to recommend on
        results.append({
            "site_id": site.id,
            "site_name": site.name,
            "project_name": project_names.get(site.project_id, "Unknown"),
            "overall_suitability_score": score.overall_score,
            "suitability_category": score.category,
            "solar_expected_output_mwh_yr": solar[site.id].expected_energy_output_mwh_yr if site.id in solar else None,
            "wind_expected_aep_mwh_yr": wind[site.id].expected_aep_mwh_yr if site.id in wind else None,
            "financial_irr_pct": financial[site.id].irr_pct if site.id in financial else None,
        })

    results.sort(key=lambda r: r["overall_suitability_score"], reverse=True)
    return results[:limit]
