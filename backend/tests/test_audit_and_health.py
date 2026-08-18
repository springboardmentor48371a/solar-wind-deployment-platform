from tests.conftest import auth_headers


def test_health_check_is_public(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_detailed_health_reports_each_dependency(client):
    resp = client.get("/health/detailed")
    assert resp.status_code == 200
    body = resp.json()
    assert "postgres" in body and "mongodb" in body and "cache" in body
    # SQLite-backed test DB should report healthy regardless of whether the
    # real Mongo/Redis services happen to be running in this environment.
    assert body["postgres"]["status"] == "operational"


def test_audit_log_requires_admin_role(client, planner):
    resp = client.get("/admin/audit-logs/", headers=auth_headers(planner))
    assert resp.status_code == 403


def test_admin_sees_audit_trail_after_actions(client, admin, planner):
    # planner's own registration/login already wrote audit rows; creating
    # a project should add one more, visible to admin.
    client.post("/projects/", headers=auth_headers(planner), json={"name": "Audited Project"})

    resp = client.get("/admin/audit-logs/", headers=auth_headers(admin))
    assert resp.status_code == 200
    actions = [row["action"] for row in resp.json()]
    assert "create_project" in actions
    assert "login" in actions
