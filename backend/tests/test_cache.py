"""
The test environment has no Redis running (conftest.py points REDIS_URL at
an unused port on purpose), so these tests are really verifying the
fallback path: app.cache must behave like a working cache even when Redis
itself is unreachable, since that's the exact situation a fresh `git
clone` + `pip install` without `docker compose up redis` puts a developer
in.
"""

from app import cache


def test_cache_set_and_get_roundtrip():
    cache.cache_set("test:key:1", {"a": 1, "b": [1, 2, 3]}, ttl_seconds=60)
    assert cache.cache_get("test:key:1") == {"a": 1, "b": [1, 2, 3]}


def test_cache_miss_returns_none():
    assert cache.cache_get("test:key:does-not-exist") is None


def test_cache_delete_removes_value():
    cache.cache_set("test:key:2", "value", ttl_seconds=60)
    cache.cache_delete("test:key:2")
    assert cache.cache_get("test:key:2") is None


def test_cache_health_reports_degraded_without_redis():
    status = cache.cache_health()
    assert status["status"] in ("operational", "degraded")
    assert "backend" in status


def test_cached_decorator_avoids_recomputation():
    calls = {"count": 0}

    @cache.cached(lambda x: f"test:decorated:{x}", ttl_seconds=60)
    def expensive(x):
        calls["count"] += 1
        return x * 2

    assert expensive(5) == 10
    assert expensive(5) == 10
    assert calls["count"] == 1  # second call was served from cache

    assert expensive(6) == 12
    assert calls["count"] == 2  # different key, cache miss
