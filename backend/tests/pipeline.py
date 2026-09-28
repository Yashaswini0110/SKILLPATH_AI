"""Shared learner-flow helpers for Phase 26 pipeline tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.db.seed import (
    catalog_assessment_id,
    catalog_question_id,
    catalog_role_id,
    load_assessments,
)
from tests.conftest import auth_header, register_user

SAMPLE_RESUME = (
    Path(__file__).resolve().parents[2] / "datasets" / "synthetic" / "sample_resume.txt"
)


def start_learner(client: TestClient, email: str) -> dict[str, str]:
    created = register_user(client, email)
    return auth_header(created["tokens"]["access_token"])


def upload_sample_resume(client: TestClient, headers: dict[str, str]) -> dict[str, Any]:
    response = client.post(
        "/api/v1/employees/me/resumes",
        headers=headers,
        files={"file": ("sample_resume.txt", SAMPLE_RESUME.read_bytes(), "text/plain")},
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def set_target_role(
    client: TestClient,
    headers: dict[str, str],
    title: str = "ML Engineer",
    hours: int = 10,
) -> dict[str, Any]:
    response = client.put(
        "/api/v1/employees/me",
        headers=headers,
        json={
            "target_role_id": str(catalog_role_id(title)),
            "available_hours_per_week": hours,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]


def skill_profile(client: TestClient, headers: dict[str, str]) -> dict[str, Any]:
    response = client.get("/api/v1/employees/me/skill-profile", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()["data"]


def gap_analysis(client: TestClient, headers: dict[str, str]) -> dict[str, Any]:
    response = client.get("/api/v1/gap-analysis", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()["data"]


def recommend_courses(client: TestClient, headers: dict[str, str]) -> dict[str, Any]:
    response = client.get("/api/v1/recommendations/courses", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()["data"]


def learning_path(
    client: TestClient, headers: dict[str, str], method: str = "TOPOLOGICAL"
) -> dict[str, Any]:
    response = client.get(
        "/api/v1/learning-paths",
        headers=headers,
        params={"method": method},
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]


def quiz_answers(skill: str, *, correct: bool = True) -> list[dict[str, Any]]:
    bank = next(item for item in load_assessments() if item["skill"] == skill)
    payload: list[dict[str, Any]] = []
    for position, question in enumerate(bank["questions"], start=1):
        index = int(question["correct_index"])
        payload.append(
            {
                "question_id": str(catalog_question_id(skill, position)),
                "selected_index": (
                    index if correct else (index + 1) % len(question["choices"])
                ),
            }
        )
    return payload


def submit_quiz(
    client: TestClient,
    headers: dict[str, str],
    skill: str,
    *,
    correct: bool = True,
) -> dict[str, Any]:
    quiz_id = str(catalog_assessment_id(skill))
    response = client.post(
        f"/api/v1/assessments/{quiz_id}/attempts",
        headers=headers,
        json={"answers": quiz_answers(skill, correct=correct)},
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]


def profile_names(profile: dict[str, Any]) -> set[str]:
    return {item["skill"]["canonical_name"] for item in profile["skills"]}


def open_gap_names(gaps: dict[str, Any]) -> set[str]:
    return {
        item["skill"]["canonical_name"]
        for item in gaps["gaps"]
        if float(item["gap_basic"]) > 0
    }


def rec_matched_names(recs: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for item in recs["items"]:
        names.update(
            skill["skill"]["canonical_name"] for skill in item["matched_skills"]
        )
    return names


def path_skill_names(path: dict[str, Any]) -> list[str]:
    return [item["skill"]["name"] for item in path["steps"]]


def assessed_skills() -> set[str]:
    return {item["skill"] for item in load_assessments()}
