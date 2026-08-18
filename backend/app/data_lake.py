"""
Data Lake — S3-compatible object storage for raw, immutable ingestion
payloads (architecture diagram's "Data Lake (AWS S3 / Blob)").

This sits alongside MongoDB (see mongo.py), not instead of it: Mongo is
the queryable "latest raw payload per site" store the app reads back from
(e.g. /ingestion-log); the data lake is the durable, append-only archive
of literally every payload ever pulled, organized for later bulk/warehouse
processing (one object per fetch, partitioned by date).

Works against AWS S3 or any S3-compatible endpoint (MinIO, Cloudflare R2,
Backblaze B2) by setting DATA_LAKE_S3_ENDPOINT_URL. Same resilience
pattern as every other external connector in this codebase: if boto3
isn't installed, no bucket/credentials are configured, or the upload
fails, callers get a clear best-effort no-op instead of a crashed
request — archival is durability/analytics infrastructure, never a hard
dependency the ingestion pipeline can't run without.
"""

import datetime
import json
from typing import Any, Optional

from app.config import settings

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
    _BOTO_AVAILABLE = True
except ImportError:  # boto3 not installed — data lake archival simply no-ops
    _BOTO_AVAILABLE = False

_client = None
_client_checked = False


def _get_client():
    global _client, _client_checked
    if _client_checked:
        return _client
    _client_checked = True
    if not _BOTO_AVAILABLE or not settings.data_lake_bucket:
        return None
    try:
        kwargs = {}
        if settings.data_lake_s3_endpoint_url:
            kwargs["endpoint_url"] = settings.data_lake_s3_endpoint_url
        if settings.data_lake_access_key_id:
            kwargs["aws_access_key_id"] = settings.data_lake_access_key_id
            kwargs["aws_secret_access_key"] = settings.data_lake_secret_access_key
        _client = boto3.client("s3", region_name=settings.data_lake_region or None, **kwargs)
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: data lake S3 client init failed: {exc}")
        _client = None
    return _client


def is_configured() -> bool:
    return _BOTO_AVAILABLE and bool(settings.data_lake_bucket)


def archive_payload(collection: str, site_id: int, source: str, payload: Any) -> Optional[str]:
    """
    Writes one raw payload as a JSON object, partitioned by UTC date and
    collection, e.g.:
        s3://<bucket>/raw/weather_raw/2026-08-17/site-42-1755436800.json

    Returns the object key on success, None if archival is unconfigured
    or failed (best-effort — never raises).
    """
    client = _get_client()
    if client is None:
        return None

    now = datetime.datetime.utcnow()
    key = (
        f"raw/{collection}/{now:%Y-%m-%d}/"
        f"site-{site_id}-{source.lower()}-{int(now.timestamp() * 1000)}.json"
    )
    body = json.dumps(
        {"site_id": site_id, "source": source, "fetched_at": now.isoformat(), "payload": payload},
        default=str,
    )
    try:
        client.put_object(
            Bucket=settings.data_lake_bucket,
            Key=key,
            Body=body.encode("utf-8"),
            ContentType="application/json",
        )
        return key
    except (BotoCoreError, ClientError, Exception) as exc:  # noqa: BLE001
        print(f"Warning: data lake archival failed ({collection}, site {site_id}): {exc}")
        return None
