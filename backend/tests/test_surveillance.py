from sqlalchemy import select

from app.models import HealthSignal
from app.models.enums import SymptomCategory, UserRole
from app.services.surveillance import detect_signals
from tests.conftest import auth


def test_cluster_raises_one_school_and_one_area_signal(db, add_reports):
    add_reports(5, days_ago=1)
    created, updated = detect_signals(db)
    assert (created, updated) == (2, 0)

    signals = db.scalars(select(HealthSignal)).all()
    assert {s.symptom_category for s in signals} == {SymptomCategory.GASTROINTESTINAL}
    assert sum(1 for s in signals if s.school_id) == 1
    assert sum(1 for s in signals if s.area_id) == 1


def test_rerun_updates_instead_of_duplicating(db, add_reports):
    add_reports(5, days_ago=1)
    detect_signals(db)
    add_reports(1, days_ago=0)
    created, updated = detect_signals(db)
    assert (created, updated) == (0, 2)
    assert all(s.report_count == 6 for s in db.scalars(select(HealthSignal)))


def test_few_reports_do_not_raise_signal(db, add_reports):
    add_reports(2, days_ago=1)
    assert detect_signals(db) == (0, 0)


def test_steady_baseline_does_not_raise_signal(db, add_reports):
    # ~4 per week for the previous four weeks, then 4 this week -> ratio ~1
    for week in range(1, 5):
        add_reports(4, days_ago=7 * week + 1)
    add_reports(4, days_ago=1)
    assert detect_signals(db) == (0, 0)


def test_signal_review_workflow(client, db, make_user, add_reports):
    add_reports(5, days_ago=1)
    detect_signals(db)
    signal = db.scalars(select(HealthSignal)).first()
    analyst = make_user(UserRole.ANALYST)
    parent = make_user(UserRole.PARENT)
    url = f"/api/v1/signals/{signal.id}/transition"

    assert client.get("/api/v1/signals", headers=auth(parent)).status_code == 403

    # Cannot jump straight to confirmed
    r = client.post(url, headers=auth(analyst), json={"status": "confirmed", "note": "skip"})
    assert r.status_code == 409

    r = client.post(url, headers=auth(analyst), json={"status": "under_review", "note": "Looking"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "under_review"
    assert body["assigned_to_id"] == analyst.id
    assert body["notes"][0]["status_change"] == "detected->under_review"
