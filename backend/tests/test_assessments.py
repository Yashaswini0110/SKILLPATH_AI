from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import SkillSourceType
from app.db.seed import (
    catalog_assessment_id,
    catalog_question_id,
    catalog_role_id,
    catalog_skill_id,
    load_assessments,
)
from app.models import Evidence
from tests.conftest import auth_header, page_items, register_user


def _answers(skill: str, *, correct: bool) -> list[dict]:
    bank = next(item for item in load_assessments() if item["skill"] == skill)
    return _answers_correct_count(skill, len(bank["questions"]) if correct else 0)


def _answers_correct_count(skill: str, correct_count: int) -> list[dict]:
    bank = next(item for item in load_assessments() if item["skill"] == skill)
    payload: list[dict] = []
    for position, question in enumerate(bank["questions"], start=1):
        index = int(question["correct_index"])
        payload.append(
            {
                "question_id": str(catalog_question_id(skill, position)),
                "selected_index": (
                    index
                    if position <= correct_count
                    else (index + 1) % len(question["choices"])
                ),
            }
        )
    return payload


def test_assessment_requires_auth(client: TestClient) -> None:
    listing = client.get("/api/v1/assessments")
    assert listing.status_code == 401
    quiz_id = catalog_assessment_id("Python")
    detail = client.get(f"/api/v1/assessments/{quiz_id}")
    assert detail.status_code == 401


def test_python_quiz_hides_answers_until_submit(
    client: TestClient, unique_email: str, db_session: Session
) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    quiz_id = str(catalog_assessment_id("Python"))

    listing = client.get("/api/v1/assessments", headers=headers)
    assert listing.status_code == 200, listing.text
    titles = {item["skill"]["name"]: item for item in page_items(listing)}
    assert "Python" in titles
    assert titles["Python"]["attempt_count"] == 0

    detail = client.get(f"/api/v1/assessments/{quiz_id}", headers=headers)
    assert detail.status_code == 200, detail.text
    body = detail.json()["data"]
    assert body["title"] == "Python quiz"
    for question in body["questions"]:
        assert "correct_index" not in question
        assert "explanation" not in question
        assert len(question["choices"]) == 4

    first = client.post(
        f"/api/v1/assessments/{quiz_id}/attempts",
        headers=headers,
        json={"answers": _answers("Python", correct=True)},
    )
    assert first.status_code == 200, first.text
    result = first.json()["data"]
    assert result["passed"] is True
    assert result["percent"] == 1.0
    assert result["extracted_level"] == 5.0
    assert result["path_effect"] == "SKIP"
    assert result["answers"][0]["is_correct"] is True

    db_session.expire_all()
    evidence = db_session.scalars(
        select(Evidence).where(Evidence.source_type == SkillSourceType.ASSESSMENT.value)
    ).all()
    assert len(evidence) == 1
    assert evidence[0].source_id is not None
    first_id = evidence[0].id

    second = client.post(
        f"/api/v1/assessments/{quiz_id}/attempts",
        headers=headers,
        json={"answers": _answers("Python", correct=False)},
    )
    assert second.status_code == 200, second.text
    assert second.json()["data"]["passed"] is False
    assert second.json()["data"]["path_effect"] == "REFRESHER"
    db_session.expire_all()
    evidence = db_session.scalars(
        select(Evidence).where(Evidence.source_type == SkillSourceType.ASSESSMENT.value)
    ).all()
    assert len(evidence) == 2
    assert first_id in {row.id for row in evidence}


def test_passed_quiz_marks_path_step_complete(
    client: TestClient, unique_email: str
) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    client.put(
        "/api/v1/employees/me",
        headers=headers,
        json={
            "target_role_id": str(catalog_role_id("Backend Engineer")),
            "available_hours_per_week": 10,
        },
    )
    client.post(
        "/api/v1/employees/me/skills",
        headers=headers,
        json={"skill_id": str(catalog_skill_id("Python")), "current_level": 1},
    )

    quiz_id = str(catalog_assessment_id("Python"))
    submitted = client.post(
        f"/api/v1/assessments/{quiz_id}/attempts",
        headers=headers,
        json={"answers": _answers("Python", correct=True)},
    )
    assert submitted.status_code == 200, submitted.text

    profile = client.get("/api/v1/employees/me/skill-profile", headers=headers)
    assert profile.status_code == 200, profile.text
    python = next(
        item
        for item in profile.json()["data"]["skills"]
        if item["skill"]["name"] == "Python"
    )
    sources = {row["source_type"] for row in python["evidence"]}
    assert "ASSESSMENT" in sources
    assert "SELF" in sources
    assert float(python["current_level"]) > 1.0

    path = client.get(
        "/api/v1/learning-paths",
        headers=headers,
        params={"method": "TOPOLOGICAL"},
    )
    assert path.status_code == 200, path.text
    body = path.json()["data"]
    names = [item["skill"]["name"] for item in body["steps"]]
    skip = next(
        (item for item in body["adaptations"] if item["skill"] == "Python"), None
    )
    assert skip is not None
    assert skip["action"] == "SKIP"
    if "Python" in names:
        step = next(item for item in body["steps"] if item["skill"]["name"] == "Python")
        assert step["status"] == "COMPLETED"
        assert step["assessment_id"] == quiz_id
    else:
        assert (
            "Python" in body["skipped_foundations"]
            or float(python["current_level"]) >= 4
        )


