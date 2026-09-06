"""
Environmental Data Collection Engine (simplified).

Per the Data Flow Workflow doc: this pulls from NASA POWER for weather/climate
data and stores it into the Weather_Readings time-series table. Terrain
(NASA SRTM), roads/infra (OpenStreetMap), and land cover (Copernicus Sentinel)
connectors follow the same pattern and can be added as sibling functions here
once Milestone 2 begins.
"""

import datetime

import requests
from sqlalchemy.orm import Session

from app.cache import cache_get, cache_set
from app.config import settings
from app import models
from app import mongo
from app import data_lake


_FIELD_BOUNDS = {
    "solar_irradiance": (0, 15),      # kWh/m^2/day — 0 to ~15 covers even the most extreme real-world sites
    "wind_speed": (0, 120),            # m/s — generously covers even extreme storm readings
    "wind_speed_50m": (0, 120),
    "wind_direction_deg": (0, 360),
    "temperature": (-90, 60),          # deg C — widest recorded surface temps on Earth
    "rainfall": (0, 1000),             # mm/day — generous upper bound for extreme storm days
    "cloud_cover_pct": (0, 100),
}


def _valid_reading(value, min_val: float, max_val: float):
    """
    NASA POWER (and most scientific weather APIs) use -999 as a "no data
    for this day" fill value rather than omitting the key entirely — this
    codebase was previously storing that literal -999 as if it were a
    real reading, which corrupted every downstream average (solar/wind
    potential, suitability score) whenever a single day had a data gap.
    Rejects the -999 family of sentinels plus anything outside a
    physically plausible range for the parameter, storing None instead so
    every existing `is not None` filter throughout the codebase (scoring.py,
    solar_engine.py, wind_engine.py) already handles it correctly as
    "no data for this day" rather than "measured value of -999."
    """
    if value is None:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    if value <= -900:  # covers -999, -999.0, -99900 (scaled variants some datasets use)
        return None
    if value < min_val or value > max_val:
        return None
    return value


def fetch_and_store_weather_data(db: Session, site: models.Site, days_back: int = 7) -> None:
    """
    Fetch recent daily weather data from the NASA POWER API for a site's
    coordinates and persist it into Weather_Readings.

    NASA POWER parameters used:
      ALLSKY_SFC_SW_DWN -> solar irradiance (kWh/m^2/day)
      WS10M             -> wind speed at 10m / surface (m/s)
      WS50M             -> wind speed at 50m — the Wind Potential Service's
                            real input, since that's much closer to actual
                            turbine hub height than a 10m surface reading
      WD50M             -> wind direction at 50m (degrees, 0-360) — a named
                            Environmental Factor in the project spec that
                            was missing entirely until this pass, even
                            though it's the same free API call already
                            being made for every other wind parameter
      T2M               -> temperature at 2m (deg C)
      PRECTOTCORR       -> precipitation (mm/day)
      CLOUD_AMT         -> cloud cover (%)
    """
    from app.services.data_source_overrides import is_disabled
    if is_disabled(db, "NASA POWER"):
        print(f"Info: NASA POWER is manually paused by an administrator — skipping weather fetch for site {site.id}")
        return

    # Real bug found via live testing and confirmed against NASA's own
    # documentation: solar irradiance (ALLSKY_SFC_SW_DWN) comes from a
    # completely different processing pipeline (CERES/FLASHFlux) than
    # the meteorological parameters below it (T2M/PRECTOTCORR/CLOUD_AMT,
    # from MERRA-2) — and NASA's own docs state the solar "low latency"
    # product has a 5-7 day processing lag under normal conditions, with
    # NASA's own forum confirming an additional active delay beyond
    # that as of this writing. Querying all the way up to today (the
    # old behavior) meant the most recent several days were requested
    # before irradiance had actually been computed for them, while the
    # much-faster meteorological parameters for those same recent days
    # were already available — explaining exactly the reported pattern
    # (temperature/rainfall/cloud always populate, irradiance never
    # does, for the same site, every time). Shifting the whole window
    # back by a safety buffer keeps it well within NASA's confirmed
    # processing latency for every parameter requested, not just the
    # fast ones.
    IRRADIANCE_PROCESSING_LAG_DAYS = 10
    end_date = datetime.date.today() - datetime.timedelta(days=IRRADIANCE_PROCESSING_LAG_DAYS)
    start_date = end_date - datetime.timedelta(days=days_back)

    params = {
        "parameters": "ALLSKY_SFC_SW_DWN,WS10M,WS50M,WD50M,T2M,PRECTOTCORR,CLOUD_AMT",
        "community": "RE",
        "longitude": site.longitude,
        "latitude": site.latitude,
        "start": start_date.strftime("%Y%m%d"),
        "end": end_date.strftime("%Y%m%d"),
        "format": "JSON",
    }

    # NASA POWER responses for the same site+date-range are identical on
    # repeat calls within the caching window, so a same-day re-run (e.g.
    # the user refreshing a dashboard) hits Redis instead of the public
    # API. Cache key includes the date range so tomorrow's fetch naturally
    # misses and pulls fresh data.
    cache_key = (
        f"weather:nasa_power:{round(site.latitude, 4)}:{round(site.longitude, 4)}:"
        f"{start_date.isoformat()}:{end_date.isoformat()}"
    )
    payload = cache_get(cache_key)
    if payload is None:
        response = requests.get(settings.nasa_power_base_url, params=params, timeout=15)
        response.raise_for_status()
        payload = response.json()
        cache_set(cache_key, payload, ttl_seconds=6 * 60 * 60)  # 6h — weather is not static

    # Archive the full raw response to MongoDB (secondary database) before
    # any parsing, so the exact upstream payload is reprocessable later.
    mongo.store_raw_payload("weather_raw", site.id, "NASA_POWER", payload)
    data_lake.archive_payload("weather_raw", site.id, "NASA_POWER", payload)

    daily = payload.get("properties", {}).get("parameter", {})
    irradiance = daily.get("ALLSKY_SFC_SW_DWN", {})
    wind = daily.get("WS10M", {})
    wind_50m = daily.get("WS50M", {})
    wind_direction = daily.get("WD50M", {})
    temp = daily.get("T2M", {})
    rain = daily.get("PRECTOTCORR", {})
    cloud = daily.get("CLOUD_AMT", {})

    fetched_count = 0
    repaired_count = 0
    # Real, significant bug found via live testing: this used to
    # iterate over irradiance.keys() specifically, meaning if
    # irradiance had zero data for the entire requested window (a real,
    # recurring issue — see the processing-lag fix and comment above),
    # the loop ran zero times and NOTHING got stored at all, not just
    # missing irradiance — even if NASA had perfectly good temperature/
    # rainfall/cloud/wind data for those same dates. Iterating over the
    # union of every parameter's own dates means a gap in any one
    # parameter can never block the others from being stored.
    all_dates = set(irradiance.keys()) | set(wind.keys()) | set(wind_50m.keys()) | set(wind_direction.keys()) | set(temp.keys()) | set(rain.keys()) | set(cloud.keys())
    for date_str in sorted(all_dates):
        reading_date = datetime.datetime.strptime(date_str, "%Y%m%d")

        fresh_values = {
            "solar_irradiance": _valid_reading(irradiance.get(date_str), 0, 15),
            "wind_speed": _valid_reading(wind.get(date_str), 0, 120),
            "wind_speed_50m": _valid_reading(wind_50m.get(date_str), 0, 120),
            "wind_direction_deg": _valid_reading(wind_direction.get(date_str), 0, 360),
            "temperature": _valid_reading(temp.get(date_str), -90, 60),
            "rainfall": _valid_reading(rain.get(date_str), 0, 1000),
            "cloud_cover_pct": _valid_reading(cloud.get(date_str), 0, 100),
        }

        existing = (
            db.query(models.WeatherReading)
            .filter(
                models.WeatherReading.site_id == site.id,
                models.WeatherReading.reading_date == reading_date,
            )
            .first()
        )
        if existing:
            # Self-healing repair: a row stored before the sentinel-value
            # fix above may still hold a raw, invalid value (e.g. a
            # literal -999) in a column that's supposed to be None. Re-run
            # the same validity check against what's *currently stored*
            # and overwrite only the columns that fail it — this means
            # simply clicking "Refresh data" repairs old corrupted rows
            # without the user needing to delete and re-register the site.
            for field, fresh_value in fresh_values.items():
                stored_value = getattr(existing, field)
                if stored_value is not None and _valid_reading(stored_value, *_FIELD_BOUNDS[field]) is None:
                    setattr(existing, field, fresh_value)
                    repaired_count += 1
            continue

        reading = models.WeatherReading(
            site_id=site.id,
            reading_date=reading_date,
            **fresh_values,
        )
        db.add(reading)
        fetched_count += 1

    db.commit()
    if repaired_count:
        print(f"Info: repaired {repaired_count} previously-corrupted weather field(s) for site {site.id}")
    return fetched_count


