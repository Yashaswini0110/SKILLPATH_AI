from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import SkillSourceType
from app.db.seed import catalog_skill_id
from app.models import Evidence
from tests.conftest import auth_header, register_user

SAMPLE = (
    Path(__file__).resolve().parents[2] / "datasets" / "synthetic" / "sample_resume.txt"
)


def test_declared_skill_writes_self_evidence(
    client: TestClient, unique_email: str, db_session: Session
) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    python_id = str(catalog_skill_id("Python"))
    added = client.post(
        "/api/v1/employees/me/skills",
        headers=headers,
        json={"skill_id": python_id, "current_level": 4},
    )
    assert added.status_code == 201, added.text

    profile = client.get("/api/v1/employees/me/skill-profile", headers=headers)
    assert profile.status_code == 200, profile.text
    body = profile.json()["data"]
    python = next(
        item for item in body["skills"] if item["skill"]["canonical_name"] == "Python"
    )
    assert float(python["current_level"]) == 4.0
    assert float(python["confidence"]) == settings.self_declaration_reliability
    assert python["confidence_label"] == "LOW"
    assert python["conflict"] is False
    assert python["inferred_only"] is False
    assert python["evidence"][0]["source_type"] == "SELF"
    assert python["evidence"][0]["inferred"] is False

    db_session.expire_all()
    rows = db_session.scalars(
        select(Evidence).where(Evidence.source_type == SkillSourceType.SELF.value)
    ).all()
    assert len(rows) == 1


def test_resume_and_self_aggregate_and_can_conflict(
    client: TestClient, unique_email: str
) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    python_id = str(catalog_skill_id("Python"))
    client.post(
        "/api/v1/employees/me/skills",
        headers=headers,
        json={"skill_id": python_id, "current_level": 1},
    )
    upload = client.post(
        "/api/v1/employees/me/resumes",
        headers=headers,
        files={"file": ("sample_resume.txt", SAMPLE.read_bytes(), "text/plain")},
    )
    assert upload.status_code == 201, upload.text

    profile = client.get("/api/v1/employees/me/skill-profile", headers=headers)
    assert profile.status_code == 200, profile.text
    body = profile.json()["data"]
    assert body["skill_count"] >= 2
    python = next(
        item for item in body["skills"] if item["skill"]["canonical_name"] == "Python"
    )
    sources = {item["source_type"] for item in python["evidence"]}
    assert sources == {"SELF", "RESUME"}
    assert python["conflict"] is True
    assert python["recommend_assessment"] is True
    assert 1.0 < float(python["current_level"]) < 5.0
    assert float(python["confidence"]) > settings.self_declaration_reliability

    kubernetes = next(
        item
        for item in body["skills"]
        if item["skill"]["canonical_name"] == "Kubernetes"
    )
    assert kubernetes["inferred_only"] is True
    assert all(item["inferred"] for item in kubernetes["evidence"])


def test_deleting_self_skill_keeps_resume_evidence(
    client: TestClient, unique_email: str
) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    python_id = str(catalog_skill_id("Python"))
    added = client.post(
        "/api/v1/employees/me/skills",
        headers=headers,
        json={"skill_id": python_id, "current_level": 4},
    )
    skill_row_id = added.json()["data"]["id"]
    client.post(
        "/api/v1/employees/me/resumes",
        headers=headers,
        files={"file": ("sample_resume.txt", SAMPLE.read_bytes(), "text/plain")},
    )
    deleted = client.delete(
        f"/api/v1/employees/me/skills/{skill_row_id}", headers=headers
    )
    assert deleted.status_code == 200

    profile = client.get("/api/v1/employees/me/skill-profile", headers=headers)
    python = next(
        item
        for item in profile.json()["data"]["skills"]
        if item["skill"]["canonical_name"] == "Python"
    )
    assert {item["source_type"] for item in python["evidence"]} == {"RESUME"}
    assert python["inferred_only"] is True


def test_skill_profile_requires_auth(client: TestClient) -> None:
    response = client.get("/api/v1/employees/me/skill-profile")
    assert response.status_code == 401
