import httpx
from fastapi import APIRouter, Depends, HTTPException
from ..models.user import User
from ..core.dependencies import get_current_user

ML_SERVICE = "http://ml-service:8001"

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
    """Manually trigger predictions for a site (re-runs all models)."""
    from ..database import SessionLocal
    from ..models.site import Site
    db = SessionLocal()
    try:
        site = db.query(Site).filter(Site.id == site_id).first()
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")
        payload = {
            "site_id": site.id,
            "latitude": site.latitude,
            "longitude": site.longitude,
            "elevation": site.elevation,
            "energy_type": site.energy_type.value,
        }
    finally:
        db.close()

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(f"{ML_SERVICE}/predict/all", json=payload)
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=r.text)
    return r.json()
