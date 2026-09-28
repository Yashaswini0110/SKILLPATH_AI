from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.seed import catalog_role_id
from app.models import MentorMatch
from tests.conftest import auth_header, register_user


def test_mentor_matches_require_gaps_and_auth(
    client: TestClient, unique_email: str
) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    missing = client.get("/api/v1/recommendations/mentor-matches", headers=headers)
    assert missing.status_code == 422
    unauth = client.get("/api/v1/recommendations/mentor-matches")
    assert unauth.status_code == 401


def test_genai_mentor_match_explains_overlap(
    client: TestClient, unique_email: str, db_session: Session
) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    client.put(
        "/api/v1/employees/me",
        headers=headers,
        json={"target_role_id": str(catalog_role_id("GenAI Engineer"))},
    )

    response = client.get("/api/v1/recommendations/mentor-matches", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()["data"]
    assert body["target"]["title"] == "GenAI Engineer"
    assert body["items"]
    top = body["items"][0]
    assert top["mentor"]["name"] == "Sara Chen"
    why = top["why"]
    assert why["matched_gap_count"] >= 3
    assert why["top_gap_count"] == 5
    names = {item["name"] for item in why["matched_skills"]}
    assert {"RAG", "LLMs"}.issubset(names)
    assert why["available_hours_per_month"] == 10
    assert why["open_mentee_slots"] == 4
    assert "skill gaps match" in top["reason"]
    assert "available hours/month" in top["reason"]
    assert top["explanation"]["facts"]
    assert top["explanation"]["verbalization"] == top["reason"]

    db_session.expire_all()
    stored = db_session.scalars(select(MentorMatch)).all()
    assert len(stored) == len(body["items"])
    assert stored[0].why["matched_gap_count"] >= 3
