import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app import models, schemas, auth, authz
from app.database import get_db
from app.services.environmental import fetch_and_store_weather_data, fetch_seasonal_climatology, distribute_annual_output_by_month
from app.services.terrain import fetch_elevation, estimate_slope_pct
from app.services.infrastructure import fetch_and_store_infrastructure
from app.services.geo_utils import site_point_wkt
from app.services.scoring import compute_site_suitability
from app.services.alerting import generate_weather_alerts, generate_suitability_alert
from app.services.satellite import fetch_and_store_satellite_summary
from app.services.land_data import fetch_and_store_environmental_constraints
from app.services.supplemental_weather import fetch_and_store_supplemental_weather
from app.services.solar_engine import compute_solar_potential
from app.services.wind_engine import compute_wind_potential
from app.services.financial import compute_financial_analysis
from app.services.power_simulation import simulate_power_output
from app.services.deployment_optimizer import recommend_technology, estimate_grid_contribution
from app.services.ml_investment_predictor import predict_npv_and_irr
from app.services.ml_risk_predictor import predict_risk_category
from app.security import log_action
from app import mongo
from app import data_lake

router = APIRouter(prefix="/projects/{project_id}/sites", tags=["Sites"])


def _run_full_intelligence_pipeline(db: Session, site: models.Site) -> None:
    """
    Runs every data-collection and prediction engine for a site, in the
    same resilience pattern as the rest of this file: each stage is
    independent and best-effort, so one upstream hiccup (e.g. Sentinel Hub
    rate-limited) never blocks the others from running or turns a
    register/refresh call into a 500. Called from both register_site and
    refresh_site_data so a fresh site and a re-analyzed site go through
    the identical pipeline.
    """
    try:
        fetch_and_store_weather_data(db, site)
        generate_weather_alerts(db, site)
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: weather data fetch failed for site {site.id}: {exc}")

    try:
        fetch_and_store_infrastructure(db, site)
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: infrastructure data fetch failed for site {site.id}: {exc}")

    try:
        fetch_and_store_satellite_summary(db, site)
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: satellite imagery fetch failed for site {site.id}: {exc}")

    try:
        fetch_and_store_environmental_constraints(db, site)
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: environmental/demographic data fetch failed for site {site.id}: {exc}")

    try:
        fetch_and_store_supplemental_weather(db, site)
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: supplemental weather (OpenWeather/NOAA) fetch failed for site {site.id}: {exc}")

    db.refresh(site)

    try:
        compute_solar_potential(db, site)
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: solar potential computation failed for site {site.id}: {exc}")

    try:
        compute_wind_potential(db, site)
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: wind potential computation failed for site {site.id}: {exc}")

    try:
        db.refresh(site)
        score = compute_site_suitability(db, site)
        generate_suitability_alert(db, site, score)
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: suitability scoring failed for site {site.id}: {exc}")


def _get_project_or_404(project_id: int, db: Session) -> models.Project:
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _get_site_or_404(project_id: int, site_id: int, db: Session) -> models.Site:
    site = (
        db.query(models.Site)
        .filter(models.Site.project_id == project_id, models.Site.id == site_id)
        .first()
    )
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return site


