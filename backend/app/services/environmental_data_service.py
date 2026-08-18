from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


# NASA POWER daily point parameters normalized into the mentor-defined schema.
# External parameter -> internal field -> stored unit.
NASA_POWER_MAPPINGS = {
    "ALLSKY_SFC_SW_DWN": ("solar_irradiance", "kWh/m2/day"),
    "T2M": ("temperature", "deg C"),
    "PRECTOTCORR": ("rainfall", "mm/day"),
    "RH2M": ("humidity", "%"),
    "CLOUD_AMT": ("cloud_cover", "%"),
}

MISSING_SENTINELS = {-999, -999.0, -9999, -9999.0}


class EnvironmentalDataError(Exception):
    pass


class ProviderUnavailableError(EnvironmentalDataError):
    pass


class ProviderResponseError(EnvironmentalDataError):
    pass


@dataclass
class ProviderResult:
    name: str
    values: dict[str, float | bool | None]
    status: str


class NasaPowerProvider:
    name = "NASA POWER"
    base_url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    parameters = tuple(NASA_POWER_MAPPINGS.keys())

    def __init__(self, timeout_seconds: int = 20, lookback_days: int = 10):
        self.timeout_seconds = timeout_seconds
        self.lookback_days = lookback_days

    def collect(self, latitude: float, longitude: float) -> ProviderResult:
        self._validate_coordinates(latitude, longitude)

        end_date = datetime.now(timezone.utc).date() - timedelta(days=1)
        start_date = end_date - timedelta(days=self.lookback_days - 1)
        query = urlencode(
            {
                "parameters": ",".join(self.parameters),
                "community": "RE",
                "longitude": longitude,
                "latitude": latitude,
                "start": start_date.strftime("%Y%m%d"),
                "end": end_date.strftime("%Y%m%d"),
                "format": "JSON",
                "time-standard": "UTC",
            }
        )
        url = f"{self.base_url}?{query}"

        try:
            with urlopen(url, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            raise ProviderUnavailableError(
                f"NASA POWER request failed with status {error.code}."
            ) from error
        except (URLError, TimeoutError, socket.timeout) as error:
            raise ProviderUnavailableError("NASA POWER is unavailable or timed out.") from error
        except json.JSONDecodeError as error:
            raise ProviderResponseError("NASA POWER returned malformed JSON.") from error

        values = self._normalize(payload)
        if not any(value is not None for value in values.values()):
            raise ProviderResponseError("NASA POWER returned no usable mapped values.")

        return ProviderResult(name=self.name, values=values, status="available")

    def _normalize(self, payload: dict) -> dict[str, float | None]:
        try:
            parameters = payload["properties"]["parameter"]
        except (KeyError, TypeError) as error:
            raise ProviderResponseError("NASA POWER response is missing parameters.") from error

        normalized: dict[str, float | None] = {}
        for external_name, (internal_name, _unit) in NASA_POWER_MAPPINGS.items():
            series = parameters.get(external_name)
            normalized[internal_name] = self._latest_valid_value(series)

        return normalized

    @staticmethod
    def _latest_valid_value(series: dict | None) -> float | None:
        if not isinstance(series, dict):
            return None

        for key in sorted(series.keys(), reverse=True):
            value = series[key]
            if value in MISSING_SENTINELS or value is None:
                continue
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
        return None

    @staticmethod
    def _validate_coordinates(latitude: float, longitude: float) -> None:
        if latitude < -90 or latitude > 90 or longitude < -180 or longitude > 180:
            raise ProviderResponseError("Site coordinates are outside valid ranges.")


class GlobalWindAtlasProvider:
    name = "Global Wind Atlas"

    def collect(self, latitude: float, longitude: float) -> ProviderResult:
        raise ProviderUnavailableError(
            "Global Wind Atlas point-data provider is not configured. "
            "A stable public point API for wind speed and wind direction was not available "
            "in this environment."
        )


class EnvironmentalDataService:
    def __init__(self):
        self.providers = [NasaPowerProvider(), GlobalWindAtlasProvider()]

    def collect_for_site(self, latitude: float, longitude: float) -> tuple[dict, dict[str, str]]:
        collected: dict[str, float | bool | None] = {}
        statuses: dict[str, str] = {}

        for provider in self.providers:
            try:
                result = provider.collect(latitude, longitude)
            except EnvironmentalDataError as error:
                statuses[provider.name] = str(error)
                continue

            statuses[result.name] = result.status
            for field_name, value in result.values.items():
                if value is not None:
                    collected[field_name] = value

        if not collected:
            details = "; ".join(f"{name}: {message}" for name, message in statuses.items())
            raise ProviderUnavailableError(
                f"No environmental provider returned usable data. {details}"
            )

        return collected, statuses
