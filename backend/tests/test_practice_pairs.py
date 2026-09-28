from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.seed import catalog_role_id
from app.models import PracticePairing
from tests.conftest import auth_header, register_user


def test_practice_pairs_require_gaps_and_auth(
    client: TestClient, unique_email: str
) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    missing = client.get("/api/v1/recommendations/practice-pairs", headers=headers)
    assert missing.status_code == 422
    unauth = client.get("/api/v1/recommendations/practice-pairs")
    assert unauth.status_code == 401


def test_genai_pairs_rag_course_then_document_qa(
    client: TestClient, unique_email: str, db_session: Session
) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    client.put(
        "/api/v1/employees/me",
        headers=headers,
        json={"target_role_id": str(catalog_role_id("GenAI Engineer"))},
    )

    response = client.get("/api/v1/recommendations/practice-pairs", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()["data"]
    assert body["target"]["title"] == "GenAI Engineer"
    assert body["items"]
    assert body["weights"]["skills_addressed"] == 1.0

    names = {item["skill"]["name"]: item for item in body["items"]}
    assert "RAG" in names
    rag = names["RAG"]
    assert rag["course"]["title"] == "Retrieval-Augmented Generation"
    assert rag["project"]["title"] == "Document Q&A System"
    assert "learn" in rag["reason"].lower()
    assert "practice" in rag["reason"].lower()
    assert rag["explanation"]["facts"]
    shown = rag["skill"]["canonical_name"]
    assert any(shown in item["text"] for item in rag["explanation"]["facts"])
    course_ids = {item["course"]["id"] for item in body["items"]}
    project_ids = {item["project"]["id"] for item in body["items"]}
    assert len(course_ids) == len(body["items"])
    assert len(project_ids) == len(body["items"])

    db_session.expire_all()
    stored = db_session.scalars(select(PracticePairing)).all()
    assert len(stored) == len(body["items"])
    assert stored[0].batch_id is not None
    assert "skills_addressed" in stored[0].components["project"]
