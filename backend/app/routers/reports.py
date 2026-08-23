import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from app import models, auth, authz
from app.database import get_db
from app.services.score_explanation import explain_suitability_score

router = APIRouter(prefix="/projects/{project_id}/reports", tags=["Reports"])


def _gather_report_rows(db: Session, project_id: int):
    sites = db.query(models.Site).filter(models.Site.project_id == project_id).all()
    rows = []
    for site in sites:
        latest = (
            db.query(models.SuitabilityScore)
            .filter(models.SuitabilityScore.site_id == site.id)
            .order_by(models.SuitabilityScore.computed_at.desc())
            .first()
        )
        rows.append(
            {
                "site": site,
                "name": site.name,
                "latitude": site.latitude,
                "longitude": site.longitude,
                "elevation_m": site.elevation_m,
                "overall_score": latest.overall_score if latest else "N/A",
                "category": latest.category if latest else "Unscored",
                "reasons": explain_suitability_score(db, site, latest) if latest else None,
            }
        )
    return sites, rows


@router.get("/excel")
def export_excel(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    authz.require_project_read(project, current_user)

    _, rows = _gather_report_rows(db, project_id)

    wb = Workbook()
    ws = wb.active
    ws.title = "Site Assessment"
    ws.append(["Site Name", "Latitude", "Longitude", "Elevation (m)", "Suitability Score", "Category", "Reasoning"])
    for row in rows:
        reasoning_text = " | ".join(row["reasons"]) if row["reasons"] else "No score computed yet"
        ws.append(
            [
                row["name"],
                row["latitude"],
                row["longitude"],
                row["elevation_m"],
                row["overall_score"],
                row["category"],
                reasoning_text,
            ]
        )
    ws.column_dimensions["G"].width = 100

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=project-{project_id}-site-assessment.xlsx"},
    )


@router.get("/pdf")
def export_pdf(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    authz.require_project_read(project, current_user)

    _, rows = _gather_report_rows(db, project_id)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph(f"Site Assessment Report \u2014 {project.name}", styles["Title"]),
        Spacer(1, 12),
    ]

    summary_data = [["Site", "Lat / Long", "Elevation (m)", "Score", "Category"]]
    for row in rows:
        summary_data.append(
            [
                row["name"],
                f'{row["latitude"]:.4f}, {row["longitude"]:.4f}',
                str(row["elevation_m"] or "\u2014"),
                str(row["overall_score"]),
                row["category"],
            ]
        )
    summary_table = Table(summary_data, hAlign="LEFT")
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e6f4c")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6f8")]),
            ]
        )
    )
    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    # Per-site reasoning — this is the part that turns "Score: 78.5,
    # Category: Highly Suitable" into an explanation of *why*, by tying
    # each sub-score back to the actual measured data behind it.
    elements.append(Paragraph("Why Each Site Scored the Way It Did", styles["Heading2"]))
    elements.append(Spacer(1, 8))
    for row in rows:
        elements.append(Paragraph(f"{row['name']} \u2014 {row['overall_score']} ({row['category']})", styles["Heading3"]))
        if row["reasons"]:
            for reason in row["reasons"]:
                elements.append(Paragraph(f"\u2022 {reason}", styles["BodyText"]))
        else:
            elements.append(Paragraph("No suitability score has been computed for this site yet \u2014 register or refresh it to generate one.", styles["BodyText"]))
        elements.append(Spacer(1, 10))

    doc.build(elements)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=project-{project_id}-site-assessment.pdf"},
    )
