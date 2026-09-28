from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.seed import catalog_role_id, catalog_skill_id
from app.models import LearningPath, LearningPathStep
from tests.conftest import auth_header, register_user

PLAYBOOK = [
    "Statistics",
    "Machine Learning",
    "Deep Learning",
    "Transformers",
    "LLMs",
    "RAG",
]


def test_learning_path_requires_gaps_and_auth(
    client: TestClient, unique_email: str
) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    missing = client.get("/api/v1/learning-paths", headers=headers)
    assert missing.status_code == 422
    unauth = client.get("/api/v1/learning-paths")
    assert unauth.status_code == 401


def test_genai_path_keeps_playbook_order(
    client: TestClient, unique_email: str, db_session: Session
) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    client.put(
        "/api/v1/employees/me",
        headers=headers,
        json={"target_role_id": str(catalog_role_id("GenAI Engineer"))},
    )

    response = client.get(
        "/api/v1/learning-paths",
        headers=headers,
        params={"method": "TOPOLOGICAL"},
    )
    assert response.status_code == 200, response.text
    body = response.json()["data"]
    assert body["target"]["title"] == "GenAI Engineer"
    assert body["method"] == "TOPOLOGICAL"
    assert body["prerequisite_violation_count"] == 0
    names = [item["skill"]["name"] for item in body["steps"]]
    order = {name: index for index, name in enumerate(names)}
    for earlier, later in zip(PLAYBOOK, PLAYBOOK[1:], strict=False):
        assert earlier in order
        assert later in order
        assert order[earlier] < order[later]
    rag = next(item for item in body["steps"] if item["skill"]["name"] == "RAG")
    assert rag["kind"] == "GAP"
    assert rag["stage"] == "ADVANCED"
    assert rag["status"] == "NOT_STARTED"
    assert 1 <= rag["difficulty"] <= 5
    assert rag["course"]["title"] == "Retrieval-Augmented Generation"
    assert "open skill gap" in rag["reason"].lower() or "RAG" in rag["reason"]
    assert rag["explanation"]["facts"]
    shown = rag["skill"]["canonical_name"]
    assert any(shown in item["text"] for item in rag["explanation"]["facts"])
    stats = next(
        item for item in body["steps"] if item["skill"]["name"] == "Statistics"
    )
    assert stats["stage"] == "FOUNDATION"
    ml = next(
        item for item in body["steps"] if item["skill"]["name"] == "Machine Learning"
    )
    assert ml["stage"] == "CORE"
    for item in body["steps"]:
        assert item["status"] == "NOT_STARTED"
        assert 1 <= item["difficulty"] <= 5
        assert item["stage"] in {"FOUNDATION", "CORE", "ADVANCED"}

    db_session.expire_all()
    stored = db_session.scalars(select(LearningPath)).all()
    assert len(stored) == 1
    assert stored[0].prerequisite_violation_count == 0
    steps = db_session.scalars(select(LearningPathStep)).all()
    assert len(steps) == len(body["steps"])


def test_known_foundation_is_skipped(client: TestClient, unique_email: str) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    client.put(
        "/api/v1/employees/me",
        headers=headers,
        json={"target_role_id": str(catalog_role_id("GenAI Engineer"))},
    )
    client.post(
        "/api/v1/employees/me/skills",
        headers=headers,
        json={"skill_id": str(catalog_skill_id("Statistics")), "current_level": 5},
    )

    response = client.get(
        "/api/v1/learning-paths",
        headers=headers,
        params={"method": "TOPOLOGICAL"},
    )
    assert response.status_code == 200, response.text
    body = response.json()["data"]
    names = [item["skill"]["name"] for item in body["steps"]]
    assert "Statistics" not in names
    assert "Statistics" in body["skipped_foundations"]
    order = {name: index for index, name in enumerate(names)}
    assert order["Machine Learning"] < order["RAG"]
    assert body["prerequisite_violation_count"] == 0
