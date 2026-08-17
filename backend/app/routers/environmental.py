from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import date, timedelta

from ..database import get_db
from ..models.environmental import EnvironmentalData
from ..models.site import Site
from ..models.user import User
from ..schemas.environmental import EnvironmentalDataResponse, EnvironmentalSummary
from ..services.environmental import collect_environmental_data
from ..core.dependencies import get_current_user

router = APIRouter(prefix="/environmental", tags=["Environmental Data"])

@router.post("/{site_id}/collect", response_model=dict)
async def collect_data(
    site_id: int,
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user)
):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    # Check if we already have recent data (within 24hrs) — avoid redundant API calls
    from datetime import datetime
    recent = db.query(EnvironmentalData).filter(
        EnvironmentalData.site_id == site_id,
        EnvironmentalData.fetched_at >= datetime.utcnow() - timedelta(hours=24)
    ).first()
    if recent:
        return {"message": "Data already up to date", "site_id": site_id}

    records = await collect_environmental_data(site.latitude, site.longitude, days)

    # Delete old records for this site before inserting fresh ones
    db.query(EnvironmentalData).filter(EnvironmentalData.site_id == site_id).delete()

    for r in records:
        db.add(EnvironmentalData(site_id=site_id, **r))

    db.commit()
    return {"message": f"Collected {len(records)} days of data", "site_id": site_id}

@router.get("/{site_id}", response_model=List[EnvironmentalDataResponse])
def get_environmental_data(
    site_id: int,
    start_date: date = Query(default=None),
    end_date: date = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user)
):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    q = db.query(EnvironmentalData).filter(EnvironmentalData.site_id == site_id)
    if start_date:
        q = q.filter(EnvironmentalData.date >= start_date)
    if end_date:
        q = q.filter(EnvironmentalData.date <= end_date)

    return q.order_by(EnvironmentalData.date.desc()).all()

@router.get("/{site_id}/summary", response_model=EnvironmentalSummary)
def get_summary(site_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    def avg(col): return db.query(func.avg(col)).filter(EnvironmentalData.site_id == site_id).scalar()
    def total(col): return db.query(func.sum(col)).filter(EnvironmentalData.site_id == site_id).scalar()
    count = db.query(func.count(EnvironmentalData.id)).filter(EnvironmentalData.site_id == site_id).scalar()

    elev = db.query(EnvironmentalData.elevation).filter(
        EnvironmentalData.site_id == site_id,
        EnvironmentalData.elevation.isnot(None)
    ).first()

    def r(val): return round(val, 2) if val else None

    return EnvironmentalSummary(
        site_id=site_id,
        total_days=count,
        avg_solar_irradiance=r(avg(EnvironmentalData.solar_irradiance)),
        avg_peak_sun_hours=r(avg(EnvironmentalData.peak_sun_hours)),
        avg_wind_speed=r(avg(EnvironmentalData.wind_speed)),
        avg_wind_speed_50m=r(avg(EnvironmentalData.wind_speed_50m)),
        avg_temperature=r(avg(EnvironmentalData.temperature_avg)),
        total_rainfall=r(total(EnvironmentalData.rainfall)),
        avg_cloud_cover=r(avg(EnvironmentalData.cloud_cover)),
        avg_humidity=r(avg(EnvironmentalData.humidity)),
        elevation=elev[0] if elev else None,
    )
