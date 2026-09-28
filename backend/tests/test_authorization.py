from fastapi.testclient import TestClient

from tests.conftest import auth_header, register_user


def test_me_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_refresh_token_cannot_be_used_as_access_token(
    client: TestClient, unique_email: str
) -> None:
    created = register_user(client, unique_email)
    refresh = created["tokens"]["refresh_token"]
    response = client.get("/api/v1/auth/me", headers=auth_header(refresh))
    assert response.status_code == 401


def test_invalid_token_is_rejected(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me", headers=auth_header("not-a-jwt"))
    assert response.status_code == 401


def test_employee_cannot_call_admin_ping(client: TestClient, unique_email: str) -> None:
    created = register_user(client, unique_email, role="EMPLOYEE")
    response = client.get(
        "/api/v1/admin/ping",
        headers=auth_header(created["tokens"]["access_token"]),
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_hr_admin_can_call_admin_ping(client: TestClient, unique_email: str) -> None:
    created = register_user(client, unique_email, role="HR_ADMIN")
    response = client.get(
        "/api/v1/admin/ping",
        headers=auth_header(created["tokens"]["access_token"]),
    )
    assert response.status_code == 200
    assert response.json()["data"]["role"] == "HR_ADMIN"


def test_user_cannot_mutate_another_users_education(client: TestClient) -> None:
    first = register_user(client, "owner@example.com")
    second = register_user(client, "other@example.com")
    created = client.post(
        "/api/v1/employees/me/education",
        headers=auth_header(first["tokens"]["access_token"]),
        json={
            "degree": "B.S.",
            "institution": "State University",
            "start_year": 2018,
            "end_year": 2022,
        },
    )
    assert created.status_code == 201
    education_id = created.json()["data"]["id"]
    deleted = client.delete(
        f"/api/v1/employees/me/education/{education_id}",
        headers=auth_header(second["tokens"]["access_token"]),
    )
    assert deleted.status_code == 404
