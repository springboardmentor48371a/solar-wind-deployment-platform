import os
import httpx
from fastapi import APIRouter, Depends, HTTPException
from ..models.user import User
from ..core.dependencies import get_current_user
from ..services.infrastructure import fetch_infrastructure_score

ML_SERVICE = os.getenv("ML_SERVICE_URL", "http://ml-service:8001")

router = APIRouter(prefix="/predictions", tags=["Predictions"])

@router.get("/{site_id}")
async def get_prediction(site_id: int, _: User = Depends(get_current_user)):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{ML_SERVICE}/predict/{site_id}")
    if r.status_code == 404:
        raise HTTPException(status_code=404, detail="No predictions yet for this site")
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail="ML service error")
    return r.json()

@router.post("/{site_id}/run")
async def run_prediction(site_id: int, _: User = Depends(get_current_user)):
    from ..database import SessionLocal
    from ..models.site import Site
    db = SessionLocal()
    try:
        site = db.query(Site).filter(Site.id == site_id).first()
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")
        lat, lon = site.latitude, site.longitude
        land_ownership = site.land_ownership.value if site.land_ownership else None
    finally:
        db.close()

    infra = await fetch_infrastructure_score(lat, lon)

    payload = {
        "site_id": site_id,
        "latitude": lat,
        "longitude": lon,
        "elevation": site.elevation,
        "energy_type": site.energy_type.value,
        "land_ownership": land_ownership,
        "infrastructure_score": infra["infrastructure_score"],
    }

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(f"{ML_SERVICE}/predict/all", json=payload)
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=r.text)
    return r.json()
