from fastapi.testclient import TestClient

from app.db.seed import catalog_role_id
from tests.conftest import auth_header, register_user


def _set_role(client: TestClient, headers: dict[str, str], title: str) -> None:
    client.put(
        "/api/v1/employees/me",
        headers=headers,
        json={"target_role_id": str(catalog_role_id(title))},
    )


def test_whatif_requires_auth(client: TestClient) -> None:
    role_id = catalog_role_id("ML Engineer")
    response = client.get("/api/v1/what-if", params={"role_ids": str(role_id)})
    assert response.status_code == 401


def test_whatif_compares_roles_without_changing_target(
    client: TestClient, unique_email: str
) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    _set_role(client, headers, "Software Engineer")
    path = client.get("/api/v1/learning-paths", headers=headers)
    assert path.status_code == 200, path.text
    original = path.json()["data"]["target"]["title"]

    se_id = catalog_role_id("Software Engineer")
    ml_id = catalog_role_id("ML Engineer")
    response = client.get(
        "/api/v1/what-if",
        headers=headers,
        params=[("role_ids", str(se_id)), ("role_ids", str(ml_id))],
    )
    assert response.status_code == 200, response.text
    body = response.json()["data"]
    assert "not a hiring" in body["disclaimer"].lower()
    assert "employment" in body["disclaimer"].lower()
    assert len(body["scenarios"]) == 2
    titles = {item["role"]["title"]: item for item in body["scenarios"]}
    assert "Software Engineer" in titles
    assert "ML Engineer" in titles
    assert titles["Software Engineer"]["is_current"] is True
    assert titles["ML Engineer"]["is_current"] is False
    assert (
        titles["ML Engineer"]["open_gap_count"]
        >= titles["Software Engineer"]["open_gap_count"]
    )
    assert 0 <= titles["Software Engineer"]["coverage"] <= 1
    assert (
        titles["ML Engineer"]["path_skills"]
        or titles["ML Engineer"]["open_gap_count"] == 0
    )

    profile = client.get("/api/v1/employees/me", headers=headers)
    assert profile.json()["data"]["target_role"]["title"] == "Software Engineer"
    again = client.get("/api/v1/learning-paths", headers=headers)
    assert again.json()["data"]["target"]["title"] == original
