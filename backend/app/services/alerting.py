"""
Automatic alert generation — turns weather and suitability data into
Notification & Alert System entries, per the project spec's "Weather alerts"
and "Site suitability updates" categories.
"""

from sqlalchemy.orm import Session

from app import models
from app.services.integration_dispatch import dispatch_event

HIGH_WIND_THRESHOLD_MS = 20.0
HIGH_RAINFALL_THRESHOLD_MM = 50.0


def generate_weather_alerts(db: Session, site: models.Site) -> None:
    latest = (
        db.query(models.WeatherReading)
        .filter(models.WeatherReading.site_id == site.id)
        .order_by(models.WeatherReading.reading_date.desc())
        .first()
    )
    if not latest:
        return

    created = []

    if latest.wind_speed and latest.wind_speed >= HIGH_WIND_THRESHOLD_MS:
        alert = models.Alert(
            site_id=site.id,
            project_id=site.project_id,
            title=f"High wind speed at {site.name}",
            message=f"Recorded wind speed of {latest.wind_speed} m/s exceeds the {HIGH_WIND_THRESHOLD_MS} m/s threshold.",
            severity=models.AlertSeverity.warning,
            category="weather",
        )
        db.add(alert)
        created.append(alert)

    if latest.rainfall and latest.rainfall >= HIGH_RAINFALL_THRESHOLD_MM:
        alert = models.Alert(
            site_id=site.id,
            project_id=site.project_id,
            title=f"Heavy rainfall at {site.name}",
            message=f"Recorded rainfall of {latest.rainfall} mm exceeds the {HIGH_RAINFALL_THRESHOLD_MM} mm threshold.",
            severity=models.AlertSeverity.warning,
            category="weather",
        )
        db.add(alert)
        created.append(alert)

    db.commit()

    # Push each new alert out to any connected project-management /
    # SCADA / analytics webhook (see services/integration_dispatch.py).
    # Best-effort: a webhook failure never rolls back the alert itself,
    # since the alert row is already committed above.
    for alert in created:
        try:
            dispatch_event(
                db,
                site.project_id,
                "weather_alert",
                {"site_id": site.id, "site_name": site.name, "title": alert.title, "message": alert.message, "severity": alert.severity.value},
            )
        except Exception as exc:  # noqa: BLE001
            print(f"Warning: integration dispatch failed for weather alert on site {site.id}: {exc}")


def generate_suitability_alert(db: Session, site: models.Site, score: models.SuitabilityScore) -> None:
    db.add(
        models.Alert(
            site_id=site.id,
            project_id=site.project_id,
            title=f"Suitability score updated for {site.name}",
            message=f"New overall score: {score.overall_score} ({score.category}).",
            severity=models.AlertSeverity.info,
            category="suitability",
        )
    )
    db.commit()

    try:
        dispatch_event(
            db,
            site.project_id,
            "suitability_score_updated",
            {
                "site_id": site.id,
                "site_name": site.name,
                "overall_score": score.overall_score,
                "category": score.category,
            },
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: integration dispatch failed for suitability alert on site {site.id}: {exc}")


def generate_environmental_risk_alert(db: Session, site: models.Site) -> None:
    """
    Environmental Risk Alerts — a named category in the project spec
    that had no implementation at all until this pass. Uses the same
    real ML Risk Assessment Model (see app/services/ml_risk_predictor.py)
    already computed for the site, rather than duplicating risk logic
    in two places.
    """
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
        return

    from app.services.ml_risk_predictor import predict_risk_category

    result = predict_risk_category(
        latest_wind.average_wind_speed_ms,
        env.protected_area_distance_km if env and env.protected_area_distance_km is not None else 20.0,
        site.land_slope_pct if site.land_slope_pct is not None else 5.0,
    )
    if not result or result["risk_category"] != "High":
        return  # Only alert on elevated risk, not every routine check

    alert = models.Alert(
        site_id=site.id,
        project_id=site.project_id,
        title=f"Elevated environmental/operational risk at {site.name}",
        message=f"Risk model flagged this site as High risk ({result['confidence_pct']}% confidence) \u2014 see the site's Risk Assessment panel for details.",
        severity=models.AlertSeverity.warning,
        category="environmental_risk",
    )
    db.add(alert)
    db.commit()

    try:
        dispatch_event(
            db, site.project_id, "environmental_risk_alert",
            {"site_id": site.id, "site_name": site.name, "risk_category": result["risk_category"], "confidence_pct": result["confidence_pct"]},
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: integration dispatch failed for environmental risk alert on site {site.id}: {exc}")


def generate_forecast_update_alert(db: Session, site: models.Site, previous_output_mwh_yr: float | None, new_output_mwh_yr: float | None) -> None:
    """
    Forecast Updates — another named spec category with no prior
    implementation. Fires when a site's expected annual output changes
    meaningfully between two consecutive "Refresh data" runs (e.g. new
    weather data shifted the estimate), not on every routine refresh
    where the number is essentially unchanged.
    """
    if previous_output_mwh_yr is None or new_output_mwh_yr is None or previous_output_mwh_yr == 0:
        return
    pct_change = abs(new_output_mwh_yr - previous_output_mwh_yr) / previous_output_mwh_yr * 100
    if pct_change < 10:
        return  # Not a meaningful change — don't spam an alert for routine noise

    direction = "increased" if new_output_mwh_yr > previous_output_mwh_yr else "decreased"
    alert = models.Alert(
        site_id=site.id,
        project_id=site.project_id,
        title=f"Energy forecast updated for {site.name}",
        message=f"Expected annual output {direction} by {pct_change:.1f}% (from {previous_output_mwh_yr:.0f} to {new_output_mwh_yr:.0f} MWh/yr per MW) since the last refresh.",
        severity=models.AlertSeverity.info,
        category="forecast_update",
    )
    db.add(alert)
    db.commit()

    try:
        dispatch_event(
            db, site.project_id, "forecast_updated",
            {"site_id": site.id, "site_name": site.name, "previous_output_mwh_yr": previous_output_mwh_yr, "new_output_mwh_yr": new_output_mwh_yr, "pct_change": round(pct_change, 1)},
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: integration dispatch failed for forecast update alert on site {site.id}: {exc}")


def generate_project_notification(db: Session, project_id: int, title: str, message: str, severity=None) -> None:
    """
    Project Notifications — the spec's most general alert category:
    project-level events not tied to any single site (e.g. a new site
    added to the project). site_id is left null deliberately (see
    models.Alert — it's nullable exactly for this case).
    """
    alert = models.Alert(
        site_id=None,
        project_id=project_id,
        title=title,
        message=message,
        severity=severity or models.AlertSeverity.info,
        category="project_notification",
    )
    db.add(alert)
    db.commit()

    try:
        dispatch_event(db, project_id, "project_notification", {"title": title, "message": message})
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: integration dispatch failed for project notification on project {project_id}: {exc}")
