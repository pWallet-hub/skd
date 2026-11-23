from datetime import date

from sqlalchemy import select

from app.models import Child, Notification
from app.models.enums import UserRole
from app.services.alerts import publish_alert
from tests.conftest import auth


def test_small_counts_are_suppressed(client, make_user, add_reports):
    add_reports(2)
    analyst = make_user(UserRole.ANALYST)
    areas = client.get("/api/v1/analytics/areas", headers=auth(analyst)).json()
    assert areas[0]["suppressed"] is True
    assert areas[0]["report_count"] is None
    assert areas[0]["top_category"] is None


def test_large_counts_are_visible(client, make_user, add_reports):
    add_reports(4)
    analyst = make_user(UserRole.ANALYST)
    schools = client.get("/api/v1/analytics/schools", headers=auth(analyst)).json()
    assert schools[0]["report_count"] == 4
    assert schools[0]["suppressed"] is False


def test_parents_cannot_see_analytics(client, make_user):
    assert client.get("/api/v1/analytics/overview", headers=auth(make_user())).status_code == 403


def test_alert_four_eyes_approval_and_fanout(client, db, make_user, geo, monkeypatch):
    analyst = make_user(UserRole.ANALYST)
    reviewer = make_user(UserRole.HEALTH_REVIEWER)
    parent_in_school = make_user()
    other_parent = make_user()
    db.add_all(
        [
            Child(
                guardian=parent_in_school,
                display_name="A",
                date_of_birth=date(2019, 1, 1),
                school=geo["school"],
            ),
            Child(guardian=other_parent, display_name="B", date_of_birth=date(2019, 1, 1)),
        ]
    )
    db.commit()

    r = client.post(
        "/api/v1/alerts",
        headers=auth(reviewer),
        json={
            "title": "Advice for families",
            "message": "Please follow hygiene guidance and seek care if needed.",
            "target_school_ids": [geo["school"].id],
        },
    )
    assert r.status_code == 201
    alert_id = r.json()["id"]

    assert (
        client.post(f"/api/v1/alerts/{alert_id}/submit", headers=auth(reviewer)).status_code == 200
    )
    # The author cannot approve their own alert
    assert (
        client.post(f"/api/v1/alerts/{alert_id}/approve", headers=auth(reviewer)).status_code == 403
    )
    # Analysts cannot approve at all
    assert (
        client.post(f"/api/v1/alerts/{alert_id}/approve", headers=auth(analyst)).status_code == 403
    )

    second_reviewer = make_user(UserRole.HEALTH_REVIEWER)
    r = client.post(f"/api/v1/alerts/{alert_id}/approve", headers=auth(second_reviewer))
    assert r.json()["status"] == "approved"

    # Run the Celery task inline against the test session
    from app.api.routes import alerts as alerts_route
    from app.models import CommunityAlert

    monkeypatch.setattr(
        alerts_route.publish_alert_task,
        "delay",
        lambda aid: publish_alert(db, db.get(CommunityAlert, aid)),
    )
    assert (
        client.post(f"/api/v1/alerts/{alert_id}/publish", headers=auth(analyst)).status_code == 202
    )

    recipients = set(db.scalars(select(Notification.recipient_id)))
    assert recipients == {parent_in_school.id}
