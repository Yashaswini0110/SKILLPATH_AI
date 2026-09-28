from fastapi.testclient import TestClient

from app.db.seed import catalog_role_id
from tests.conftest import auth_header, register_user


def test_profile_get_and_update(client: TestClient, unique_email: str) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])

    profile = client.get("/api/v1/employees/me", headers=headers)
    assert profile.status_code == 200
    body = profile.json()["data"]
    assert body["email"] == unique_email
    assert body["available_hours_per_week"] == 10
    assert body["completeness"]["score"] == 0

    updated = client.put(
        "/api/v1/employees/me",
        headers=headers,
        json={
            "job_title": "Software Engineer",
            "department": "Platform",
            "years_experience": 2.0,
            "available_hours_per_week": 10,
            "learning_preferences": {
                "formats": ["video", "hands-on"],
                "pace": "moderate",
            },
            "target_role_id": str(catalog_role_id("ML Engineer")),
        },
    )
    assert updated.status_code == 200, updated.text
    data = updated.json()["data"]
    assert data["job_title"] == "Software Engineer"
    assert data["target_role"]["title"] == "ML Engineer"
    assert data["completeness"]["breakdown"]["job_title"] is True
    assert data["completeness"]["breakdown"]["target_role"] is True
    assert data["learning_preferences"]["formats"] == ["video", "hands-on"]


def test_unknown_target_role_is_rejected(client: TestClient, unique_email: str) -> None:
    created = register_user(client, unique_email)
    response = client.put(
        "/api/v1/employees/me",
        headers=auth_header(created["tokens"]["access_token"]),
        json={"target_role_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert response.status_code == 404
