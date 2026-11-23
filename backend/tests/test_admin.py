from sqlalchemy import select

from app.models import AuditLog
from app.models.enums import UserRole
from app.services.surveillance import detect_signals
from tests.conftest import auth


def test_only_admins_reach_admin_api(client, make_user):
    for role in (UserRole.PARENT, UserRole.ANALYST, UserRole.HEALTH_REVIEWER):
        assert client.get("/api/v1/admin/users", headers=auth(make_user(role))).status_code == 403


def test_create_user_with_temporary_password_and_login(client, db, make_user):
    admin = make_user(UserRole.ADMIN)
    r = client.post(
        "/api/v1/admin/users",
        headers=auth(admin),
        json={"email": "New.Analyst@Example.com", "full_name": "New Analyst", "role": "analyst"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["user"]["email"] == "new.analyst@example.com"
    temp = body["temporary_password"]
    assert temp

    login = client.post(
        "/api/v1/auth/login", json={"email": "new.analyst@example.com", "password": temp}
    )
    assert login.status_code == 200
    actions = set(db.scalars(select(AuditLog.action)))
    assert {"user.create", "auth.login"} <= actions


def test_user_listing_search_and_filters(client, make_user):
    admin = make_user(UserRole.ADMIN, full_name="Root Admin")
    make_user(UserRole.PARENT, full_name="Aline Parent")
    make_user(UserRole.ANALYST, full_name="Eric Analyst")
    r = client.get("/api/v1/admin/users?role=parent", headers=auth(admin)).json()
    assert r["total"] == 1 and r["items"][0]["full_name"] == "Aline Parent"
    r = client.get("/api/v1/admin/users?search=eric", headers=auth(admin)).json()
    assert r["total"] == 1 and r["items"][0]["role"] == "analyst"


def test_deactivated_user_cannot_sign_in(client, make_user):
    admin = make_user(UserRole.ADMIN)
    parent = make_user(email="p@example.com")
    r = client.patch(
        f"/api/v1/admin/users/{parent.id}", headers=auth(admin), json={"is_active": False}
    )
    assert r.status_code == 200 and r.json()["is_active"] is False
    r = client.post(
        "/api/v1/auth/login", json={"email": "p@example.com", "password": "password123"}
    )
    assert r.status_code == 403


def test_admin_cannot_lock_themselves_out(client, make_user):
    admin = make_user(UserRole.ADMIN)
    url = f"/api/v1/admin/users/{admin.id}"
    assert client.patch(url, headers=auth(admin), json={"is_active": False}).status_code == 409
    assert client.patch(url, headers=auth(admin), json={"role": "parent"}).status_code == 409


def test_password_reset(client, make_user):
    admin = make_user(UserRole.ADMIN)
    user = make_user(email="r@example.com")
    temp = client.post(f"/api/v1/admin/users/{user.id}/reset-password", headers=auth(admin)).json()[
        "temporary_password"
    ]
    r = client.post("/api/v1/auth/login", json={"email": "r@example.com", "password": temp})
    assert r.status_code == 200


def test_detection_settings_override_changes_detection(client, db, make_user, add_reports):
    admin = make_user(UserRole.ADMIN)
    add_reports(3, days_ago=1)
    assert detect_signals(db) == (0, 0)  # default minimum is 4 reports

    current = client.get("/api/v1/admin/settings/detection", headers=auth(admin)).json()
    r = client.put(
        "/api/v1/admin/settings/detection",
        headers=auth(admin),
        json={**current, "signal_min_reports": 3},
    )
    assert r.status_code == 200 and r.json()["signal_min_reports"] == 3
    created, _ = detect_signals(db)
    assert created == 2
    assert db.scalar(select(AuditLog).where(AuditLog.action == "settings.update"))


def test_invalid_settings_rejected(client, make_user):
    admin = make_user(UserRole.ADMIN)
    current = client.get("/api/v1/admin/settings/detection", headers=auth(admin)).json()
    r = client.put(
        "/api/v1/admin/settings/detection",
        headers=auth(admin),
        json={**current, "signal_window_days": 30, "signal_baseline_days": 14},
    )
    assert r.status_code == 422


def test_school_crud(client, make_user, geo):
    admin = make_user(UserRole.ADMIN)
    payload = {
        "name": "New School",
        "area_id": geo["sector"].id,
        "location": {"latitude": -1.95, "longitude": 30.06},
    }
    r = client.post("/api/v1/geo/schools", headers=auth(admin), json=payload)
    assert r.status_code == 201, r.text
    school_id = r.json()["id"]
    assert r.json()["location"]["longitude"] == 30.06

    r = client.patch(
        f"/api/v1/geo/schools/{school_id}", headers=auth(admin), json={"is_verified": True}
    )
    assert r.json()["is_verified"] is True and r.json()["name"] == "New School"
    assert client.delete(f"/api/v1/geo/schools/{school_id}", headers=auth(admin)).status_code == 204
    analyst = make_user(UserRole.ANALYST)
    assert (
        client.post("/api/v1/geo/schools", headers=auth(analyst), json=payload).status_code == 403
    )


def test_stats_system_and_audit_endpoints(client, make_user, add_reports):
    admin = make_user(UserRole.ADMIN)
    add_reports(2)
    stats = client.get("/api/v1/admin/stats", headers=auth(admin)).json()
    assert stats["total_users"] >= 3 and len(stats["reports_per_day"]) == 30
    system = client.get("/api/v1/admin/system", headers=auth(admin)).json()
    assert {s["name"] for s in system["services"]} >= {"Database", "Redis"}
    logs = client.get("/api/v1/admin/audit-logs", headers=auth(admin)).json()
    assert "items" in logs and "total" in logs


def test_csv_export_is_suppressed(client, make_user, add_reports):
    add_reports(2)
    r = client.get("/api/v1/analytics/export.csv", headers=auth(make_user(UserRole.INSTITUTION)))
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
    rows = r.text.strip().splitlines()
    assert rows[0].startswith("level,id,name")
    assert ",,True," in rows[1]  # count blank, suppressed
