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
      T2M               -> temperature at 2m (deg C)
      PRECTOTCORR       -> precipitation (mm/day)
      CLOUD_AMT         -> cloud cover (%)
    """
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=days_back)

    params = {
        "parameters": "ALLSKY_SFC_SW_DWN,WS10M,WS50M,T2M,PRECTOTCORR,CLOUD_AMT",
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
    temp = daily.get("T2M", {})
    rain = daily.get("PRECTOTCORR", {})
    cloud = daily.get("CLOUD_AMT", {})

    fetched_count = 0
    for date_str in irradiance.keys():
        reading_date = datetime.datetime.strptime(date_str, "%Y%m%d")

        # Skip if we already have a reading for this site/date
        existing = (
            db.query(models.WeatherReading)
            .filter(
                models.WeatherReading.site_id == site.id,
                models.WeatherReading.reading_date == reading_date,
            )
            .first()
        )
        if existing:
            continue

        reading = models.WeatherReading(
            site_id=site.id,
            reading_date=reading_date,
            solar_irradiance=irradiance.get(date_str),
            wind_speed=wind.get(date_str),
            wind_speed_50m=wind_50m.get(date_str),
            temperature=temp.get(date_str),
            rainfall=rain.get(date_str),
            cloud_cover_pct=cloud.get(date_str),
        )
        db.add(reading)
        fetched_count += 1

    db.commit()
    return fetched_count
