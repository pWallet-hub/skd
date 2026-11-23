from datetime import date, timedelta

from app.models.enums import UserRole
from tests.conftest import auth


def _create_child(client, parent, geo):
    r = client.post(
        "/api/v1/children",
        headers=auth(parent),
        json={
            "display_name": "Keza",
            "date_of_birth": "2020-05-01",
            "school_id": geo["school"].id,
            "area_id": geo["sector"].id,
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_parent_only_sees_own_children(client, make_user, geo):
    alice, bob = make_user(), make_user()
    child = _create_child(client, alice, geo)

    assert len(client.get("/api/v1/children", headers=auth(alice)).json()) == 1
    assert client.get("/api/v1/children", headers=auth(bob)).json() == []
    assert client.get(f"/api/v1/children/{child['id']}", headers=auth(bob)).status_code == 404


def test_report_defaults_location_from_child(client, make_user, geo):
    parent = make_user()
    child = _create_child(client, parent, geo)
    r = client.post(
        "/api/v1/reports",
        headers=auth(parent),
        json={
            "child_id": child["id"],
            "symptom_ids": [geo["diarrhea"].id],
            "onset_date": str(date.today() - timedelta(days=1)),
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["school_id"] == geo["school"].id
    assert body["area_id"] == geo["sector"].id
    assert body["verification"] == "parent_observation"


def test_future_onset_rejected(client, make_user, geo):
    parent = make_user()
    child = _create_child(client, parent, geo)
    r = client.post(
        "/api/v1/reports",
        headers=auth(parent),
        json={
            "child_id": child["id"],
            "symptom_ids": [geo["diarrhea"].id],
            "onset_date": str(date.today() + timedelta(days=1)),
        },
    )
    assert r.status_code == 422


def test_parent_cannot_report_for_someone_elses_child(client, make_user, geo):
    alice, bob = make_user(), make_user()
    child = _create_child(client, alice, geo)
    r = client.post(
        "/api/v1/reports",
        headers=auth(bob),
        json={
            "child_id": child["id"],
            "symptom_ids": [geo["diarrhea"].id],
            "onset_date": str(date.today()),
        },
    )
    assert r.status_code == 404


def test_institution_cannot_read_individual_reports(client, make_user):
    institution = make_user(UserRole.INSTITUTION)
    assert client.get("/api/v1/reports", headers=auth(institution)).status_code == 403
