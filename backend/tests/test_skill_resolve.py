from fastapi.testclient import TestClient

from app.db.seed import catalog_skill_id
from tests.conftest import auth_header, page_items, register_user


def test_catalog_includes_aliases_and_canonical_names(
    client: TestClient, unique_email: str
) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])

    catalog = client.get("/api/v1/skills", headers=headers)
    assert catalog.status_code == 200
    skills = page_items(catalog)
    machine_learning = next(
        item for item in skills if item["name"] == "Machine Learning"
    )
    nlp = next(item for item in skills if item["name"] == "NLP")
    assert machine_learning["canonical_name"] == "Machine Learning"
    assert "ML" in machine_learning["aliases"]
    assert machine_learning["difficulty"] >= 1
    assert nlp["canonical_name"] == "Natural Language Processing"

    filtered = client.get(
        "/api/v1/skills", headers=headers, params={"category": "GenAI"}
    )
    assert filtered.status_code == 200
    assert page_items(filtered)
    assert all(item["category"] == "GenAI" for item in page_items(filtered))


def test_resolve_exact_alias_unknown_and_collision_cases(
    client: TestClient, unique_email: str
) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    response = client.post(
        "/api/v1/skills/resolve",
        headers=headers,
        json={"mentions": ["ML", "machine-learning", "K8s", "quantum knitting"]},
    )
    assert response.status_code == 200, response.text
    results = {item["raw"]: item for item in response.json()["data"]["results"]}

    assert results["ML"]["canonical_name"] == "Machine Learning"
    assert results["ML"]["skill_id"] == str(catalog_skill_id("Machine Learning"))
    assert results["ML"]["match_type"] == "alias"
    assert results["ML"]["confidence"] == 0.9

    assert results["machine-learning"]["match_type"] == "exact"
    assert results["machine-learning"]["confidence"] == 1.0
    assert results["machine-learning"]["skill_id"] == results["ML"]["skill_id"]

    assert results["K8s"]["canonical_name"] == "Kubernetes"
    assert results["K8s"]["match_type"] == "alias"

    assert results["quantum knitting"]["match_type"] == "unmatched"
    assert results["quantum knitting"]["skill_id"] is None
    assert results["quantum knitting"]["confidence"] == 0.0


def test_resolve_requires_auth(client: TestClient) -> None:
    response = client.post("/api/v1/skills/resolve", json={"mentions": ["Python"]})
    assert response.status_code == 401
