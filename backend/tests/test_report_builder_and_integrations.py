from tests.conftest import auth_headers


def _make_project(client, planner):
    resp = client.post("/projects/", headers=auth_headers(planner), json={"name": "Report Builder Test"})
    return resp.json()["id"]


def test_report_template_crud_and_generation(client, planner):
    project_id = _make_project(client, planner)

    create_resp = client.post(
        "/report-templates",
        headers=auth_headers(planner),
        json={"name": "My Summary", "sections": ["summary", "suitability"], "is_executive_summary": False},
    )
    assert create_resp.status_code == 201, create_resp.text
    template_id = create_resp.json()["id"]
    assert create_resp.json()["sections"] == ["summary", "suitability"]

    list_resp = client.get("/report-templates", headers=auth_headers(planner))
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    gen_resp = client.get(
        f"/projects/{project_id}/reports/from-template/{template_id}", headers=auth_headers(planner)
    )
    assert gen_resp.status_code == 200
    assert gen_resp.headers["content-type"] == "application/pdf"

    del_resp = client.delete(f"/report-templates/{template_id}", headers=auth_headers(planner))
    assert del_resp.status_code == 204


def test_custom_report_rejects_unknown_section(client, planner):
    project_id = _make_project(client, planner)
    resp = client.get(
        f"/projects/{project_id}/reports/custom?sections=summary,not_a_real_section",
        headers=auth_headers(planner),
    )
    assert resp.status_code == 422


def test_executive_summary_generates_pdf(client, planner):
    project_id = _make_project(client, planner)
    resp = client.get(f"/projects/{project_id}/reports/executive-summary", headers=auth_headers(planner))
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"


def test_integration_connection_requires_admin_or_pm(client, planner):
    resp = client.post(
        "/integrations/",
        headers=auth_headers(planner),
        json={
            "integration_type": "scada_iot",
            "name": "Test SCADA bridge",
            "endpoint_url": "https://example.com/webhook",
        },
    )
    assert resp.status_code == 403


def test_integration_connection_crud_as_admin(client, admin):
    create_resp = client.post(
        "/integrations/",
        headers=auth_headers(admin),
        json={
            "integration_type": "project_management",
            "name": "Jira Webhook",
            "endpoint_url": "https://example.com/webhook",
            "auth_header_name": "Authorization",
            "auth_header_value": "Bearer secret-token",
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    integration_id = create_resp.json()["id"]
    # auth_header_value must never be echoed back in responses
    assert "auth_header_value" not in create_resp.json()

    list_resp = client.get("/integrations/", headers=auth_headers(admin))
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    del_resp = client.delete(f"/integrations/{integration_id}", headers=auth_headers(admin))
    assert del_resp.status_code == 204
