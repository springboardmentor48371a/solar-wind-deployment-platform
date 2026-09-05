from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List

from ..database import get_db
from ..models import SitePrediction, EnergyForecast, LandCover
from ..schemas.predict import PredictRequest, SitePredictionResponse, EnergyForecastResponse, LandCoverResponse
from ..services import solar, wind, land_cover, suitability, forecast

router = APIRouter(prefix="/predict", tags=["Predictions"])

def get_env_summary(db: Session, site_id: int) -> dict:
    """Fetch averaged environmental data for a site from the shared DB."""
    row = db.execute(text("""
        SELECT
            AVG(solar_irradiance)   AS solar_irradiance,
            AVG(peak_sun_hours)     AS peak_sun_hours,
            AVG(wind_speed)         AS wind_speed,
            AVG(wind_speed_50m)     AS wind_speed_50m,
            AVG(wind_direction)     AS wind_direction,
            AVG(temperature_avg)    AS temperature_avg,
            AVG(cloud_cover)        AS cloud_cover,
            AVG(humidity)           AS humidity,
            AVG(elevation)          AS elevation,
            AVG(vegetation_index)   AS vegetation_index,
            AVG(land_slope)         AS land_slope,
            AVG(aspect_deg)         AS aspect_deg
        FROM environmental_data
        WHERE site_id = :site_id
    """), {"site_id": site_id}).fetchone()
    return dict(row._mapping) if row else {}

def get_historical_series(db: Session, site_id: int) -> tuple[list, list]:
    """Fetch ordered daily solar and wind values for forecasting."""
    rows = db.execute(text("""
        SELECT solar_irradiance, wind_speed
        FROM environmental_data
        WHERE site_id = :site_id
        ORDER BY date ASC
    """), {"site_id": site_id}).fetchall()
    solar_vals = [r[0] or 0.0 for r in rows]
    wind_vals  = [r[1] or 0.0 for r in rows]
    return solar_vals, wind_vals

@router.post("/all", response_model=SitePredictionResponse)
def predict_all(payload: PredictRequest, db: Session = Depends(get_db)):
    """Run all models for a site and store results. Called automatically on site creation."""
    env = get_env_summary(db, payload.site_id)
    if not env:
        raise HTTPException(status_code=404, detail="No environmental data found for this site. Collect env data first.")

    # Solar
    solar_result = solar.predict_solar(
        solar_irradiance=env.get("solar_irradiance") or 0.0,
        temperature_avg=env.get("temperature_avg") or 25.0,
        cloud_cover=env.get("cloud_cover") or 0.0,
        peak_sun_hours=env.get("peak_sun_hours") or 0.0,
    )

    # Wind
    wind_result = wind.predict_wind(
        wind_speed=env.get("wind_speed") or 0.0,
        wind_direction=env.get("wind_direction") or 0.0,
        temperature_avg=env.get("temperature_avg") or 25.0,
    )

    # Land cover — use real NDVI and slope from environmental_data
    ndvi      = env.get("vegetation_index") or 0.3
    slope_deg = env.get("land_slope") or 2.0
    lc_result = land_cover.predict_land_cover(
        ndvi=ndvi,
        slope_deg=slope_deg,
        elevation=env.get("elevation") or 0.0,
    )

    # Save land cover separately
    existing_lc = db.query(LandCover).filter(LandCover.site_id == payload.site_id).first()
    if existing_lc:
        for k, v in lc_result.items():
            if hasattr(existing_lc, k):
                setattr(existing_lc, k, v)
    else:
        db.add(LandCover(site_id=payload.site_id, **{k: v for k, v in lc_result.items() if k != "land_cover_score"}))

    # Infrastructure score — computed in backend (has internet), passed in payload
    infra_score = payload.infrastructure_score

    # Suitability
    suit_result = suitability.predict_suitability(
        solar_score=solar_result.get("solar_score"),
        wind_score=wind_result.get("wind_score"),
        land_cover_score=lc_result.get("land_cover_score"),
        elevation=env.get("elevation"),
        energy_type=payload.energy_type,
        infrastructure_score=infra_score,
        land_ownership=payload.land_ownership,
        slope_deg=env.get("land_slope"),
        aspect_deg=env.get("aspect_deg"),
    )

    # Upsert site prediction
    existing = db.query(SitePrediction).filter(SitePrediction.site_id == payload.site_id).first()
    data = {**solar_result, **wind_result, **suit_result,
            "land_cover_class": lc_result.get("cover_class"),
            "vegetation_index": lc_result.get("ndvi"),
            "land_slope": lc_result.get("slope_deg"),
            "land_cover_score": lc_result.get("land_cover_score")}

    if existing:
        for k, v in data.items():
            setattr(existing, k, v)
        prediction = existing
    else:
        prediction = SitePrediction(site_id=payload.site_id, **data)
        db.add(prediction)

    db.commit()
    db.refresh(prediction)

    # Forecast
    solar_series, wind_series = get_historical_series(db, payload.site_id)
    if solar_series:
        forecasts = forecast.predict_forecast(solar_series, wind_series, days_ahead=30)
        db.query(EnergyForecast).filter(EnergyForecast.site_id == payload.site_id).delete()
        for f in forecasts:
            db.add(EnergyForecast(site_id=payload.site_id, **f))
        db.commit()

    return prediction

@router.get("/{site_id}", response_model=SitePredictionResponse)
def get_prediction(site_id: int, db: Session = Depends(get_db)):
    pred = db.query(SitePrediction).filter(SitePrediction.site_id == site_id).first()
    if not pred:
        raise HTTPException(status_code=404, detail="No predictions found for this site")
    return pred

@router.get("/{site_id}/forecast", response_model=List[EnergyForecastResponse])
def get_forecast(site_id: int, db: Session = Depends(get_db)):
    return db.query(EnergyForecast).filter(EnergyForecast.site_id == site_id).order_by(EnergyForecast.forecast_date).all()

@router.get("/{site_id}/land-cover", response_model=LandCoverResponse)
def get_land_cover(site_id: int, db: Session = Depends(get_db)):
    lc = db.query(LandCover).filter(LandCover.site_id == site_id).first()
    if not lc:
        raise HTTPException(status_code=404, detail="No land cover data found for this site")
    return lc
