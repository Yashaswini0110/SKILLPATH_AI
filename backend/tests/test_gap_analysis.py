from fastapi.testclient import TestClient

from app.db.seed import catalog_role_id, catalog_skill_id
from tests.conftest import auth_header, register_user

SAMPLE_JD = """
Senior ML Engineer

Requirements
- Expert Python
- Machine Learning
- Deep Learning
"""


def test_gap_analysis_uses_target_role(client: TestClient, unique_email: str) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    role_id = str(catalog_role_id("ML Engineer"))
    client.put(
        "/api/v1/employees/me",
        headers=headers,
        json={"target_role_id": role_id},
    )
    client.post(
        "/api/v1/employees/me/skills",
        headers=headers,
        json={"skill_id": str(catalog_skill_id("Python")), "current_level": 4},
    )

    response = client.get("/api/v1/gap-analysis", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()["data"]
    assert body["target"]["title"] == "ML Engineer"
    by_name = {item["skill"]["canonical_name"]: item for item in body["gaps"]}
    assert float(by_name["Python"]["gap_basic"]) == 0
    assert by_name["Python"]["priority"] == "NONE"
    assert float(by_name["Deep Learning"]["current_level"]) == 0
    assert float(by_name["Deep Learning"]["gap_basic"]) == 4
    assert by_name["Deep Learning"]["priority"] == "CRITICAL"
    assert body["critical_count"] >= 1


def test_gap_analysis_accepts_job_description(
    client: TestClient, unique_email: str
) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    analyzed = client.post(
        "/api/v1/job-descriptions",
        headers=headers,
        json={"title": "Sample ML JD", "text": SAMPLE_JD},
    )
    assert analyzed.status_code == 201, analyzed.text
    jd_id = analyzed.json()["data"]["id"]
    response = client.get(
        "/api/v1/gap-analysis",
        headers=headers,
        params={"job_description_id": jd_id},
    )
    assert response.status_code == 200, response.text
    body = response.json()["data"]
    assert body["target"]["type"] == "JOB_DESCRIPTION"
    names = {item["skill"]["canonical_name"] for item in body["gaps"]}
    assert "Python" in names
    assert "Machine Learning" in names


def test_gap_analysis_requires_a_target(client: TestClient, unique_email: str) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    response = client.get("/api/v1/gap-analysis", headers=headers)
    assert response.status_code == 422


def test_gap_analysis_rejects_both_targets(
    client: TestClient, unique_email: str
) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    analyzed = client.post(
        "/api/v1/job-descriptions",
        headers=headers,
        json={"title": "Sample ML JD", "text": SAMPLE_JD},
    )
    assert analyzed.status_code == 201, analyzed.text
    response = client.get(
        "/api/v1/gap-analysis",
        headers=headers,
        params={
            "role_id": str(catalog_role_id("ML Engineer")),
            "job_description_id": analyzed.json()["data"]["id"],
        },
    )
    assert response.status_code == 422


def test_gap_analysis_accepts_role_id_query(
    client: TestClient, unique_email: str
) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    response = client.get(
        "/api/v1/gap-analysis",
        headers=headers,
        params={"role_id": str(catalog_role_id("ML Engineer"))},
    )
    assert response.status_code == 200, response.text
    body = response.json()["data"]
    assert body["target"]["type"] == "ROLE"
    assert body["target"]["title"] == "ML Engineer"


def test_gap_analysis_requires_auth(client: TestClient) -> None:
    response = client.get("/api/v1/gap-analysis")
    assert response.status_code == 401
