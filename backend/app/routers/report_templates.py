"""
Custom Report Builder — the "Custom Report Builder / Executive Summary /
Templates Management" module. Lets a user save a named set of sections
(ReportTemplate) and re-run it on any project, or generate a one-off
report with an ad-hoc section list without saving a template.

Sections are assembled from the same underlying data every other
endpoint in this API already serves (suitability, solar, wind, financial,
environmental, infrastructure, weather, satellite) — this module's job is
purely selection + PDF layout, not new data collection.
"""

import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from app import models, schemas, auth, authz
from app.database import get_db
from app.services.score_explanation import explain_suitability_score
from app.security import log_action

router = APIRouter(tags=["Report Builder"])

HEADER_STYLE = TableStyle(
    [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e6f4c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6f8")]),
    ]
)


# ---------- Template CRUD ----------

@router.post("/report-templates", response_model=schemas.ReportTemplateOut, status_code=201)
def create_report_template(
    body: schemas.ReportTemplateCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    template = models.ReportTemplate(
        owner_id=current_user.id,
        name=body.name,
        description=body.description,
        sections=",".join(body.sections),
        is_executive_summary=1 if body.is_executive_summary else 0,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.get("/report-templates", response_model=list[schemas.ReportTemplateOut])
def list_report_templates(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return (
        db.query(models.ReportTemplate)
        .filter(models.ReportTemplate.owner_id == current_user.id)
        .order_by(models.ReportTemplate.created_at.desc())
        .all()
    )


@router.delete("/report-templates/{template_id}", status_code=204)
def delete_report_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    template = (
        db.query(models.ReportTemplate)
        .filter(models.ReportTemplate.id == template_id, models.ReportTemplate.owner_id == current_user.id)
        .first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Report template not found")
    db.delete(template)
    db.commit()


# ---------- Section builders ----------

def _section_summary(styles, project, sites, db):
    elements = [Paragraph("Executive Summary", styles["Heading2"])]
    scored = 0
    total_score = 0.0
    for site in sites:
        latest = (
            db.query(models.SuitabilityScore)
            .filter(models.SuitabilityScore.site_id == site.id)
            .order_by(models.SuitabilityScore.computed_at.desc())
            .first()
        )
        if latest:
            scored += 1
            total_score += latest.overall_score
    avg = round(total_score / scored, 1) if scored else None
    elements.append(
        Paragraph(
            f"Project <b>{project.name}</b> contains {len(sites)} registered site(s), "
            f"{scored} of which have a computed suitability score "
            f"(portfolio average: {avg if avg is not None else 'N/A'}). "
            f"{project.objective or ''}",
            styles["BodyText"],
        )
    )
    elements.append(Spacer(1, 10))
    return elements


def _section_suitability(styles, project, sites, db):
    elements = [Paragraph("Site Suitability", styles["Heading2"])]
    data = [["Site", "Overall Score", "Category"]]
    for site in sites:
        latest = (
            db.query(models.SuitabilityScore)
            .filter(models.SuitabilityScore.site_id == site.id)
            .order_by(models.SuitabilityScore.computed_at.desc())
            .first()
        )
        data.append([site.name, str(latest.overall_score) if latest else "\u2014", latest.category if latest else "Unscored"])
    table = Table(data, hAlign="LEFT")
    table.setStyle(HEADER_STYLE)
    elements.extend([table, Spacer(1, 10)])

    # Reasoning per site — same explanation logic the fixed-format PDF
    # export uses, so "why did this site score this way" is answered
    # consistently across both report formats.
    for site in sites:
        latest = (
            db.query(models.SuitabilityScore)
            .filter(models.SuitabilityScore.site_id == site.id)
            .order_by(models.SuitabilityScore.computed_at.desc())
            .first()
        )
        if not latest:
            continue
        elements.append(Paragraph(f"Why {site.name} scored {latest.overall_score} ({latest.category})", styles["Heading3"]))
        for reason in explain_suitability_score(db, site, latest):
            elements.append(Paragraph(f"\u2022 {reason}", styles["BodyText"]))
        elements.append(Spacer(1, 8))
    return elements


def _section_solar(styles, project, sites, db):
    elements = [Paragraph("Solar Potential", styles["Heading2"])]
    data = [["Site", "Annual Output (MWh/MW)", "Capacity Factor %", "Panel Efficiency %"]]
    for site in sites:
        latest = (
            db.query(models.SolarPotential)
            .filter(models.SolarPotential.site_id == site.id)
            .order_by(models.SolarPotential.computed_at.desc())
            .first()
        )
        if latest:
            data.append([
                site.name,
                str(latest.expected_energy_output_mwh_yr or "\u2014"),
                str(latest.capacity_factor_pct or "\u2014"),
                str(latest.panel_efficiency_pct or "\u2014"),
            ])
    if len(data) > 1:
        table = Table(data, hAlign="LEFT")
        table.setStyle(HEADER_STYLE)
        elements.append(table)
    else:
        elements.append(Paragraph("No solar potential data computed yet.", styles["BodyText"]))
    elements.append(Spacer(1, 10))
    return elements


def _section_wind(styles, project, sites, db):
    elements = [Paragraph("Wind Potential", styles["Heading2"])]
    data = [["Site", "Expected AEP (MWh/MW)", "Capacity Factor %", "Turbine Class"]]
    for site in sites:
        latest = (
            db.query(models.WindPotential)
            .filter(models.WindPotential.site_id == site.id)
            .order_by(models.WindPotential.computed_at.desc())
            .first()
        )
        if latest:
            data.append([
                site.name,
                str(latest.expected_aep_mwh_yr or "\u2014"),
                str(latest.capacity_factor_pct or "\u2014"),
                latest.turbine_class or "\u2014",
            ])
    if len(data) > 1:
        table = Table(data, hAlign="LEFT")
        table.setStyle(HEADER_STYLE)
        elements.append(table)
    else:
        elements.append(Paragraph("No wind potential data computed yet.", styles["BodyText"]))
    elements.append(Spacer(1, 10))
    return elements


def _section_financial(styles, project, sites, db):
    elements = [Paragraph("Investment Analytics", styles["Heading2"])]
    data = [["Site", "NPV (USD)", "IRR %", "LCOE ($/MWh)", "Payback (yrs)"]]
    for site in sites:
        latest = (
            db.query(models.FinancialAnalysis)
            .filter(models.FinancialAnalysis.site_id == site.id)
            .order_by(models.FinancialAnalysis.computed_at.desc())
            .first()
        )
        if latest:
            data.append([
                site.name,
                f"{latest.npv_usd:,.0f}" if latest.npv_usd is not None else "\u2014",
                str(latest.irr_pct if latest.irr_pct is not None else "\u2014"),
                str(latest.lcoe_usd_per_mwh if latest.lcoe_usd_per_mwh is not None else "\u2014"),
                str(latest.payback_years if latest.payback_years is not None else "\u2014"),
            ])
    if len(data) > 1:
        table = Table(data, hAlign="LEFT")
        table.setStyle(HEADER_STYLE)
        elements.append(table)
    else:
        elements.append(Paragraph("No financial analysis run yet for any site in this project.", styles["BodyText"]))
    elements.append(Spacer(1, 10))
    return elements


def _section_environmental(styles, project, sites, db):
    elements = [Paragraph("Environmental & Demographic Constraints", styles["Heading2"])]
    data = [["Site", "Protected Area (km)", "Water Body (km)", "Country", "Pop. Density"]]
    for site in sites:
        latest = (
            db.query(models.EnvironmentalConstraint)
            .filter(models.EnvironmentalConstraint.site_id == site.id)
            .order_by(models.EnvironmentalConstraint.fetched_at.desc())
            .first()
        )
        if latest:
            data.append([
                site.name,
                str(latest.protected_area_distance_km if latest.protected_area_distance_km is not None else "\u2014"),
                str(latest.water_body_distance_km if latest.water_body_distance_km is not None else "\u2014"),
                latest.country_iso3 or "\u2014",
                str(latest.population_density_km2 if latest.population_density_km2 is not None else "\u2014"),
            ])
    if len(data) > 1:
        table = Table(data, hAlign="LEFT")
        table.setStyle(HEADER_STYLE)
        elements.append(table)
    else:
        elements.append(Paragraph("No environmental/demographic data fetched yet.", styles["BodyText"]))
    elements.append(Spacer(1, 10))
    return elements


def _section_infrastructure(styles, project, sites, db):
    elements = [Paragraph("Infrastructure Proximity", styles["Heading2"])]
    data = [["Site", "Feature", "Distance (km)"]]
    for site in sites:
        for feature in site.infrastructure_features:
            data.append([site.name, feature.feature_type, str(feature.distance_km)])
    if len(data) > 1:
        table = Table(data, hAlign="LEFT")
        table.setStyle(HEADER_STYLE)
        elements.append(table)
    else:
        elements.append(Paragraph("No infrastructure data fetched yet.", styles["BodyText"]))
    elements.append(Spacer(1, 10))
    return elements


def _section_weather(styles, project, sites, db):
    elements = [Paragraph("Recent Weather / Climate", styles["Heading2"])]
    data = [["Site", "Date", "Irradiance (kWh/m2/day)", "Wind Speed (m/s)"]]
    for site in sites:
        for reading in sorted(site.weather_readings, key=lambda r: r.reading_date, reverse=True)[:3]:
            data.append([
                site.name,
                str(reading.reading_date),
                str(reading.solar_irradiance if reading.solar_irradiance is not None else "\u2014"),
                str(reading.wind_speed if reading.wind_speed is not None else "\u2014"),
            ])
    if len(data) > 1:
        table = Table(data, hAlign="LEFT")
        table.setStyle(HEADER_STYLE)
        elements.append(table)
    else:
        elements.append(Paragraph("No weather data fetched yet.", styles["BodyText"]))
    elements.append(Spacer(1, 10))
    return elements


def _section_satellite(styles, project, sites, db):
    elements = [Paragraph("Satellite Imagery Summary", styles["Heading2"])]
    data = [["Site", "Provider", "Scene Date", "Cloud Cover %", "Land Cover"]]
    for site in sites:
        latest = (
            db.query(models.SiteImage)
            .filter(models.SiteImage.site_id == site.id)
            .order_by(models.SiteImage.fetched_at.desc())
            .first()
        )
        if latest:
            data.append([
                site.name,
                latest.provider,
                str(latest.scene_date) if latest.scene_date else "\u2014",
                str(latest.cloud_cover_pct if latest.cloud_cover_pct is not None else "\u2014"),
                latest.land_cover_summary or "\u2014",
            ])
    if len(data) > 1:
        table = Table(data, hAlign="LEFT")
        table.setStyle(HEADER_STYLE)
        elements.append(table)
    else:
        elements.append(Paragraph("No satellite imagery fetched yet.", styles["BodyText"]))
    elements.append(Spacer(1, 10))
    return elements


SECTION_BUILDERS = {
    "summary": _section_summary,
    "suitability": _section_suitability,
    "solar": _section_solar,
    "wind": _section_wind,
    "financial": _section_financial,
    "environmental": _section_environmental,
    "infrastructure": _section_infrastructure,
    "weather": _section_weather,
    "satellite": _section_satellite,
}


def _build_pdf(project, sites, sections, db, title_suffix=""):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph(f"{project.name} — {title_suffix or 'Site Assessment Report'}", styles["Title"]),
        Spacer(1, 12),
    ]
    for key in sections:
        builder = SECTION_BUILDERS.get(key)
        if builder:
            elements.extend(builder(styles, project, sites, db))
    doc.build(elements)
    buffer.seek(0)
    return buffer


def _get_project_or_404(project_id: int, db: Session) -> models.Project:
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("/projects/{project_id}/reports/custom")
def generate_custom_report(
    project_id: int,
    sections: str,  # comma-separated section keys, e.g. "summary,suitability,solar"
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    project = _get_project_or_404(project_id, db)
    authz.require_project_read(project, current_user)
    section_keys = [s.strip() for s in sections.split(",") if s.strip()]
    invalid = set(section_keys) - set(SECTION_BUILDERS.keys())
    if invalid:
        raise HTTPException(status_code=422, detail=f"Unknown section(s): {sorted(invalid)}")

    sites = db.query(models.Site).filter(models.Site.project_id == project_id).all()
    buffer = _build_pdf(project, sites, section_keys, db, "Custom Report")
    log_action(db, current_user.id, "generate_custom_report", f"project:{project.id}", None)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=custom_report_{project.id}.pdf"},
    )


@router.get("/projects/{project_id}/reports/executive-summary")
def generate_executive_summary(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Fixed, opinionated section set for a concise decision-maker-facing report."""
    project = _get_project_or_404(project_id, db)
    authz.require_project_read(project, current_user)
    sites = db.query(models.Site).filter(models.Site.project_id == project_id).all()
    buffer = _build_pdf(
        project, sites, ["summary", "suitability", "financial"], db, "Executive Summary"
    )
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=executive_summary_{project.id}.pdf"},
    )


@router.get("/projects/{project_id}/reports/from-template/{template_id}")
def generate_report_from_template(
    project_id: int,
    template_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    project = _get_project_or_404(project_id, db)
    authz.require_project_read(project, current_user)
    template = (
        db.query(models.ReportTemplate)
        .filter(models.ReportTemplate.id == template_id, models.ReportTemplate.owner_id == current_user.id)
        .first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Report template not found")

    sites = db.query(models.Site).filter(models.Site.project_id == project_id).all()
    section_keys = template.sections.split(",")
    buffer = _build_pdf(project, sites, section_keys, db, template.name)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={template.name.replace(' ', '_')}_{project.id}.pdf"},
    )
