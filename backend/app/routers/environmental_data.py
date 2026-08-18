import uuid
from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.environmental_data import EnvironmentalData
from app.models.site import Site
from app.models.user import User
from app.schemas.environmental_data import (
    EnvironmentalDataCollectResponse,
    EnvironmentalDataCreate,
    EnvironmentalDataResponse,
)
from app.services.environmental_data_service import (
    EnvironmentalDataError,
    EnvironmentalDataService,
)

router = APIRouter(tags=["Environmental Data"])


def get_site_or_404(site_id: uuid.UUID, db: Session) -> Site:
    site = db.query(Site).filter(Site.site_id == site_id).first()
    if site is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found.",
        )
    return site


def get_environmental_data_or_404(
    environment_id: uuid.UUID,
    db: Session,
) -> EnvironmentalData:
    record = (
        db.query(EnvironmentalData)
        .filter(EnvironmentalData.environment_id == environment_id)
        .first()
    )
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Environmental data record not found.",
        )
    return record


def serialize_record(
    record: EnvironmentalData,
    data_sources: dict[str, str] | None = None,
) -> EnvironmentalDataResponse | EnvironmentalDataCollectResponse:
    payload = {
        "environment_id": record.environment_id,
        "site_id": record.site_id,
        "solar_irradiance": record.solar_irradiance,
        "wind_speed": record.wind_speed,
        "wind_direction": record.wind_direction,
        "temperature": record.temperature,
        "rainfall": record.rainfall,
        "humidity": record.humidity,
        "cloud_cover": record.cloud_cover,
        "terrain_slope": record.terrain_slope,
        "vegetation_index": record.vegetation_index,
        "nearest_substation_distance": record.nearest_substation_distance,
        "road_distance": record.road_distance,
        "protected_area": record.protected_area,
        "collected_at": record.collected_at,
    }
    if data_sources is not None:
        payload["data_sources"] = data_sources
        return EnvironmentalDataCollectResponse(**payload)
    return EnvironmentalDataResponse(**payload)


@router.get(
    "/sites/{site_id}/environmental-data",
    response_model=list[EnvironmentalDataResponse],
)
def list_site_environmental_data(
    site_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_site_or_404(site_id, db)
    records = (
        db.query(EnvironmentalData)
        .filter(EnvironmentalData.site_id == site_id)
        .order_by(EnvironmentalData.collected_at.desc())
        .all()
    )
    return [serialize_record(record) for record in records]


@router.post(
    "/sites/{site_id}/environmental-data",
    response_model=EnvironmentalDataResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_site_environmental_data(
    site_id: uuid.UUID,
    environmental_data: EnvironmentalDataCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_site_or_404(site_id, db)
    payload = environmental_data.model_dump(exclude={"collected_at"})
    record = EnvironmentalData(site_id=site_id, **payload)

    if environmental_data.collected_at is not None:
        record.collected_at = environmental_data.collected_at.astimezone(timezone.utc)

    db.add(record)
    db.commit()
    db.refresh(record)
    return serialize_record(record)


@router.post(
    "/sites/{site_id}/environmental-data/collect",
    response_model=EnvironmentalDataCollectResponse,
    status_code=status.HTTP_201_CREATED,
)
def collect_site_environmental_data(
    site_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    site = get_site_or_404(site_id, db)
    service = EnvironmentalDataService()

    try:
        payload, data_sources = service.collect_for_site(site.latitude, site.longitude)
    except EnvironmentalDataError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error

    record = EnvironmentalData(site_id=site_id, **payload)
    db.add(record)
    db.commit()
    db.refresh(record)

    return serialize_record(record, data_sources=data_sources)


@router.get(
    "/environmental-data/{environment_id}",
    response_model=EnvironmentalDataResponse,
)
def get_environmental_data(
    environment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = get_environmental_data_or_404(environment_id, db)
    return serialize_record(record)
