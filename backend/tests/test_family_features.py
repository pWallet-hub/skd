from datetime import date, timedelta

from sqlalchemy import select

from app.models import Child, Notification, SystemSetting
from app.models.enums import NotificationKind, UserRole
from app.services.demo import simulate_activity
from tests.conftest import auth


def _child(client, parent, dob: date, **extra):
    r = client.post(
        "/api/v1/children",
        headers=auth(parent),
        json={"display_name": "Gisa", "date_of_birth": str(dob), **extra},
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_vaccination_schedule_statuses_and_recording(client, make_user):
    parent = make_user()
    # ~9.5 months old: early doses overdue (nothing recorded), measles-rubella 1 due, MR2 upcoming
    child = _child(client, parent, date.today() - timedelta(days=285))
    url = f"/api/v1/children/{child['id']}/immunizations"
    items = {v["code"]: v for v in client.get(url, headers=auth(parent)).json()}
    assert items["BCG"]["status"] == "overdue"
    assert items["MR1"]["status"] == "due"
    assert items["MR2"]["status"] == "upcoming"

    r = client.post(
        url, headers=auth(parent), json={"vaccine_code": "MR1", "given_on": str(date.today())}
    )
    assert r.status_code == 201
    assert {v["code"]: v for v in r.json()}["MR1"]["status"] == "given"

    bad = client.post(
        url, headers=auth(parent), json={"vaccine_code": "NOPE", "given_on": str(date.today())}
    )
    assert bad.status_code == 422
    summary = client.get(
        f"/api/v1/children/{child['id']}/care-summary", headers=auth(parent)
    ).json()
    assert summary["vaccines_overdue"] > 0


def test_milestones(client, make_user):
    parent = make_user()
    child = _child(client, parent, date.today() - timedelta(days=30 * 20))  # ~20 months
    url = f"/api/v1/children/{child['id']}/milestones"
    items = {m["code"]: m for m in client.get(url, headers=auth(parent)).json()}
    assert items["smiles"]["status"] == "check"  # well past expected age, not recorded
    assert items["points"]["status"] == "expected"
    assert items["counts_10"]["status"] == "upcoming"
    r = client.post(
        url,
        headers=auth(parent),
        json={"milestone_code": "walks", "achieved_on": str(date.today())},
    )
    assert {m["code"]: m for m in r.json()}["walks"]["status"] == "achieved"


def test_other_parents_cannot_touch_child_records(client, make_user):
    alice, bob = make_user(), make_user()
    child = _child(client, alice, date.today() - timedelta(days=400))
    assert (
        client.get(f"/api/v1/children/{child['id']}/immunizations", headers=auth(bob)).status_code
        == 404
    )
    assert (
        client.post(f"/api/v1/children/{child['id']}/share", headers=auth(bob), json={}).status_code
        == 404
    )


def test_report_creates_confirmation_and_guidance(client, db, make_user, geo):
    parent = make_user()
    child = _child(client, parent, date(2020, 1, 1))
    r = client.post(
        "/api/v1/reports",
        headers=auth(parent),
        json={
            "child_id": child["id"],
            "symptom_ids": [geo["diarrhea"].id],
            "onset_date": str(date.today()),
        },
    )
    assert r.status_code == 201
    kinds = [
        n.kind
        for n in db.scalars(select(Notification).where(Notification.recipient_id == parent.id))
    ]
    assert NotificationKind.FOLLOW_UP in kinds and NotificationKind.GUIDANCE in kinds


def test_verification_notifies_parent_and_queue_filters(client, db, make_user, geo):
    parent = make_user()
    reviewer = make_user(UserRole.HEALTH_REVIEWER)
    child = _child(client, parent, date(2020, 1, 1), area_id=geo["sector"].id)
    report = client.post(
        "/api/v1/reports",
        headers=auth(parent),
        json={
            "child_id": child["id"],
            "symptom_ids": [geo["cough"].id],
            "onset_date": str(date.today()),
        },
    ).json()
    queue = client.get(
        "/api/v1/reports?verification=parent_observation", headers=auth(reviewer)
    ).json()
    assert queue[0]["area_name"] == "Sector" and queue[0]["child_age_months"] > 0

    r = client.post(
        f"/api/v1/reports/{report['id']}/verification",
        headers=auth(reviewer),
        json={"verification": "clinically_confirmed"},
    )
    assert r.status_code == 200
    titles = [
        n.title
        for n in db.scalars(select(Notification).where(Notification.recipient_id == parent.id))
    ]
    assert "Your report was reviewed" in titles
    assert (
        client.get("/api/v1/reports?verification=parent_observation", headers=auth(reviewer)).json()
        == []
    )


def test_health_card_share_link(client, make_user):
    parent = make_user()
    child = _child(client, parent, date.today() - timedelta(days=500))
    link = client.post(
        f"/api/v1/children/{child['id']}/share", headers=auth(parent), json={"hours": 1}
    ).json()
    assert link["url"].endswith(link["token"])
    card = client.get(f"/api/v1/health-card/{link['token']}")  # no login needed
    assert card.status_code == 200
    assert card.json()["display_name"] == "Gisa" and len(card.json()["vaccines"]) > 5
    assert client.get("/api/v1/health-card/not-a-token").status_code == 404
    # an access token must not work as a health-card token
    from app.core.security import create_token

    assert client.get(f"/api/v1/health-card/{create_token(parent.id, 'access')}").status_code == 404


def test_google_sign_in_is_a_placeholder(client):
    assert client.get("/api/v1/auth/providers").json()["google"]["status"] == "placeholder"
    assert client.post("/api/v1/auth/google").status_code == 501


def test_demo_simulator_generates_activity(client, db, make_user, geo):
    parent = make_user(email="sim@example.com")
    dob = date.today() - timedelta(days=700)
    db.add(
        Child(
            guardian=parent, display_name="Sim", date_of_birth=dob,
            area=geo["sector"], school=geo["school"],
        )
    )  # fmt: skip
    db.commit()
    stats = simulate_activity(db, seed=1)
    assert stats["reports"] >= 1
    assert db.get(SystemSetting, "demo_last_run") is not None

    admin = make_user(UserRole.ADMIN)
    assert client.get("/api/v1/admin/demo", headers=auth(admin)).json()["enabled"] is False
    r = client.put("/api/v1/admin/demo", headers=auth(admin), json={"enabled": True})
    assert r.json()["enabled"] is True
    assert client.post("/api/v1/admin/demo/simulate", headers=auth(admin)).status_code == 200
    assert (
        client.put(
            "/api/v1/admin/demo", headers=auth(make_user()), json={"enabled": False}
        ).status_code
        == 403
    )
