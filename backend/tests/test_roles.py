from fastapi.testclient import TestClient

from app.db.seed import catalog_role_id
from tests.conftest import auth_header, page_items, register_user


def test_list_and_get_target_roles(client: TestClient, unique_email: str) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])

    listed = client.get("/api/v1/roles", headers=headers)
    assert listed.status_code == 200
    titles = {row["title"] for row in page_items(listed)}
    assert "ML Engineer" in titles
    assert "GenAI Engineer" in titles

    role_id = catalog_role_id("ML Engineer")
    detail = client.get(f"/api/v1/roles/{role_id}", headers=headers)
    assert detail.status_code == 200
    skills = detail.json()["data"]["skills"]
    assert len(skills) >= 3
    assert any(item["skill"]["name"] == "Machine Learning" for item in skills)
    assert any(item["requirement"] == "REQUIRED" for item in skills)
    assert any(item["requirement"] == "PREFERRED" for item in skills)
    weights = detail.json()["data"]["weights"]
    assert float(weights["required"]) == 1.0
    assert float(weights["preferred"]) == 0.6
    assert float(weights["mentioned"]) == 0.4
