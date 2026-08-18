"""
Cache layer backed by Redis, per the platform's Cloud & DevOps tech stack.

Design goal: caching must never be a reason the app breaks. If Redis is
down or unreachable (dev machine with no Redis running, container not
started yet, network hiccup), every function here falls back to a
per-process in-memory dict transparently. Callers never need to know
which backend is actually serving a given call — they just get a cache
that sometimes doesn't persist across restarts, which is a perfectly
acceptable degradation for what this is used for (short-TTL caching of
external API responses).

What gets cached: NASA POWER weather responses, Overpass infrastructure
responses, and elevation lookups, all keyed by rounded coordinates (+
date range where relevant) so nearby repeat calls within the TTL window
reuse a response instead of re-hitting a public, rate-limited API.
"""

import json
import logging
import threading
import time
from functools import wraps
from typing import Any, Callable, Optional

from app.config import settings

logger = logging.getLogger("swdip.cache")

_redis_client = None
_redis_checked = False
_redis_lock = threading.Lock()

# In-process fallback store: {key: (expires_at_epoch, json_value)}
_local_store: dict[str, tuple[float, str]] = {}
_local_lock = threading.Lock()


def _get_redis():
    """Lazily connect to Redis once; remember failure so we don't retry
    a TCP connect on every single request if Redis simply isn't there."""
    global _redis_client, _redis_checked
    if _redis_checked:
        return _redis_client
    with _redis_lock:
        if _redis_checked:
            return _redis_client
        try:
            import redis as redis_lib

            client = redis_lib.from_url(
                settings.redis_url, socket_connect_timeout=1, socket_timeout=1
            )
            client.ping()
            _redis_client = client
            logger.info("Redis cache connected at %s", settings.redis_url)
        except Exception as exc:  # noqa: BLE001 - any failure just disables Redis
            logger.warning(
                "Redis unavailable (%s) — falling back to in-process cache. "
                "This is expected in local dev without `docker compose up redis`.",
                exc,
            )
            _redis_client = None
        _redis_checked = True
    return _redis_client


def cache_get(key: str) -> Optional[Any]:
    client = _get_redis()
    if client is not None:
        try:
            raw = client.get(key)
            return json.loads(raw) if raw is not None else None
        except Exception as exc:  # noqa: BLE001
            logger.warning("Redis GET failed for %s (%s); falling back to local cache", key, exc)

    with _local_lock:
        entry = _local_store.get(key)
        if entry is None:
            return None
        expires_at, raw = entry
        if expires_at < time.monotonic():
            _local_store.pop(key, None)
            return None
        return json.loads(raw)


def cache_set(key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
    ttl_seconds = ttl_seconds or settings.cache_ttl_seconds
    raw = json.dumps(value)

    client = _get_redis()
    if client is not None:
        try:
            client.setex(key, ttl_seconds, raw)
            return
        except Exception as exc:  # noqa: BLE001
            logger.warning("Redis SET failed for %s (%s); falling back to local cache", key, exc)

    with _local_lock:
        _local_store[key] = (time.monotonic() + ttl_seconds, raw)


def cache_delete(key: str) -> None:
    client = _get_redis()
    if client is not None:
        try:
            client.delete(key)
        except Exception:  # noqa: BLE001
            pass
    with _local_lock:
        _local_store.pop(key, None)


def cache_health() -> dict:
    """Used by /health/detailed. Reports which backend is actually active."""
    client = _get_redis()
    if client is None:
        return {"backend": "in-process (Redis unavailable)", "status": "degraded"}
    try:
        client.ping()
        return {"backend": "redis", "status": "operational"}
    except Exception as exc:  # noqa: BLE001
        return {"backend": "in-process (Redis unavailable)", "status": "degraded", "detail": str(exc)}


def cached(key_fn: Callable[..., str], ttl_seconds: Optional[int] = None):
    """
    Decorator for functions that call a slow/rate-limited external API and
    return JSON-serializable data. `key_fn` receives the same args/kwargs
    as the wrapped function and must return a cache key string.

    Usage:
        @cached(lambda lat, lon: f"elevation:{round(lat,3)}:{round(lon,3)}")
        def fetch_elevation(lat, lon): ...
    """

    def decorator(fn: Callable):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            key = key_fn(*args, **kwargs)
            hit = cache_get(key)
            if hit is not None:
                return hit
            result = fn(*args, **kwargs)
            if result is not None:
                cache_set(key, result, ttl_seconds)
            return result

        return wrapper

    return decorator
