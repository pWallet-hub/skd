from sqlalchemy import func, select

from app.models import SystemSetting, User
from app.models.enums import UserRole
from app.scripts import seed as demo_seed
from tests.conftest import auth


def test_change_password(client, make_user):
    user = make_user(email="pw@example.com", password="old-password")
    url = "/api/v1/auth/change-password"
    bad = client.post(
        url, headers=auth(user), json={"current_password": "nope", "new_password": "new-password"}
    )
    assert bad.status_code == 400
    ok = client.post(
        url,
        headers=auth(user),
        json={"current_password": "old-password", "new_password": "new-password"},
    )
    assert ok.status_code == 204
    login = client.post(
        "/api/v1/auth/login", json={"email": "pw@example.com", "password": "new-password"}
    )
    assert login.status_code == 200


def test_update_profile(client, make_user):
    user = make_user()
    r = client.patch(
        "/api/v1/auth/me",
        headers=auth(user),
        json={"full_name": "New Name", "phone_number": "+250 1"},
    )
    assert r.json()["full_name"] == "New Name" and r.json()["phone_number"] == "+250 1"


def test_auto_seed_loads_refreshes_and_protects_real_data(db, make_user):
    # 1) empty database -> demo data is loaded and versioned
    demo_seed.auto(db)
    assert db.get(SystemSetting, demo_seed.DEMO_VERSION_KEY).value == demo_seed.DEMO_DATA_VERSION
    families = db.scalar(select(func.count(User.id)).where(User.role == UserRole.PARENT))
    assert families == demo_seed.NUM_FAMILIES

    # 2) same version -> untouched
    marker = make_user(email="marker@example.com")
    demo_seed.auto(db)
    assert db.get(User, marker.id) is not None

    # 3) older version, demo-only accounts -> refreshed (marker demo account wiped)
    db.get(SystemSetting, demo_seed.DEMO_VERSION_KEY).value = "old"
    db.commit()
    demo_seed.auto(db)
    db.expire_all()
    assert db.scalar(select(User).where(User.email == "marker@example.com")) is None

    # 4) a real (non-demo) account exists -> never touched, even if the version is old
    real = make_user(email="someone@realmail.org")
    db.get(SystemSetting, demo_seed.DEMO_VERSION_KEY).value = "old"
    db.commit()
    demo_seed.auto(db)
    db.expire_all()
    assert db.scalar(select(User).where(User.email == "someone@realmail.org")).id == real.id
