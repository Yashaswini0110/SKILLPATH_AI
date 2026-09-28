from fastapi.testclient import TestClient

from tests.conftest import auth_header, register_user


def test_experience_crud(client: TestClient, unique_email: str) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    payload = {
        "company": "Acme Corp",
        "role_title": "Software Engineer",
        "description": "Built internal APIs.",
        "start_date": "2023-01-01",
        "is_current": True,
    }
    created_exp = client.post(
        "/api/v1/employees/me/experience", headers=headers, json=payload
    )
    assert created_exp.status_code == 201, created_exp.text
    experience_id = created_exp.json()["data"]["id"]
    assert created_exp.json()["data"]["end_date"] is None

    listed = client.get("/api/v1/employees/me/experience", headers=headers)
    assert len(listed.json()["data"]) == 1

    updated = client.put(
        f"/api/v1/employees/me/experience/{experience_id}",
        headers=headers,
        json={
            "is_current": False,
            "end_date": "2024-06-01",
            "role_title": "Senior Software Engineer",
        },
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["data"]["role_title"] == "Senior Software Engineer"
    assert updated.json()["data"]["end_date"] == "2024-06-01"

    deleted = client.delete(
        f"/api/v1/employees/me/experience/{experience_id}", headers=headers
    )
    assert deleted.status_code == 200


def test_experience_requires_end_date_when_not_current(
    client: TestClient, unique_email: str
) -> None:
    created = register_user(client, unique_email)
    response = client.post(
        "/api/v1/employees/me/experience",
        headers=auth_header(created["tokens"]["access_token"]),
        json={
            "company": "Acme",
            "role_title": "Engineer",
            "start_date": "2023-01-01",
            "is_current": False,
        },
    )
    assert response.status_code == 422
