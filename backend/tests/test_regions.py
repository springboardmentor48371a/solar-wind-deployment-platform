from tests.conftest import auth_headers


def test_planner_cannot_create_region(client, planner):
    resp = client.post(
        "/regions/", headers=auth_headers(planner), json={"name": "Coastal Andhra"}
    )
    assert resp.status_code == 403


def test_gis_analyst_can_create_and_list_region(client, gis_analyst):
    create = client.post(
        "/regions/",
        headers=auth_headers(gis_analyst),
        json={
            "name": "Coastal Andhra",
            "country": "India",
            "admin_area": "Andhra Pradesh",
            "min_latitude": 15.0,
            "max_latitude": 19.0,
            "min_longitude": 80.0,
            "max_longitude": 84.5,
        },
    )
    assert create.status_code == 201, create.text
    region = create.json()
    assert region["project_count"] == 0

    listed = client.get("/regions/", headers=auth_headers(gis_analyst))
    assert listed.status_code == 200
    assert any(r["id"] == region["id"] for r in listed.json())


def test_duplicate_region_name_rejected(client, admin):
    payload = {"name": "Rayalaseema"}
    first = client.post("/regions/", headers=auth_headers(admin), json=payload)
    assert first.status_code == 201
    second = client.post("/regions/", headers=auth_headers(admin), json=payload)
    assert second.status_code == 409


def test_invalid_bounding_box_rejected(client, admin):
    resp = client.post(
        "/regions/",
        headers=auth_headers(admin),
        json={"name": "Bad Box", "min_latitude": 20.0, "max_latitude": 10.0},
    )
    assert resp.status_code == 422


def test_project_can_reference_a_region_and_count_updates(client, admin, planner):
    region = client.post(
        "/regions/", headers=auth_headers(admin), json={"name": "North Coastal AP"}
    ).json()

    project = client.post(
        "/projects/",
        headers=auth_headers(planner),
        json={"name": "Solar Farm A", "region_id": region["id"]},
    )
    assert project.status_code == 201
    assert project.json()["region_id"] == region["id"]

    refreshed = client.get(f"/regions/{region['id']}", headers=auth_headers(planner))
    assert refreshed.json()["project_count"] == 1


def test_creating_project_with_unknown_region_id_404s(client, planner):
    resp = client.post(
        "/projects/", headers=auth_headers(planner), json={"name": "Ghost Region", "region_id": 999999}
    )
    assert resp.status_code == 404


def test_cannot_delete_region_still_referenced_by_a_project(client, admin, planner):
    region = client.post(
        "/regions/", headers=auth_headers(admin), json={"name": "Uddanam"}
    ).json()
    client.post(
        "/projects/",
        headers=auth_headers(planner),
        json={"name": "Wind Farm B", "region_id": region["id"]},
    )

    delete_resp = client.delete(f"/regions/{region['id']}", headers=auth_headers(admin))
    assert delete_resp.status_code == 409


def test_delete_unreferenced_region_succeeds(client, admin):
    region = client.post(
        "/regions/", headers=auth_headers(admin), json={"name": "Empty Region"}
    ).json()
    delete_resp = client.delete(f"/regions/{region['id']}", headers=auth_headers(admin))
    assert delete_resp.status_code == 204

    get_resp = client.get(f"/regions/{region['id']}", headers=auth_headers(admin))
    assert get_resp.status_code == 404
