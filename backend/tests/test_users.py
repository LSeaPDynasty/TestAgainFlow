"""User/auth API tests."""
from fastapi.testclient import TestClient


def test_user_register_login_me_flow(client: TestClient):
    reg = client.post(
        "/api/v1/users/register",
        json={"username": "alice", "password": "alice123", "role": "member"},
    )
    assert reg.status_code == 200
    assert reg.json()["code"] == 0

    login = client.post(
        "/api/v1/users/login",
        json={"username": "alice", "password": "alice123"},
    )
    assert login.status_code == 200
    body = login.json()
    assert body["code"] == 0
    token = body["data"]["access_token"]

    me = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["code"] == 0
    assert me.json()["data"]["username"] == "alice"


def test_users_list_requires_admin(client: TestClient):
    client.post(
        "/api/v1/users/register",
        json={"username": "admin1", "password": "admin123", "role": "admin"},
    )
    login = client.post(
        "/api/v1/users/login",
        json={"username": "admin1", "password": "admin123"},
    )
    token = login.json()["data"]["access_token"]

    users = client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
    assert users.status_code == 200
    assert users.json()["code"] == 0
    assert len(users.json()["data"]) >= 1
