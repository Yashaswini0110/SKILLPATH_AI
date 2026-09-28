from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import EmployeeSkill, Evidence
from tests.conftest import auth_header, register_user

SAMPLE = (
    Path(__file__).resolve().parents[2] / "datasets" / "synthetic" / "sample_jd.txt"
)


def test_paste_jd_classifies_through_taxonomy(
    client: TestClient, unique_email: str, db_session: Session
) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    response = client.post(
        "/api/v1/job-descriptions",
        headers=headers,
        json={"text": SAMPLE.read_text(encoding="utf-8")},
    )
    assert response.status_code == 201, response.text
    body = response.json()["data"]
    assert body["title"] == "Senior ML Engineer"
    assert body["source_type"] == "PASTE"
    assert float(body["weights"]["required"]) == 1.0
    assert float(body["weights"]["preferred"]) == 0.6
    assert float(body["weights"]["mentioned"]) == 0.4

    by_name = {item["skill"]["canonical_name"]: item for item in body["skills"]}
    assert by_name["Python"]["requirement"] == "REQUIRED"
    assert float(by_name["Python"]["importance"]) == 1.0
    assert by_name["FastAPI"]["requirement"] == "REQUIRED"
    assert by_name["Amazon Web Services"]["requirement"] == "PREFERRED"
    assert by_name["Kubernetes"]["requirement"] == "PREFERRED"
    assert by_name["Natural Language Processing"]["requirement"] == "PREFERRED"
    assert by_name["Git"]["requirement"] == "MENTIONED"
    assert "quantum knitting" not in {name.lower() for name in by_name}
    assert "TensorFlow" not in by_name

    listed = client.get("/api/v1/job-descriptions", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["data"][0]["skill_count"] == body["skill_count"]

    detail = client.get(f"/api/v1/job-descriptions/{body['id']}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["data"]["title"] == "Senior ML Engineer"

    db_session.expire_all()
    assert db_session.scalar(select(EmployeeSkill.id)) is None
    assert db_session.scalar(select(Evidence.id)) is None


def test_upload_jd_txt(client: TestClient, unique_email: str) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    response = client.post(
        "/api/v1/job-descriptions/upload",
        headers=headers,
        files={"file": ("sample_jd.txt", SAMPLE.read_bytes(), "text/plain")},
        data={"title": "Uploaded ML role"},
    )
    assert response.status_code == 201, response.text
    body = response.json()["data"]
    assert body["title"] == "Uploaded ML role"
    assert body["source_type"] == "FILE"
    names = {item["skill"]["canonical_name"] for item in body["skills"]}
    assert "Python" in names
    assert "Docker" in names


def test_jd_requires_auth(client: TestClient) -> None:
    response = client.post(
        "/api/v1/job-descriptions",
        json={"text": "Requirements\nPython and Docker for production services.\n"},
    )
    assert response.status_code == 401


def test_jd_rejects_short_text(client: TestClient, unique_email: str) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    response = client.post(
        "/api/v1/job-descriptions",
        headers=headers,
        json={"text": "too short"},
    )
    assert response.status_code == 422


def test_jd_weights_follow_settings(
    client: TestClient, unique_email: str, monkeypatch
) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "jd_weight_required", 0.9)
    monkeypatch.setattr(settings, "jd_weight_preferred", 0.5)
    monkeypatch.setattr(settings, "jd_weight_mentioned", 0.2)

    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    response = client.post(
        "/api/v1/job-descriptions",
        headers=headers,
        json={"text": SAMPLE.read_text(encoding="utf-8")},
    )
    assert response.status_code == 201, response.text
    body = response.json()["data"]
    assert float(body["weights"]["required"]) == 0.9
    by_name = {item["skill"]["canonical_name"]: item for item in body["skills"]}
    assert float(by_name["Python"]["importance"]) == 0.9
    assert float(by_name["Kubernetes"]["importance"]) == 0.5
    assert float(by_name["Git"]["importance"]) == 0.2
