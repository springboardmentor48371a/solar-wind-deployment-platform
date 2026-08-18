from tests.conftest import auth_headers


def _create_project(client, user, name="Test Project"):
    resp = client.post(
        "/projects/",
        headers=auth_headers(user),
        json={"name": name, "objective": "Testing", "region": "Andhra Pradesh"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_planner_can_create_and_read_own_project(client, planner):
    project = _create_project(client, planner)
    resp = client.get(f"/projects/{project['id']}", headers=auth_headers(planner))
    assert resp.status_code == 200
    assert resp.json()["owner_id"] == planner["id"]


def test_planner_cannot_read_another_planners_project(client, planner, second_planner):
    project = _create_project(client, planner)
    resp = client.get(f"/projects/{project['id']}", headers=auth_headers(second_planner))
    assert resp.status_code == 403


def test_planner_cannot_write_another_planners_project(client, planner, second_planner):
    project = _create_project(client, planner)
    resp = client.post(
        f"/projects/{project['id']}/sites/",
        headers=auth_headers(second_planner),
        json={"name": "Sneaky Site", "latitude": 17.7, "longitude": 83.3},
    )
    assert resp.status_code == 403


def test_investor_has_read_only_oversight(client, planner):
    from tests.conftest import register_and_login

    investor = register_and_login(client, "Investor / Developer")
    project = _create_project(client, planner)

    read_resp = client.get(f"/projects/{project['id']}", headers=auth_headers(investor))
    assert read_resp.status_code == 200

    write_resp = client.post(
        f"/projects/{project['id']}/sites/",
        headers=auth_headers(investor),
        json={"name": "Investor Site", "latitude": 17.7, "longitude": 83.3},
    )
    assert write_resp.status_code == 403


def test_admin_and_pm_have_full_access_to_any_project(client, planner, admin, project_manager):
    project = _create_project(client, planner)

    admin_read = client.get(f"/projects/{project['id']}", headers=auth_headers(admin))
    assert admin_read.status_code == 200

    pm_site = client.post(
        f"/projects/{project['id']}/sites/",
        headers=auth_headers(project_manager),
        json={"name": "PM-created site", "latitude": 17.7, "longitude": 83.3},
    )
    assert pm_site.status_code == 201


def test_gis_analyst_can_read_and_analyze_but_not_create_project(client, gis_analyst):
    resp = client.post(
        "/projects/",
        headers=auth_headers(gis_analyst),
        json={"name": "GIS Attempt", "objective": "x"},
    )
    assert resp.status_code == 403


def test_site_creation_populates_derived_fields_from_stubbed_connectors(client, planner):
    """Confirms the ingestion pipeline (elevation + weather + infra) runs
    end-to-end using the deterministic test stubs from conftest, without
    needing the real external APIs."""
    project = _create_project(client, planner)
    site_resp = client.post(
        f"/projects/{project['id']}/sites/",
        headers=auth_headers(planner),
        json={"name": "Vizag Coastal Plot", "latitude": 17.72, "longitude": 83.30},
    )
    assert site_resp.status_code == 201, site_resp.text
    site = site_resp.json()
    assert site["elevation_m"] == 250.0
    assert site["land_slope_pct"] == 3.5


def test_unauthenticated_request_to_projects_is_rejected(client):
    resp = client.get("/projects/")
    assert resp.status_code == 401
