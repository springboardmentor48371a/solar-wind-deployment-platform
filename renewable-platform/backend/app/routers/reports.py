"""
Module 13 & Section 22: Downloadable Reports & Export System.
Provides JSON, PDF, and Excel export endpoints for site and project evaluations.
"""
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..auth import get_current_user
from ..routers.sites import _build_site_detail
from ..services import report_generator

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/site/{site_id}")
def site_report(site_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    site = db.query(models.Site).filter(models.Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    detail = _build_site_detail(site)
    return {
        "report_type": "Site Assessment / Feasibility / Investment Report",
        "generated_for": site.name,
        "data": detail.model_dump(),
    }


@router.get("/site/{site_id}/pdf")
def download_site_pdf(site_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    site = db.query(models.Site).filter(models.Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    detail = _build_site_detail(site)
    pdf_bytes = report_generator.generate_site_pdf_report(detail.model_dump())
    filename = f"site_assessment_{site_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/site/{site_id}/excel")
def download_site_excel(site_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    site = db.query(models.Site).filter(models.Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    detail = _build_site_detail(site)
    excel_bytes = report_generator.generate_site_excel_report(detail.model_dump())
    filename = f"site_assessment_{site_id}.xlsx"
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/project/{project_id}")
def project_report(project_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    sites_data = [_build_site_detail(s).model_dump() for s in project.sites]
    return {
        "report_type": "Deployment Recommendation Report",
        "project": project.name,
        "site_count": len(sites_data),
        "sites": sites_data,
    }
