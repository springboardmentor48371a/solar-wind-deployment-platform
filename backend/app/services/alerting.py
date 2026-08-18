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
