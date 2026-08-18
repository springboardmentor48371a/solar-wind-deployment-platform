"""
MongoDB connector — the platform's secondary database.

PostgreSQL/PostGIS (see database.py) holds structured, relational data:
users, projects, sites, parsed weather readings, scores. MongoDB holds the
raw, unstructured payloads those structured rows were derived from — the
full NASA POWER JSON response, the full Overpass JSON response — so a
future reprocessing pass (e.g. once new AI/ML parameters are needed) can
re-derive fields without re-querying the external API.

Every write here is best-effort: if Mongo is unreachable, callers should
degrade gracefully (log and continue) rather than fail the request, the
same resilience pattern already used for the external HTTP calls.
"""

import datetime
from typing import Any, Optional

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from app.config import settings

_client: Optional[MongoClient] = None


def get_mongo_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(settings.mongodb_url, serverSelectionTimeoutMS=5000)
    return _client


def get_db():
    return get_mongo_client()[settings.mongodb_db_name]


def store_raw_payload(collection: str, site_id: int, source: str, payload: Any) -> None:
    """
    Persists a raw external-API response for a site.

    collection: e.g. "weather_raw", "infrastructure_raw"
    source:     e.g. "NASA_POWER", "OVERPASS"
    """
    try:
        db = get_db()
        db[collection].insert_one(
            {
                "site_id": site_id,
                "source": source,
                "payload": payload,
                "fetched_at": datetime.datetime.utcnow(),
            }
        )
    except PyMongoError as exc:
        print(f"Warning: MongoDB write failed ({collection}, site {site_id}): {exc}")


def get_latest_raw_payload(collection: str, site_id: int) -> Optional[dict]:
    try:
        db = get_db()
        return db[collection].find_one(
            {"site_id": site_id}, sort=[("fetched_at", -1)]
        )
    except PyMongoError as exc:
        print(f"Warning: MongoDB read failed ({collection}, site {site_id}): {exc}")
        return None


def list_ingestion_events(site_id: int, limit: int = 20) -> list:
    """
    Every raw-payload write for a site, across both raw collections, newest
    first — used by the /ingestion-log endpoint so a person can see actual
    proof of which external API was called, when, and how large the
    response was, rather than just trusting that "ingestion" happened.
    """
    events = []
    try:
        db = get_db()
        for collection in ("weather_raw", "infrastructure_raw"):
            cursor = (
                db[collection]
                .find({"site_id": site_id}, {"payload": 0})  # metadata only, skip the (large) payload
                .sort("fetched_at", -1)
                .limit(limit)
            )
            for doc in cursor:
                events.append(
                    {
                        "collection": collection,
                        "source": doc.get("source"),
                        "fetched_at": doc.get("fetched_at"),
                    }
                )
    except PyMongoError as exc:
        print(f"Warning: MongoDB read failed (ingestion log, site {site_id}): {exc}")
    events.sort(key=lambda e: e["fetched_at"] or datetime.datetime.min, reverse=True)
    return events[:limit]


def check_connection() -> bool:
    try:
        get_mongo_client().admin.command("ping")
        return True
    except PyMongoError:
        return False
