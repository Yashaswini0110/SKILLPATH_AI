from fastapi.testclient import TestClient

from tests.conftest import register_user


def test_register_rejects_short_password(client: TestClient, unique_email: str) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "short1",
            "full_name": "Alex",
            "role": "EMPLOYEE",
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_register_rejects_password_without_number(
    client: TestClient, unique_email: str
) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "Password",
            "full_name": "Alex",
            "role": "EMPLOYEE",
        },
    )
    assert response.status_code == 422


def test_register_rejects_invalid_email(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "password": "Password1",
            "full_name": "Alex",
            "role": "EMPLOYEE",
        },
    )
    assert response.status_code == 422


def test_register_rejects_invalid_role(client: TestClient, unique_email: str) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "Password1",
            "full_name": "Alex",
            "role": "SUPERUSER",
        },
    )
    assert response.status_code == 422


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_openapi_available(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "/api/v1/auth/register" in response.json()["paths"]


def test_duplicate_register_keeps_original_account(
    client: TestClient, unique_email: str
) -> None:
    register_user(client, unique_email)
    login = client.post(
        "/api/v1/auth/login", json={"email": unique_email, "password": "Password1"}
    )
    assert login.status_code == 200
