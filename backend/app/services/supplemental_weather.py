"""
Supplemental weather — OpenWeather (live current conditions, global) and
NOAA (short-range forecast, US only), the two additional "Weather &
Climate APIs" from the architecture diagram beyond NASA POWER.

Both are genuinely real-time: OpenWeather returns the current observed
conditions at the moment of the call, and NOAA returns the National
Weather Service's live forecast for that point — not archival/historical
data like NASA POWER. Same graceful-degradation pattern as every other
connector here: missing API key / non-US coordinates / upstream failure
all produce a clean None, never an exception the caller has to guard
against.
"""

import requests
from sqlalchemy.orm import Session

from app.cache import cache_get, cache_set
from app.config import settings
from app import models
from app import mongo
from app import data_lake


def fetch_openweather_current(db: Session, site: models.Site) -> models.SupplementalWeatherReading | None:
    """Current live conditions from OpenWeather. Requires OPENWEATHER_API_KEY."""
    if not settings.openweather_api_key:
        return None

    cache_key = f"openweather:{round(site.latitude, 3)}:{round(site.longitude, 3)}"
    payload = cache_get(cache_key)
    if payload is None:
        response = requests.get(
            settings.openweather_base_url,
            params={
                "lat": site.latitude,
                "lon": site.longitude,
                "appid": settings.openweather_api_key,
                "units": "metric",
            },
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        cache_set(cache_key, payload, ttl_seconds=600)  # live data — short TTL, not the week-long ones used elsewhere

    mongo.store_raw_payload("weather_raw", site.id, "OPENWEATHER", payload)
    data_lake.archive_payload("weather_raw", site.id, "OPENWEATHER", payload)

    reading = models.SupplementalWeatherReading(
        site_id=site.id,
        source="OPENWEATHER",
        temperature_c=payload.get("main", {}).get("temp"),
        wind_speed_ms=payload.get("wind", {}).get("speed"),
        cloud_cover_pct=payload.get("clouds", {}).get("all"),
        condition_text=(payload.get("weather") or [{}])[0].get("description"),
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading


def fetch_noaa_forecast(db: Session, site: models.Site) -> models.SupplementalWeatherReading | None:
    """
    NOAA/National Weather Service forecast — US coverage only. Two-step
    API: resolve lat/lon to a forecast office + grid cell via /points,
    then fetch that grid cell's forecast. Returns None outside the US
    (NOAA's own 404 for out-of-coverage points) rather than raising.
    """
    cache_key = f"noaa:points:{round(site.latitude, 4)}:{round(site.longitude, 4)}"
    points_payload = cache_get(cache_key)
    if points_payload is None:
        try:
            points_resp = requests.get(
                f"{settings.noaa_base_url}/{site.latitude},{site.longitude}",
                headers={"User-Agent": "SolsticeOS (solar-wind-deployment-intelligence)"},
                timeout=15,
            )
            if points_resp.status_code == 404:
                return None  # outside NOAA/NWS coverage (non-US)
            points_resp.raise_for_status()
            points_payload = points_resp.json()
            cache_set(cache_key, points_payload, ttl_seconds=24 * 60 * 60)
        except requests.RequestException:
            return None

    forecast_url = points_payload.get("properties", {}).get("forecast")
    if not forecast_url:
        return None

    forecast_cache_key = f"noaa:forecast:{forecast_url}"
    forecast_payload = cache_get(forecast_cache_key)
    if forecast_payload is None:
        try:
            forecast_resp = requests.get(
                forecast_url, headers={"User-Agent": "SolsticeOS (solar-wind-deployment-intelligence)"}, timeout=15
            )
            forecast_resp.raise_for_status()
            forecast_payload = forecast_resp.json()
            cache_set(forecast_cache_key, forecast_payload, ttl_seconds=3 * 60 * 60)
        except requests.RequestException:
            return None

    mongo.store_raw_payload("weather_raw", site.id, "NOAA_FORECAST", forecast_payload)
    data_lake.archive_payload("weather_raw", site.id, "NOAA_FORECAST", forecast_payload)

    periods = forecast_payload.get("properties", {}).get("periods", [])
    if not periods:
        return None
    period = periods[0]

    reading = models.SupplementalWeatherReading(
        site_id=site.id,
        source="NOAA_FORECAST",
        temperature_c=(
            round((period["temperature"] - 32) * 5 / 9, 1)
            if period.get("temperatureUnit") == "F" and period.get("temperature") is not None
            else period.get("temperature")
        ),
        wind_speed_ms=_parse_noaa_wind_speed(period.get("windSpeed")),
        condition_text=period.get("shortForecast"),
        forecast_period=period.get("name"),
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading


def _parse_noaa_wind_speed(wind_speed_str: str | None) -> float | None:
    """NOAA returns wind speed as a string like '10 mph' or '5 to 10 mph' — take the first number, convert to m/s."""
    if not wind_speed_str:
        return None
    try:
        first_number = float(wind_speed_str.split()[0])
        return round(first_number * 0.44704, 2)  # mph -> m/s
    except (ValueError, IndexError):
        return None


def fetch_and_store_supplemental_weather(db: Session, site: models.Site) -> list[models.SupplementalWeatherReading]:
    """Runs both connectors best-effort and returns whichever succeeded."""
    from app.services.data_source_overrides import is_disabled

    results = []
    if is_disabled(db, "OpenWeather"):
        print(f"Info: OpenWeather is manually paused by an administrator — skipping for site {site.id}")
    else:
        try:
            ow = fetch_openweather_current(db, site)
            if ow:
                results.append(ow)
        except Exception as exc:  # noqa: BLE001
            print(f"Warning: OpenWeather fetch failed for site {site.id}: {exc}")

    if is_disabled(db, "NOAA / National Weather Service"):
        print(f"Info: NOAA is manually paused by an administrator — skipping for site {site.id}")
    else:
        try:
            noaa = fetch_noaa_forecast(db, site)
            if noaa:
                results.append(noaa)
        except Exception as exc:  # noqa: BLE001
            print(f"Warning: NOAA forecast fetch failed for site {site.id}: {exc}")

    return results
