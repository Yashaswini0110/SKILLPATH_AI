from fastapi.testclient import TestClient

from app.db.seed import catalog_assessment_id, catalog_role_id, catalog_skill_id
from tests.conftest import auth_header, register_user
from tests.test_assessments import _answers


def test_twin_requires_auth(client: TestClient) -> None:
    response = client.get("/api/v1/twin")
    assert response.status_code == 401


def test_twin_requires_a_target(client: TestClient, unique_email: str) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    response = client.get("/api/v1/twin", headers=headers)
    assert response.status_code == 422


def test_twin_joins_profile_and_gaps_without_changing_target(
    client: TestClient, unique_email: str
) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    client.put(
        "/api/v1/employees/me",
        headers=headers,
        json={"target_role_id": str(catalog_role_id("ML Engineer"))},
    )
    client.post(
        "/api/v1/employees/me/skills",
        headers=headers,
        json={"skill_id": str(catalog_skill_id("Python")), "current_level": 4},
    )
    path = client.get("/api/v1/learning-paths", headers=headers)
    assert path.status_code == 200, path.text
    original_target = path.json()["data"]["target"]["title"]

    response = client.get("/api/v1/twin", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()["data"]
    assert body["target"]["title"] == "ML Engineer"
    assert "github is not collected" in body["disclaimer"].lower()
    assert "not a hiring" in body["disclaimer"].lower()
    assert body["github_collected"] is False
    by_name = {item["skill"]["canonical_name"]: item for item in body["skills"]}
    assert "Python" in by_name
    assert "Deep Learning" in by_name
    python = by_name["Python"]
    assert python["in_target"] is True
    assert float(python["current_level"]) >= 4
    assert python["priority"] == "NONE"
    assert python["trend"] == "INSUFFICIENT_DATA"
    sources = {item["source_type"]: item for item in python["evidence_sources"]}
    assert sources["SELF"]["present"] is True
    assert sources["GITHUB"]["present"] is False
    assert float(by_name["Deep Learning"]["current_level"]) == 0
    assert by_name["Deep Learning"]["priority"] == "CRITICAL"
    assert body["open_gap_count"] >= 1

    profile = client.get("/api/v1/employees/me", headers=headers)
    assert profile.json()["data"]["target_role"]["title"] == "ML Engineer"
    again = client.get("/api/v1/learning-paths", headers=headers)
    assert again.json()["data"]["target"]["title"] == original_target


def test_twin_trend_improves_after_quiz(client: TestClient, unique_email: str) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    client.put(
        "/api/v1/employees/me",
        headers=headers,
        json={"target_role_id": str(catalog_role_id("Software Engineer"))},
    )
    client.post(
        "/api/v1/employees/me/skills",
        headers=headers,
        json={"skill_id": str(catalog_skill_id("Python")), "current_level": 2},
    )
    quiz_id = str(catalog_assessment_id("Python"))
    submitted = client.post(
        f"/api/v1/assessments/{quiz_id}/attempts",
        headers=headers,
        json={"answers": _answers("Python", correct=True)},
    )
    assert submitted.status_code == 200, submitted.text

    response = client.get("/api/v1/twin", headers=headers)
    assert response.status_code == 200, response.text
    python = next(
        item
        for item in response.json()["data"]["skills"]
        if item["skill"]["canonical_name"] == "Python"
    )
    sources = {item["source_type"]: item for item in python["evidence_sources"]}
    assert sources["SELF"]["present"] is True
    assert sources["ASSESSMENT"]["present"] is True
    assert sources["GITHUB"]["present"] is False
    assert python["trend"] == "IMPROVING"
    assert len(python["history"]) >= 2
    assert float(python["history"][0]["level"]) == 2
    assert float(python["history"][-1]["level"]) == 5
