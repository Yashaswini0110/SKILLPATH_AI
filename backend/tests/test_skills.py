from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.seed import catalog_skill_id
from tests.conftest import auth_header, page_items, register_user


def test_skill_catalog_and_employee_skills(
    client: TestClient, unique_email: str
) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])

    catalog = client.get("/api/v1/skills", headers=headers)
    assert catalog.status_code == 200
    assert len(page_items(catalog)) >= 10

    python_id = str(catalog_skill_id("Python"))
    added = client.post(
        "/api/v1/employees/me/skills",
        headers=headers,
        json={"skill_id": python_id, "current_level": 4},
    )
    assert added.status_code == 201, added.text
    body = added.json()["data"]
    assert body["skill"]["name"] == "Python"
    assert float(body["current_level"]) == 4.0
    assert float(body["confidence"]) == settings.self_declaration_reliability
    assert body["source_type"] == "SELF"
    assert body["inferred"] is False

    duplicate = client.post(
        "/api/v1/employees/me/skills",
        headers=headers,
        json={"skill_id": python_id, "current_level": 3},
    )
    assert duplicate.status_code == 409

    skill_row_id = body["id"]
    updated = client.put(
        f"/api/v1/employees/me/skills/{skill_row_id}",
        headers=headers,
        json={"current_level": 4.5},
    )
    assert updated.status_code == 200
    assert float(updated.json()["data"]["current_level"]) == 4.5

    deleted = client.delete(
        f"/api/v1/employees/me/skills/{skill_row_id}", headers=headers
    )
    assert deleted.status_code == 200


def test_skill_level_out_of_range(client: TestClient, unique_email: str) -> None:
    created = register_user(client, unique_email)
    response = client.post(
        "/api/v1/employees/me/skills",
        headers=auth_header(created["tokens"]["access_token"]),
        json={"skill_id": str(catalog_skill_id("Python")), "current_level": 6},
    )
    assert response.status_code == 422
