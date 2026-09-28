from fastapi.testclient import TestClient

from tests.conftest import auth_header, register_user


def test_education_crud(client: TestClient, unique_email: str) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    payload = {
        "degree": "B.S. Computer Science",
        "institution": "State University",
        "field_of_study": "Computer Science",
        "start_year": 2018,
        "end_year": 2022,
    }
    created_edu = client.post(
        "/api/v1/employees/me/education", headers=headers, json=payload
    )
    assert created_edu.status_code == 201, created_edu.text
    education_id = created_edu.json()["data"]["id"]

    listed = client.get("/api/v1/employees/me/education", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()["data"]) == 1

    updated = client.put(
        f"/api/v1/employees/me/education/{education_id}",
        headers=headers,
        json={"institution": "Tech University"},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["institution"] == "Tech University"

    deleted = client.delete(
        f"/api/v1/employees/me/education/{education_id}", headers=headers
    )
    assert deleted.status_code == 200
    listed_after = client.get("/api/v1/employees/me/education", headers=headers)
    assert listed_after.json()["data"] == []


def test_education_rejects_inverted_years(
    client: TestClient, unique_email: str
) -> None:
    created = register_user(client, unique_email)
    response = client.post(
        "/api/v1/employees/me/education",
        headers=auth_header(created["tokens"]["access_token"]),
        json={
            "degree": "B.S.",
            "institution": "State",
            "start_year": 2022,
            "end_year": 2018,
        },
    )
    assert response.status_code == 422
