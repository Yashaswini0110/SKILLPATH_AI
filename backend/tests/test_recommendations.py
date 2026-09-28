from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.seed import catalog_role_id, catalog_skill_id
from app.models import RecommendationResult
from tests.conftest import auth_header, register_user


def _ready_for_gaps(client: TestClient, headers: dict[str, str]) -> None:
    client.put(
        "/api/v1/employees/me",
        headers=headers,
        json={"target_role_id": str(catalog_role_id("ML Engineer"))},
    )


def test_content_recommendations_match_open_gaps(
    client: TestClient, unique_email: str, db_session: Session
) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    _ready_for_gaps(client, headers)

    response = client.get(
        "/api/v1/recommendations/courses",
        headers=headers,
        params={"method": "CONTENT"},
    )
    assert response.status_code == 200, response.text
    body = response.json()["data"]
    assert body["method"] == "CONTENT"
    assert body["resource_type"] == "COURSE"
    assert body["items"]
    top = body["items"][0]
    assert top["rank"] == 1
    assert "content" in top["components"]
    assert top["matched_skills"]
    names = {item["skill"]["canonical_name"] for item in top["matched_skills"]}
    assert names.intersection({"Deep Learning", "Machine Learning", "MLOps", "Python"})

    db_session.expire_all()
    stored = db_session.scalars(select(RecommendationResult)).all()
    assert len(stored) == len(body["items"])
    assert stored[0].batch_id is not None


def test_popularity_and_semantic_endpoints(
    client: TestClient, unique_email: str
) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    _ready_for_gaps(client, headers)

    popular = client.get(
        "/api/v1/recommendations/projects",
        headers=headers,
        params={"method": "POPULARITY"},
    )
    assert popular.status_code == 200, popular.text
    assert popular.json()["data"]["method"] == "POPULARITY"

    semantic = client.get(
        "/api/v1/recommendations/mentors",
        headers=headers,
        params={"method": "SEMANTIC"},
    )
    assert semantic.status_code == 200, semantic.text
    data = semantic.json()["data"]
    assert data["method"] == "SEMANTIC"
    assert data["encoder"] == "hashing"

    graph = client.get(
        "/api/v1/recommendations/courses",
        headers=headers,
        params={"method": "KG"},
    )
    assert graph.status_code == 200, graph.text
    assert graph.json()["data"]["method"] == "KG"
    assert graph.json()["data"]["items"][0]["components"]["kg"] is not None


def test_recommendations_require_gaps_and_auth(
    client: TestClient, unique_email: str
) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    missing = client.get("/api/v1/recommendations/courses", headers=headers)
    assert missing.status_code == 422
    unauth = client.get("/api/v1/recommendations/courses")
    assert unauth.status_code == 401


HYBRID_KEYS = (
    "semantic",
    "gap",
    "prerequisite",
    "difficulty",
    "preference",
    "collaborative",
    "kg",
)


def test_hybrid_recommendations_persist_seven_signals(
    client: TestClient, unique_email: str, db_session: Session
) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    client.put(
        "/api/v1/employees/me",
        headers=headers,
        json={
            "target_role_id": str(catalog_role_id("ML Engineer")),
            "learning_preferences": {"formats": ["video", "hands-on"]},
        },
    )
    client.post(
        "/api/v1/employees/me/skills",
        headers=headers,
        json={
            "skill_id": str(catalog_skill_id("Python")),
            "current_level": 4,
        },
    )

    response = client.get("/api/v1/recommendations/courses", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()["data"]
    assert body["method"] == "HYBRID"
    assert body["encoder"] == "hashing"
    assert body["items"]
    weights = body["weights"]
    assert set(weights) == set(HYBRID_KEYS)
    top = body["items"][0]
    for key in HYBRID_KEYS:
        assert key in top["components"]
        assert 0.0 <= float(top["components"][key]) <= 1.0
    expected = sum(weights[key] * float(top["components"][key]) for key in HYBRID_KEYS)
    expected /= sum(weights.values())
    assert abs(float(top["score"]) - expected) < 0.0015
    facts = {item["key"]: item["text"] for item in top["explanation"]["facts"]}
    assert "gap" in facts
    assert "rank" in facts
    assert facts["rank"] == "Ranking position = 1."
    assert top["explanation"]["verbalization"]
    assert "i think" not in top["explanation"]["verbalization"].lower()

    content = client.get(
        "/api/v1/recommendations/courses",
        headers=headers,
        params={"method": "CONTENT"},
    )
    assert content.status_code == 200
    content_ids = [item["course"]["id"] for item in content.json()["data"]["items"]]
    hybrid_ids = [item["course"]["id"] for item in body["items"]]
    assert hybrid_ids
    assert content_ids
    assert hybrid_ids != content_ids or float(top["components"]["final"]) != float(
        top["components"]["content"]
    )

    db_session.expire_all()
    stored = db_session.scalars(
        select(RecommendationResult).where(RecommendationResult.method == "HYBRID")
    ).all()
    assert stored
    assert all(key in stored[0].components for key in HYBRID_KEYS)
    assert stored[0].explanation
    assert stored[0].explanation.get("facts")
