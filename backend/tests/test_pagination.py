from fastapi.testclient import TestClient

from app.core.config import settings
from tests.conftest import auth_header, page_items, register_user


def test_skills_are_paginated_and_sorted(client: TestClient, unique_email: str) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    first = client.get(
        "/api/v1/skills",
        headers=headers,
        params={"page": 1, "page_size": 5, "sort": "canonical_name", "order": "asc"},
    )
    assert first.status_code == 200, first.text
    body = first.json()["data"]
    assert body["page"] == 1
    assert body["page_size"] == 5
    assert body["total"] >= 10
    assert body["total_pages"] >= 2
    names = [item["canonical_name"] for item in body["items"]]
    assert names == sorted(names)
    assert len(body["items"]) == 5

    second = client.get(
        "/api/v1/skills",
        headers=headers,
        params={"page": 2, "page_size": 5, "sort": "canonical_name"},
    )
    later = [item["canonical_name"] for item in page_items(second)]
    assert later
    assert later[0] >= names[-1]


def test_invalid_sort_is_rejected(client: TestClient, unique_email: str) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    response = client.get(
        "/api/v1/courses", headers=headers, params={"sort": "not-a-field"}
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_rate_limit_returns_envelope(client: TestClient, unique_email: str) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    settings.rate_limit_enabled = True
    settings.rate_limit_requests = 3
    settings.rate_limit_window_seconds = 60
    try:
        codes = [
            client.get("/api/v1/roles", headers=headers).status_code for _ in range(5)
        ]
        assert 429 in codes
        limited = client.get("/api/v1/roles", headers=headers)
        assert limited.status_code == 429
        assert limited.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    finally:
        settings.rate_limit_enabled = False
        settings.rate_limit_requests = 120