@router.post("/", response_model=schemas.SiteOut, status_code=201)
def register_site(
    request: Request,
    project_id: int,
    site_in: schemas.SiteCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    project = _get_project_or_404(project_id, db)
    authz.require_project_write(project, current_user)

    site = models.Site(project_id=project.id, **site_in.model_dump())
    # Populate the PostGIS geometry column alongside the plain lat/long
    # floats (which the rest of the app still reads directly). No-op-safe
    # against SQLite, where geom stays null.
    try:
        site.geom = site_point_wkt(site_in.latitude, site_in.longitude)
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: could not set PostGIS geometry (non-Postgres backend?): {exc}")
    db.add(site)
    db.commit()
    db.refresh(site)

    # Step 4 of the User Workflow: system fetches weather/terrain/infra data
    # in the background. Kept synchronous here for simplicity — swap for a
    # background task queue (Celery/RQ) before production scale.
    #
    # Wrapped in try/except like every other stage of this pipeline (see
    # _run_full_intelligence_pipeline below) — this was a real bug found
    # via live testing: it was the one external call in this whole
    # endpoint NOT protected this way, so an Open-Elevation hiccup
    # (rate-limit, gateway error, malformed response) could raise all
    # the way up to an unhandled 500, surfacing to the user as a bare
    # "Could not register site" with zero indication why.
    try:
        if site.elevation_m is None:
            elevation = fetch_elevation(site.latitude, site.longitude)
            if elevation is not None:
                site.elevation_m = elevation
        if site.land_slope_pct is None:
            slope = estimate_slope_pct(site.latitude, site.longitude)
            if slope is not None:
                site.land_slope_pct = slope
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: elevation/slope lookup failed for site {site.id}: {exc}")
    db.commit()
    db.refresh(site)

    _run_full_intelligence_pipeline(db, site)

    log_action(db, current_user.id, "register_site", f"site:{site.id}", request.client.host)
    return site


@router.post("/{site_id}/refresh-data", response_model=schemas.SiteOut)
def refresh_site_data(
    request: Request,
    project_id: int,
    site_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Re-pulls weather + infrastructure data and recomputes the suitability score."""
    project = _get_project_or_404(project_id, db)
    authz.require_project_analysis(project, current_user)
    site = _get_site_or_404(project_id, site_id, db)

    # Same resilience pattern as register_site: an upstream API hiccup
    # (NASA POWER / Overpass / Sentinel Hub / World Bank) shouldn't turn a
    # refresh into a 500 — log and continue so whatever data pipelines did
    # succeed still get applied.
    _run_full_intelligence_pipeline(db, site)

    log_action(db, current_user.id, "refresh_site_data", f"site:{site.id}", request.client.host)
    return site


@router.get("/", response_model=List[schemas.SiteOut])
def list_sites(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    project = _get_project_or_404(project_id, db)
    authz.require_project_read(project, current_user)
    return db.query(models.Site).filter(models.Site.project_id == project_id).all()


@router.get("/compare", response_model=List[schemas.SiteComparisonOut])
def compare_sites(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Side-by-side comparison for all sites in a project (User Workflow Step 7)."""
    project = _get_project_or_404(project_id, db)
    authz.require_project_read(project, current_user)

    sites = db.query(models.Site).filter(models.Site.project_id == project_id).all()
    results = []
    for site in sites:
        latest_score = (
            db.query(models.SuitabilityScore)
            .filter(models.SuitabilityScore.site_id == site.id)
            .order_by(models.SuitabilityScore.computed_at.desc())
            .first()
        )
        results.append(
            {
                "site_id": site.id,
                "site_name": site.name,
                "overall_score": latest_score.overall_score if latest_score else None,
                "category": latest_score.category if latest_score else "Unscored",
            }
        )
    results.sort(key=lambda r: (r["overall_score"] is None, -(r["overall_score"] or 0)))
    return results


@router.get("/{site_id}", response_model=schemas.SiteOut)
def get_site(
    project_id: int,
    site_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    project = _get_project_or_404(project_id, db)
    authz.require_project_read(project, current_user)
    return _get_site_or_404(project_id, site_id, db)


@router.get("/{site_id}/weather", response_model=List[schemas.WeatherReadingOut])
def get_site_weather(
    project_id: int,
    site_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    project = _get_project_or_404(project_id, db)
    authz.require_project_read(project, current_user)
    site = _get_site_or_404(project_id, site_id, db)
    return site.weather_readings


@router.get("/{site_id}/supplemental-weather", response_model=List[schemas.SupplementalWeatherReadingOut])
def get_site_supplemental_weather(
    project_id: int,
    site_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Live OpenWeather current-conditions + NOAA forecast readings — cross-validation, not scoring input."""
    project = _get_project_or_404(project_id, db)
    authz.require_project_read(project, current_user)
    site = _get_site_or_404(project_id, site_id, db)
    return (
        db.query(models.SupplementalWeatherReading)
        .filter(models.SupplementalWeatherReading.site_id == site.id)
        .order_by(models.SupplementalWeatherReading.fetched_at.desc())
        .limit(10)
        .all()
    )


@router.get("/{site_id}/infrastructure", response_model=List[schemas.InfrastructureFeatureOut])
def get_site_infrastructure(
    project_id: int,
    site_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    project = _get_project_or_404(project_id, db)
    authz.require_project_read(project, current_user)
    site = _get_site_or_404(project_id, site_id, db)
    return site.infrastructure_features


@router.get("/{site_id}/suitability", response_model=schemas.SuitabilityScoreOut)
def get_site_suitability(
    project_id: int,
    site_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    project = _get_project_or_404(project_id, db)
    authz.require_project_read(project, current_user)
    site = _get_site_or_404(project_id, site_id, db)

    latest = (
        db.query(models.SuitabilityScore)
        .filter(models.SuitabilityScore.site_id == site.id)
        .order_by(models.SuitabilityScore.computed_at.desc())
        .first()
    )
    if not latest:
        raise HTTPException(status_code=404, detail="No suitability score computed yet")
    return latest


@router.get("/{site_id}/ingestion-log", response_model=schemas.IngestionLogOut)
def get_site_ingestion_log(
    project_id: int,
    site_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Proof-of-ingestion — literal evidence that this site's environmental
    and infrastructure data actually came from the external APIs (NASA
    POWER, OpenStreetMap/Overpass) rather than being assumed: counts of
    what's stored in PostgreSQL, plus the raw-payload write history from
    MongoDB (source, and exactly when each was fetched).
    """
    project = _get_project_or_404(project_id, db)
    authz.require_project_read(project, current_user)
    site = _get_site_or_404(project_id, site_id, db)

    weather_count = (
        db.query(models.WeatherReading).filter(models.WeatherReading.site_id == site.id).count()
    )
    infra_count = (
        db.query(models.InfrastructureFeature)
        .filter(models.InfrastructureFeature.site_id == site.id)
        .count()
    )
    latest_weather = (
        db.query(models.WeatherReading)
        .filter(models.WeatherReading.site_id == site.id)
        .order_by(models.WeatherReading.reading_date.desc())
        .first()
    )

    return {
        "site_id": site.id,
        "weather_readings_count": weather_count,
        "infrastructure_features_count": infra_count,
        "latest_weather_reading_date": latest_weather.reading_date if latest_weather else None,
        "has_postgis_geometry": site.geom is not None,
        "raw_payload_events": mongo.list_ingestion_events(site.id),
        "data_lake_archival_enabled": data_lake.is_configured(),
    }


# ---------- Satellite Imagery ----------

@router.get("/{site_id}/satellite", response_model=schemas.SiteImageOut)
def get_site_satellite_summary(
    project_id: int,
    site_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    project = _get_project_or_404(project_id, db)
    authz.require_project_read(project, current_user)
    site = _get_site_or_404(project_id, site_id, db)

    latest = (
        db.query(models.SiteImage)
        .filter(models.SiteImage.site_id == site.id)
        .order_by(models.SiteImage.fetched_at.desc())
        .first()
    )
    if not latest:
        raise HTTPException(status_code=404, detail="No satellite imagery fetched yet — run refresh-data first")
    return latest


# ---------- Environmental Constraints / Demographic & Land Data ----------

@router.get("/{site_id}/environmental-constraints", response_model=schemas.EnvironmentalConstraintOut)
def get_site_environmental_constraints(
    project_id: int,
    site_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    project = _get_project_or_404(project_id, db)
    authz.require_project_read(project, current_user)
    site = _get_site_or_404(project_id, site_id, db)

    latest = (
        db.query(models.EnvironmentalConstraint)
        .filter(models.EnvironmentalConstraint.site_id == site.id)
        .order_by(models.EnvironmentalConstraint.fetched_at.desc())
        .first()
    )
    if not latest:
        raise HTTPException(status_code=404, detail="No environmental/land data fetched yet — run refresh-data first")
    return latest


# ---------- Solar / Wind Potential ----------

@router.get("/{site_id}/solar-potential", response_model=schemas.SolarPotentialOut)
def get_site_solar_potential(
    project_id: int,
    site_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    project = _get_project_or_404(project_id, db)
    authz.require_project_read(project, current_user)
    site = _get_site_or_404(project_id, site_id, db)

    latest = (
        db.query(models.SolarPotential)
        .filter(models.SolarPotential.site_id == site.id)
        .order_by(models.SolarPotential.computed_at.desc())
        .first()
    )
    if not latest:
        raise HTTPException(status_code=404, detail="Solar potential not computed yet — run refresh-data first")
    return latest


@router.get("/{site_id}/wind-potential", response_model=schemas.WindPotentialOut)
def get_site_wind_potential(
    project_id: int,
    site_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    project = _get_project_or_404(project_id, db)
    authz.require_project_read(project, current_user)
    site = _get_site_or_404(project_id, site_id, db)

    latest = (
        db.query(models.WindPotential)
        .filter(models.WindPotential.site_id == site.id)
        .order_by(models.WindPotential.computed_at.desc())
        .first()
    )
    if not latest:
        raise HTTPException(status_code=404, detail="Wind potential not computed yet — run refresh-data first")
    return latest


# ---------- Financial / Investment Analytics ----------

@router.post("/{site_id}/financial-analysis", response_model=schemas.FinancialAnalysisOut, status_code=201)
def create_site_financial_analysis(
    request: Request,
    project_id: int,
    site_id: int,
    body: schemas.FinancialAnalysisCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Runs the deterministic NPV/IRR/LCOE/payback model against a site
    using user-supplied cost/price assumptions. If annual_energy_mwh is
    omitted, it's derived from the site's latest Solar/Wind Potential
    output scaled to the requested capacity_mw.
    """
    project = _get_project_or_404(project_id, db)
    authz.require_project_analysis(project, current_user)
    site = _get_site_or_404(project_id, site_id, db)

    annual_energy_mwh = body.annual_energy_mwh
    if annual_energy_mwh is None:
        if body.technology == "wind":
            latest = (
                db.query(models.WindPotential)
                .filter(models.WindPotential.site_id == site.id)
                .order_by(models.WindPotential.computed_at.desc())
                .first()
            )
            per_mw = latest.expected_aep_mwh_yr if latest else None
        else:
            latest = (
                db.query(models.SolarPotential)
                .filter(models.SolarPotential.site_id == site.id)
                .order_by(models.SolarPotential.computed_at.desc())
                .first()
            )
            per_mw = latest.expected_energy_output_mwh_yr if latest else None
        if per_mw is None:
            raise HTTPException(
                status_code=422,
                detail=(
                    "No solar/wind potential computed for this site yet, and no "
                    "annual_energy_mwh override was supplied — run refresh-data first "
                    "or pass annual_energy_mwh explicitly."
                ),
            )
        annual_energy_mwh = round(per_mw * body.capacity_mw, 1)

    record = compute_financial_analysis(
        db,
        site,
        technology=body.technology,
        capacity_mw=body.capacity_mw,
        capex_usd=body.capex_usd,
        opex_usd_per_yr=body.opex_usd_per_yr,
        discount_rate_pct=body.discount_rate_pct,
        project_lifetime_yrs=body.project_lifetime_yrs,
        electricity_price_usd_per_mwh=body.electricity_price_usd_per_mwh,
        annual_energy_mwh=annual_energy_mwh,
    )
    log_action(db, current_user.id, "compute_financial_analysis", f"site:{site.id}", request.client.host)
    return record


@router.get("/{site_id}/financial-analysis", response_model=List[schemas.FinancialAnalysisOut])
def list_site_financial_analyses(
    project_id: int,
    site_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    project = _get_project_or_404(project_id, db)
    authz.require_project_read(project, current_user)
    site = _get_site_or_404(project_id, site_id, db)
    return (
        db.query(models.FinancialAnalysis)
        .filter(models.FinancialAnalysis.site_id == site.id)
        .order_by(models.FinancialAnalysis.computed_at.desc())
        .all()
    )


# ---------- SCADA / IoT Telemetry ----------

@router.post("/{site_id}/telemetry", response_model=schemas.TelemetryReadingOut, status_code=201)
def ingest_site_telemetry(
    project_id: int,
    site_id: int,
    body: schemas.TelemetryIngestIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    SCADA/IoT ingestion endpoint — accepts one live operational reading
    (inverter output, turbine RPM, grid export, etc) from an already-
    deployed site's monitoring system. Authenticated the same way as
    every other write in this API (bearer token); a deployed SCADA
    bridge should hold a service account with Project Manager or
    Administrator role, or an IntegrationConnection's stored credential
    if pushing through that route instead — see routers/integrations.py.
    """
    project = _get_project_or_404(project_id, db)
    authz.require_project_analysis(project, current_user)
    site = _get_site_or_404(project_id, site_id, db)

    reading = models.TelemetryReading(
        site_id=site.id,
        metric_name=body.metric_name,
        value=body.value,
        unit=body.unit,
        recorded_at=body.recorded_at or datetime.datetime.utcnow(),
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading


@router.get("/{site_id}/telemetry", response_model=List[schemas.TelemetryReadingOut])
def list_site_telemetry(
    project_id: int,
    site_id: int,
    metric_name: str | None = None,
    limit: int = 500,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    project = _get_project_or_404(project_id, db)
    authz.require_project_read(project, current_user)
    site = _get_site_or_404(project_id, site_id, db)

    query = db.query(models.TelemetryReading).filter(models.TelemetryReading.site_id == site.id)
    if metric_name:
        query = query.filter(models.TelemetryReading.metric_name == metric_name)
    return query.order_by(models.TelemetryReading.recorded_at.desc()).limit(min(limit, 5000)).all()


# ---------- Power System Simulation ----------

@router.post("/{site_id}/simulate-output", response_model=schemas.PowerSimulationOut)
def simulate_site_power_output(
    project_id: int,
    site_id: int,
    body: schemas.PowerSimulationRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Deterministic hourly output-profile simulation (see
    app/services/power_simulation.py) — driven by the site's already-
    computed capacity factor, not a live SCADA feed. Useful for
    modeling "what would this site produce" before anything is built.
    """
    project = _get_project_or_404(project_id, db)
    authz.require_project_read(project, current_user)
    site = _get_site_or_404(project_id, site_id, db)

    series = simulate_power_output(db, site, body.technology, body.capacity_mw, body.hours)
    return {
        "site_id": site.id,
        "technology": body.technology,
        "capacity_mw": body.capacity_mw,
        "series": series,
    }


# ---------- Deployment Optimization Engine ----------

@router.get("/{site_id}/technology-recommendation", response_model=schemas.TechnologyRecommendationOut)
def get_technology_recommendation(
    project_id: int,
    site_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Technology Selection + Hybrid Solar-Wind Recommendations: compares
    this site's already-computed solar and wind capacity factors (does
    not run any new prediction) and recommends Solar, Wind, or Hybrid,
    with a capacity plan sized from the site's actual land area using
    published NREL land-use figures.
    """
    project = _get_project_or_404(project_id, db)
    authz.require_project_read(project, current_user)
    site = _get_site_or_404(project_id, site_id, db)

    latest_solar = (
        db.query(models.SolarPotential)
        .filter(models.SolarPotential.site_id == site.id)
        .order_by(models.SolarPotential.computed_at.desc())
        .first()
    )
    latest_wind = (
        db.query(models.WindPotential)
        .filter(models.WindPotential.site_id == site.id)
        .order_by(models.WindPotential.computed_at.desc())
        .first()
    )
    result = recommend_technology(
        latest_solar.capacity_factor_pct if latest_solar else None,
        latest_wind.capacity_factor_pct if latest_wind else None,
        site.land_area_hectares,
    )
    return result


@router.get("/{site_id}/grid-contribution", response_model=schemas.GridContributionOut)
def get_grid_contribution(
    project_id: int,
    site_id: int,
    technology: str = "solar",
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Grid Contribution Forecasting: translates the site's already-computed
    annual output into a "homes powered" estimate, using this site's own
    country's real World Bank per-capita electricity consumption figure.
    """
    project = _get_project_or_404(project_id, db)
    authz.require_project_read(project, current_user)
    site = _get_site_or_404(project_id, site_id, db)

    if technology == "wind":
        latest = (
            db.query(models.WindPotential)
            .filter(models.WindPotential.site_id == site.id)
            .order_by(models.WindPotential.computed_at.desc())
            .first()
        )
        annual_output = latest.expected_aep_mwh_yr if latest else None
    else:
        latest = (
            db.query(models.SolarPotential)
            .filter(models.SolarPotential.site_id == site.id)
            .order_by(models.SolarPotential.computed_at.desc())
            .first()
        )
        annual_output = latest.expected_energy_output_mwh_yr if latest else None

    env = (
        db.query(models.EnvironmentalConstraint)
        .filter(models.EnvironmentalConstraint.site_id == site.id)
        .order_by(models.EnvironmentalConstraint.fetched_at.desc())
        .first()
    )
    result = estimate_grid_contribution(
        annual_output, env.electricity_consumption_kwh_per_capita if env else None
    )
    if result is None:
        return schemas.GridContributionOut(homes_powered_equivalent=None, basis="Not enough data yet \u2014 needs both computed output and environmental/demographic data (run \u201cRefresh data\u201d).")
    return result


@router.get("/{site_id}/seasonal-forecast", response_model=schemas.SeasonalForecastOut)
def get_seasonal_forecast(
    project_id: int,
    site_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Seasonal Generation Prediction: redistributes the site's already-
    computed annual solar output across 12 months using NASA POWER's
    long-term climatology (a different, longer-baseline endpoint than
    the 7-day one the daily pipeline uses) — not a new independent
    annual estimate.
    """
    project = _get_project_or_404(project_id, db)
    authz.require_project_read(project, current_user)
    site = _get_site_or_404(project_id, site_id, db)

    latest_solar = (
        db.query(models.SolarPotential)
        .filter(models.SolarPotential.site_id == site.id)
        .order_by(models.SolarPotential.computed_at.desc())
        .first()
    )
    if not latest_solar or not latest_solar.expected_energy_output_mwh_yr:
        raise HTTPException(status_code=422, detail="No solar potential computed yet for this site \u2014 run \u201cRefresh data\u201d first.")

    monthly_climatology = fetch_seasonal_climatology(site)
    if not monthly_climatology:
        raise HTTPException(status_code=503, detail="NASA POWER climatology data is currently unavailable for this location.")

    monthly_output = distribute_annual_output_by_month(latest_solar.expected_energy_output_mwh_yr, monthly_climatology)
    return schemas.SeasonalForecastOut(
        site_id=site.id,
        monthly_output_mwh_per_mw=monthly_output,
        note="Redistributes the already-computed annual output across months using NASA POWER's long-term climatology, not a new independent prediction.",
    )


# ---------- AI/ML: Investment Prediction Model + Risk Assessment Model ----------

@router.post("/{site_id}/ml-investment-estimate", response_model=schemas.MLInvestmentEstimateOut)
def get_ml_investment_estimate(
    project_id: int,
    site_id: int,
    body: schemas.MLInvestmentEstimateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Investment Prediction Model (PDF: Regression/XGBoost) — an instant
    NPV/IRR estimate from a trained model, without running the full
    financial.py calculation. Always a fast estimate, never a
    replacement for POST .../financial-analysis, which remains the
    authoritative real calculation once you commit to real assumptions.
    """
    project = _get_project_or_404(project_id, db)
    authz.require_project_read(project, current_user)
    _get_site_or_404(project_id, site_id, db)  # 404s if the site doesn't exist/belong to this project

    result = predict_npv_and_irr(
        body.capacity_mw, body.capex_usd, body.opex_usd_per_yr, body.discount_rate_pct,
        body.project_lifetime_yrs, body.electricity_price_usd_per_mwh, body.annual_energy_mwh,
    )
    if result is None:
        raise HTTPException(status_code=503, detail="Investment prediction model is not available.")

    from app.services.ml_investment_predictor import model_version as _mv
    return schemas.MLInvestmentEstimateOut(
        npv_usd=result["npv_usd"],
        irr_pct=result["irr_pct"],
        model_version=_mv() or "unknown",
        note="Fast ML estimate, trained on the platform's own validated financial formula. Run the full financial analysis for the authoritative number.",
    )


@router.get("/{site_id}/ml-risk-assessment", response_model=schemas.MLRiskAssessmentOut)
def get_ml_risk_assessment(
    project_id: int,
    site_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Risk Assessment Model (PDF: LSTM/Prophet, substituted here — see
    app/services/ml_risk_predictor.py's docstring for why). Uses the
    site's real computed wind data plus environmental siting factors.
    """
    project = _get_project_or_404(project_id, db)
    authz.require_project_read(project, current_user)
    site = _get_site_or_404(project_id, site_id, db)

    latest_wind = (
        db.query(models.WindPotential)
        .filter(models.WindPotential.site_id == site.id)
        .order_by(models.WindPotential.computed_at.desc())
        .first()
    )
    env = (
        db.query(models.EnvironmentalConstraint)
        .filter(models.EnvironmentalConstraint.site_id == site.id)
        .order_by(models.EnvironmentalConstraint.fetched_at.desc())
        .first()
    )
    if not latest_wind or not latest_wind.average_wind_speed_ms:
        raise HTTPException(status_code=422, detail="No wind data computed yet for this site \u2014 run \u201cRefresh data\u201d first.")

    result = predict_risk_category(
        latest_wind.average_wind_speed_ms,
        env.protected_area_distance_km if env and env.protected_area_distance_km is not None else 20.0,
        site.land_slope_pct if site.land_slope_pct is not None else 5.0,
    )
    if result is None:
        raise HTTPException(status_code=503, detail="Risk assessment model is not available.")

    from app.services.ml_risk_predictor import model_version as _mv
    return schemas.MLRiskAssessmentOut(
        risk_category=result["risk_category"],
        confidence_pct=result["confidence_pct"],
        model_version=_mv() or "unknown",
        note="Currently driven almost entirely by wind speed (99%+ of the model's decision weight, verified via feature importance) \u2014 not yet a meaningful environmental/permitting risk assessment despite accepting those inputs. See the model's metadata for the full honest limitation.",
    )