def fetch_seasonal_climatology(site: models.Site) -> dict | None:
    """
    Seasonal Generation Prediction — a genuinely different NASA POWER
    endpoint from fetch_and_store_weather_data's daily one: the
    /temporal/climatology/point endpoint returns long-term monthly
    averages (JAN-DEC) computed from decades of historical data, rather
    than a short recent window. Used to redistribute an already-computed
    annual output figure into a monthly shape, not to compute a new
    annual estimate — solar_engine.py/wind_engine.py's daily-driven
    annual figures remain the source of truth for the yearly total.
    """
    cache_key = f"nasa_power_climatology:{round(site.latitude, 3)}:{round(site.longitude, 3)}"
    payload = cache_get(cache_key)
    if payload is None:
        try:
            response = requests.get(
                "https://power.larc.nasa.gov/api/temporal/climatology/point",
                params={
                    "parameters": "ALLSKY_SFC_SW_DWN,WS50M",
                    "community": "RE",
                    "longitude": site.longitude,
                    "latitude": site.latitude,
                    "format": "JSON",
                },
                timeout=15,
            )
            response.raise_for_status()
            payload = response.json()
            cache_set(cache_key, payload, ttl_seconds=90 * 24 * 60 * 60)  # climatology is long-term, safe to cache for months
        except Exception as exc:  # noqa: BLE001
            print(f"Warning: NASA POWER climatology fetch failed for site {site.id}: {exc}")
            return None

    try:
        params = payload["properties"]["parameter"]
        irradiance_by_month = params.get("ALLSKY_SFC_SW_DWN", {})
        months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
        monthly_values = {}
        for m in months:
            v = irradiance_by_month.get(m)
            if v is not None and -900 < v < 15:  # same sentinel/plausibility guard as the daily fetch
                monthly_values[m] = v
        return monthly_values or None
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: could not parse NASA POWER climatology response for site {site.id}: {exc}")
        return None


def distribute_annual_output_by_month(annual_output_mwh: float, monthly_irradiance: dict) -> dict:
    """
    Splits an already-computed annual output figure across 12 months in
    proportion to each month's share of total climatological irradiance
    — e.g. a month with 10% of the year's irradiance gets ~10% of the
    annual output, not an equal 1/12th share. This is a redistribution
    of an existing number, not a new independent prediction.
    """
    total = sum(monthly_irradiance.values())
    if total <= 0:
        return {}
    return {month: round(annual_output_mwh * (value / total), 1) for month, value in monthly_irradiance.items()}