def test_failed_quiz_keeps_skill_in_progress_on_the_path(
    client: TestClient, unique_email: str
) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    client.put(
        "/api/v1/employees/me",
        headers=headers,
        json={"target_role_id": str(catalog_role_id("Backend Engineer"))},
    )
    before = client.get(
        "/api/v1/learning-paths",
        headers=headers,
        params={"method": "TOPOLOGICAL"},
    )
    assert before.status_code == 200, before.text
    before_steps = {
        item["skill"]["name"]: item for item in before.json()["data"]["steps"]
    }
    python_hours = before_steps["Python"]["duration_hours"]
    fastapi_week = before_steps["FastAPI"]["week_start"]

    quiz_id = str(catalog_assessment_id("Python"))
    submitted = client.post(
        f"/api/v1/assessments/{quiz_id}/attempts",
        headers=headers,
        json={"answers": _answers("Python", correct=False)},
    )
    assert submitted.status_code == 200, submitted.text
    assert submitted.json()["data"]["passed"] is False
    assert submitted.json()["data"]["path_effect"] == "REFRESHER"

    path = client.get(
        "/api/v1/learning-paths",
        headers=headers,
        params={"method": "TOPOLOGICAL"},
    )
    assert path.status_code == 200, path.text
    body = path.json()["data"]
    step = next(item for item in body["steps"] if item["skill"]["name"] == "Python")
    fastapi = next(item for item in body["steps"] if item["skill"]["name"] == "FastAPI")
    assert step["status"] == "IN_PROGRESS"
    assert step["assessment_id"] == quiz_id
    assert step["kind"] == "REFRESHER"
    refresh = next(item for item in body["adaptations"] if item["skill"] == "Python")
    assert refresh["action"] == "REFRESHER"
    assert refresh["extra_hours"] >= 4
    assert step["duration_hours"] == python_hours + refresh["extra_hours"]
    assert (
        fastapi["week_start"] > fastapi_week
        or fastapi["week_end"] > before_steps["FastAPI"]["week_end"]
        or step["week_end"] > before_steps["Python"]["week_end"]
    )


def test_mid_score_quiz_does_not_skip_or_add_review(
    client: TestClient, unique_email: str
) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    client.put(
        "/api/v1/employees/me",
        headers=headers,
        json={"target_role_id": str(catalog_role_id("Backend Engineer"))},
    )
    quiz_id = str(catalog_assessment_id("Python"))
    submitted = client.post(
        f"/api/v1/assessments/{quiz_id}/attempts",
        headers=headers,
        json={"answers": _answers_correct_count("Python", 3)},
    )
    assert submitted.status_code == 200, submitted.text
    result = submitted.json()["data"]
    assert result["percent"] == 0.75
    assert result["passed"] is True
    assert result["path_effect"] is None

    path = client.get(
        "/api/v1/learning-paths",
        headers=headers,
        params={"method": "TOPOLOGICAL"},
    )
    assert path.status_code == 200, path.text
    actions = {
        item["skill"]: item["action"] for item in path.json()["data"]["adaptations"]
    }
    assert actions.get("Python") not in {"SKIP", "REFRESHER"}


def test_strong_quiz_keeps_later_skills_on_the_path(
    client: TestClient, unique_email: str
) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    client.put(
        "/api/v1/employees/me",
        headers=headers,
        json={"target_role_id": str(catalog_role_id("Backend Engineer"))},
    )
    quiz_id = str(catalog_assessment_id("Python"))
    submitted = client.post(
        f"/api/v1/assessments/{quiz_id}/attempts",
        headers=headers,
        json={"answers": _answers("Python", correct=True)},
    )
    assert submitted.status_code == 200, submitted.text
    assert submitted.json()["data"]["path_effect"] == "SKIP"

    path = client.get(
        "/api/v1/learning-paths",
        headers=headers,
        params={"method": "TOPOLOGICAL"},
    )
    assert path.status_code == 200, path.text
    body = path.json()["data"]
    names = [item["skill"]["name"] for item in body["steps"]]
    skip = next(item for item in body["adaptations"] if item["skill"] == "Python")
    assert skip["action"] == "SKIP"
    assert "Python" not in names
    assert "Python" in body["skipped_foundations"]
    assert "FastAPI" in names
