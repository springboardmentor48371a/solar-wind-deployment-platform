"""
Confirms the gap closed in this pass: IntegrationConnection webhooks now
fire automatically on real events (new suitability score, new weather
alert), not just via the manual /test button. Mocks requests.post at the
module level used by app.services.integration_dispatch so no real
network call happens, but we can assert it was actually invoked with the
right event_type.
"""

from unittest.mock import patch, MagicMock

from tests.conftest import auth_headers


def test_suitability_score_dispatches_to_active_integration(client, admin, planner):
    project_resp = client.post("/projects/", headers=auth_headers(planner), json={"name": "Dispatch Test"})
    project_id = project_resp.json()["id"]

    integration_resp = client.post(
        "/integrations/",
        headers=auth_headers(admin),
        json={
            "project_id": project_id,
            "integration_type": "third_party_analytics",
            "name": "Test Analytics Hook",
            "endpoint_url": "https://example.com/webhook",
        },
    )
    assert integration_resp.status_code == 201, integration_resp.text

    mock_response = MagicMock()
    mock_response.ok = True

    with patch("app.services.integration_dispatch.requests.post", return_value=mock_response) as mock_post:
        site_resp = client.post(
            f"/projects/{project_id}/sites/",
            headers=auth_headers(planner),
            json={"name": "Dispatch Site", "latitude": 17.72, "longitude": 83.30},
        )
        assert site_resp.status_code == 201, site_resp.text

    # register_site runs the full pipeline, which ends in
    # compute_site_suitability -> generate_suitability_alert -> dispatch_event.
    # At least one call must carry event_type "suitability_score_updated".
    event_types = [call.kwargs["json"]["event_type"] for call in mock_post.call_args_list]
    assert "suitability_score_updated" in event_types


def test_integration_connections_list_reflects_last_status_after_dispatch(client, admin, planner):
    project_resp = client.post("/projects/", headers=auth_headers(planner), json={"name": "Status Test"})
    project_id = project_resp.json()["id"]

    integration_resp = client.post(
        "/integrations/",
        headers=auth_headers(admin),
        json={
            "project_id": project_id,
            "integration_type": "project_management",
            "name": "Test PM Hook",
            "endpoint_url": "https://example.com/webhook",
        },
    )
    integration_id = integration_resp.json()["id"]

    mock_response = MagicMock()
    mock_response.ok = True
    with patch("app.services.integration_dispatch.requests.post", return_value=mock_response):
        client.post(
            f"/projects/{project_id}/sites/",
            headers=auth_headers(planner),
            json={"name": "Status Site", "latitude": 10.0, "longitude": 10.0},
        )

    list_resp = client.get("/integrations/", headers=auth_headers(admin))
    updated = next(i for i in list_resp.json() if i["id"] == integration_id)
    assert updated["last_status"] == "ok"
    assert updated["last_used_at"] is not None
