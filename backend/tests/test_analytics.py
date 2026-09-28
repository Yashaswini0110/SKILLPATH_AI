from fastapi.testclient import TestClient

from app.db.seed import catalog_role_id, catalog_skill_id
from tests.conftest import auth_header, register_user


def _headers(client: TestClient, email: str, role: str = "EMPLOYEE") -> dict[str, str]:
    created = register_user(client, email, full_name=email.split("@")[0], role=role)
    return auth_header(created["tokens"]["access_token"])


def _profile(
    client: TestClient,
    headers: dict[str, str],
    department: str,
    role_title: str | None = None,
) -> None:
    payload: dict[str, str] = {"department": department}
    if role_title is not None:
        payload["target_role_id"] = str(catalog_role_id(role_title))
    client.put("/api/v1/employees/me", headers=headers, json=payload)


def _skill(client: TestClient, headers: dict[str, str], name: str, level: int) -> None:
    client.post(
        "/api/v1/employees/me/skills",
        headers=headers,
        json={"skill_id": str(catalog_skill_id(name)), "current_level": level},
    )


def test_analytics_requires_auth(client: TestClient) -> None:
    response = client.get("/api/v1/analytics")
    assert response.status_code == 401


def test_employee_cannot_read_analytics(client: TestClient) -> None:
    headers = _headers(client, "learner@example.com")
    response = client.get("/api/v1/analytics", headers=headers)
    assert response.status_code == 403


def test_manager_needs_department(client: TestClient) -> None:
    headers = _headers(client, "bare-manager@example.com", role="MANAGER")
    response = client.get("/api/v1/analytics", headers=headers)
    assert response.status_code == 422


def test_manager_sees_department_aggregates_without_identities(
    client: TestClient,
) -> None:
    manager = _headers(client, "team-lead@example.com", role="MANAGER")
    alice = _headers(client, "alice-eng@example.com")
    bob = _headers(client, "bob-eng@example.com")
    other = _headers(client, "sales-rep@example.com")
    _profile(client, manager, "Engineering", "ML Engineer")
    _profile(client, alice, "Engineering", "ML Engineer")
    _profile(client, bob, "Engineering", "ML Engineer")
    _profile(client, other, "Sales", "Software Engineer")
    _skill(client, alice, "Python", 4)
    _skill(client, bob, "Python", 2)
    _skill(client, other, "Python", 5)
    client.get("/api/v1/learning-paths", headers=alice)

    response = client.get("/api/v1/analytics", headers=manager)
    assert response.status_code == 200, response.text
    body = response.json()["data"]
    raw = response.text.lower()
    assert "alice-eng@example.com" not in raw
    assert "bob-eng" not in raw
    assert "sales-rep" not in raw
    assert "not a hiring" in body["disclaimer"].lower()
    assert body["github_collected"] is False
    assert body["scope"]["type"] == "DEPARTMENT"
    assert body["scope"]["label"] == "Engineering"
    assert body["employee_count"] == 3
    assert body["departments"] == []
    python = next(
        item for item in body["heatmap"] if item["skill"]["canonical_name"] == "Python"
    )
    assert python["band_4"] + python["band_2"] == 2
    assert python["band_5"] == 0
    assert python["missing_count"] >= 1
    assert body["learning_progress"]["employees_with_paths"] >= 1
    gaps = {item["skill"]["canonical_name"] for item in body["top_gaps"]}
    assert "Deep Learning" in gaps or body["top_gaps"]


def test_manager_cannot_query_another_department(client: TestClient) -> None:
    manager = _headers(client, "eng-lead@example.com", role="MANAGER")
    _profile(client, manager, "Engineering")
    response = client.get(
        "/api/v1/analytics", headers=manager, params={"department": "Sales"}
    )
    assert response.status_code == 403


def test_hr_sees_org_and_can_filter_department(client: TestClient) -> None:
    hr = _headers(client, "hr-admin@example.com", role="HR_ADMIN")
    eng = _headers(client, "eng-one@example.com")
    sales = _headers(client, "sales-one@example.com")
    _profile(client, hr, "People")
    _profile(client, eng, "Engineering", "ML Engineer")
    _profile(client, sales, "Sales", "Software Engineer")
    _skill(client, eng, "Python", 3)

    org = client.get("/api/v1/analytics", headers=hr)
    assert org.status_code == 200, org.text
    body = org.json()["data"]
    assert body["scope"]["type"] == "ORG"
    assert body["employee_count"] == 3
    names = {item["department"] for item in body["departments"]}
    assert "Engineering" in names
    assert "Sales" in names
    assert "hr-admin@example.com" not in org.text.lower()
    titles = {item["title"] for item in body["frameworks"]}
    assert "ML Engineer" in titles

    sliced = client.get(
        "/api/v1/analytics", headers=hr, params={"department": "Engineering"}
    )
    assert sliced.status_code == 200, sliced.text
    slice_body = sliced.json()["data"]
    assert slice_body["scope"]["type"] == "DEPARTMENT"
    assert slice_body["employee_count"] == 1
    assert slice_body["departments"] == []
