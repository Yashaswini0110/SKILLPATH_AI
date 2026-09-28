from fastapi.testclient import TestClient

from app.db.seed import catalog_role_id
from tests.conftest import auth_header, register_user


def test_ortools_respects_hour_budget_and_compares_methods(
    client: TestClient, unique_email: str
) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    client.put(
        "/api/v1/employees/me",
        headers=headers,
        json={
            "target_role_id": str(catalog_role_id("GenAI Engineer")),
            "available_hours_per_week": 10,
        },
    )

    response = client.get(
        "/api/v1/learning-paths",
        headers=headers,
        params={"method": "ORTOOLS", "deadline_weeks": 3},
    )
    assert response.status_code == 200, response.text
    body = response.json()["data"]
    assert body["method"] == "ORTOOLS"
    assert body["hours_per_week"] == 10
    assert body["deadline_weeks"] == 3
    assert body["capacity_hours"] == 30
    assert body["total_hours"] <= body["capacity_hours"]
    assert body["hours_violation_count"] == 0
    assert body["prerequisite_violation_count"] == 0
    assert body["duplicate_resource_count"] == 0
    methods = {item["method"]: item for item in body["comparison"]}
    assert set(methods) == {"ORTOOLS", "GREEDY", "TOPOLOGICAL"}
    assert methods["ORTOOLS"]["hours_violation_count"] == 0
    assert methods["GREEDY"]["hours_violation_count"] == 0
    assert methods["TOPOLOGICAL"]["total_hours"] >= methods["ORTOOLS"]["total_hours"]
    names = [item["skill"]["name"] for item in body["steps"]]
    assert names == list(dict.fromkeys(names))
    for step in body["steps"]:
        assert step["week_start"] >= 1
        assert step["week_end"] >= step["week_start"]
        assert step["duration_hours"] >= 0
        assert step["stage"] in {"FOUNDATION", "CORE", "ADVANCED"}
        assert step["status"] == "NOT_STARTED"
        assert 1 <= step["difficulty"] <= 5
