"""
Shared helper for the manual data-source pause/resume feature (Admin
Dashboard's "Data source management"). Kept as its own tiny module
rather than living inside routers/data_sources.py, since every external
connector (environmental.py, infrastructure.py, satellite.py,
land_data.py, supplemental_weather.py) needs to check this — importing
from a router module into service modules would risk a circular import.
"""

from sqlalchemy.orm import Session

from app import models


def is_disabled(db: Session, source_name: str) -> bool:
    """Returns True if an Administrator has manually paused this connector."""
    override = (
        db.query(models.DataSourceOverride)
        .filter(models.DataSourceOverride.source_name == source_name, models.DataSourceOverride.manually_disabled == 1)
        .first()
    )
    return override is not None
