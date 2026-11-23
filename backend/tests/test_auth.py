from app.models.enums import UserRole


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_register_login_and_me(client):
    payload = {"email": "Parent@Example.com", "password": "password123", "full_name": "Parent One"}
    r = client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 201
    assert r.json()["role"] == UserRole.PARENT
    assert r.json()["email"] == "parent@example.com"

    assert client.post("/api/v1/auth/register", json=payload).status_code == 409

    tokens = client.post(
        "/api/v1/auth/login", json={"email": "parent@example.com", "password": "password123"}
    ).json()
    me = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert me.status_code == 200
    assert me.json()["full_name"] == "Parent One"

    refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 200


def test_wrong_password_rejected(client, make_user):
    make_user(email="a@example.com")
    r = client.post("/api/v1/auth/login", json={"email": "a@example.com", "password": "nope-nope"})
    assert r.status_code == 401


def test_refresh_token_cannot_be_used_as_access_token(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "b@example.com", "password": "password123", "full_name": "B B"},
    )
    tokens = client.post(
        "/api/v1/auth/login", json={"email": "b@example.com", "password": "password123"}
    ).json()
    r = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['refresh_token']}"}
    )
    assert r.status_code == 401
