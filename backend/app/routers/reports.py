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
                "name": site.name,
                "latitude": site.latitude,
                "longitude": site.longitude,
                "elevation_m": site.elevation_m,
                "overall_score": latest.overall_score if latest else "N/A",
                "category": latest.category if latest else "Unscored",
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
    ws.append(["Site Name", "Latitude", "Longitude", "Elevation (m)", "Suitability Score", "Category"])
    for row in rows:
        ws.append(
            [
                row["name"],
                row["latitude"],
                row["longitude"],
                row["elevation_m"],
                row["overall_score"],
                row["category"],
            ]
        )

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
        Paragraph(f"Site Assessment Report — {project.name}", styles["Title"]),
        Spacer(1, 12),
    ]

    table_data = [["Site", "Lat / Long", "Elevation (m)", "Score", "Category"]]
    for row in rows:
        table_data.append(
            [
                row["name"],
                f'{row["latitude"]:.4f}, {row["longitude"]:.4f}',
                str(row["elevation_m"] or "\u2014"),
                str(row["overall_score"]),
                row["category"],
            ]
        )

    table = Table(table_data, hAlign="LEFT")
    table.setStyle(
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
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=project-{project_id}-site-assessment.pdf"},
    )
