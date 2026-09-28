from fastapi.testclient import TestClient

from tests.conftest import auth_header, register_user


def test_register_login_and_me(client: TestClient, unique_email: str) -> None:
    created = register_user(client, unique_email)
    assert created["user"]["email"] == unique_email
    assert created["user"]["role"] == "EMPLOYEE"
    assert created["tokens"]["token_type"] == "bearer"
    assert created["tokens"]["expires_in"] == 15 * 60

    login = client.post(
        "/api/v1/auth/login",
        json={"email": unique_email, "password": "Password1"},
    )
    assert login.status_code == 200, login.text
    token = login.json()["data"]["tokens"]["access_token"]

    me = client.get(" /api/v1/auth/me".strip(), headers=auth_header(token))
    assert me.status_code == 200
    assert me.json()["data"]["email"] == unique_email


def test_register_duplicate_email(client: TestClient, unique_email: str) -> None:
    register_user(client, unique_email)
    again = client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email.upper(),
            "password": "Password1",
            "full_name": "Other Person",
            "role": "EMPLOYEE",
        },
    )
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "CONFLICT"


def test_login_rejects_wrong_password(client: TestClient, unique_email: str) -> None:
    register_user(client, unique_email)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": unique_email, "password": "WrongPass1"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_refresh_rotates_token(client: TestClient, unique_email: str) -> None:
    created = register_user(client, unique_email)
    refresh = created["tokens"]["refresh_token"]
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert response.status_code == 200
    new_refresh = response.json()["data"]["tokens"]["refresh_token"]
    assert new_refresh != refresh

    reused = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert reused.status_code == 401


def test_logout_revokes_refresh_token(client: TestClient, unique_email: str) -> None:
    created = register_user(client, unique_email)
    access = created["tokens"]["access_token"]
    refresh = created["tokens"]["refresh_token"]
    logout = client.post(
        "/api/v1/auth/logout",
        headers=auth_header(access),
        json={"refresh_token": refresh},
    )
    assert logout.status_code == 200
    reused = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert reused.status_code == 401
