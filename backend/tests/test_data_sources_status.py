"""
GET /data-sources/status had zero test coverage before this pass, and I
just rewrote it to cover 11 connectors instead of 3. Mocks every
outbound HTTP call so the test suite stays fast/deterministic and
doesn't depend on real network access, while still exercising the real
code path (including the not_configured branches, which are the parts
most likely to have a bug like an unguarded exception).
"""

from unittest.mock import MagicMock, patch

from tests.conftest import auth_headers


def test_data_source_status_returns_all_connectors_without_crashing(client, planner):
    """
    No API keys are configured in the test environment (no
    OPENWEATHER_API_KEY) — this is exactly the "not_configured" path,
    and the endpoint must return 200 with clear statuses, never crash,
    even when every optional connector is unset. AWS Earth Search
    (Sentinel-2) needs no configuration at all, unlike the old Sentinel
    Hub integration this replaced, so it's checked separately below
    against a mocked POST response instead of "not_configured".
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    with patch("app.routers.data_sources.requests.get", return_value=mock_response), \
         patch("app.routers.data_sources.requests.post", return_value=mock_response):
        resp = client.get("/data-sources/status", headers=auth_headers(planner))

    assert resp.status_code == 200, resp.text
    body = resp.json()
    names = {item["name"] for item in body}

    # Always-on public connectors
    assert "NASA POWER" in names
    assert "World Bank Open Data" in names
    assert "NOAA / National Weather Service" in names
    assert "MongoDB (raw payload store)" in names

    # AWS Earth Search needs zero configuration — it's operational the
    # moment the (mocked) request succeeds, never "not_configured".
    earth_search = next(i for i in body if i["name"] == "AWS Earth Search (Sentinel-2)")
    assert earth_search["status"] == "operational"

    # Credential-gated connectors correctly report not_configured rather
    # than a crash or a misleading "down"
    openweather = next(i for i in body if i["name"] == "OpenWeather")
    assert openweather["status"] == "not_configured"

    data_lake_status = next(i for i in body if i["name"] == "Data Lake (S3)")
    assert data_lake_status["status"] == "not_configured"


def test_data_source_status_reports_down_on_network_failure(client, planner):
    """Confirms a real connectivity failure surfaces as 'down', not a 500."""
    import requests

    mock_ok = MagicMock()
    mock_ok.status_code = 200
    with patch("app.routers.data_sources.requests.get", side_effect=requests.ConnectionError("no route to host")), \
         patch("app.routers.data_sources.requests.post", return_value=mock_ok):
        resp = client.get("/data-sources/status", headers=auth_headers(planner))

    assert resp.status_code == 200
    nasa = next(i for i in resp.json() if i["name"] == "NASA POWER")
    assert nasa["status"] == "down"
