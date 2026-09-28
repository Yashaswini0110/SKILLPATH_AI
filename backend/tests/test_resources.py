from fastapi.testclient import TestClient

from app.db.seed import catalog_course_id, catalog_skill_id
from tests.conftest import auth_header, page_items, register_user


def test_resource_catalog_lists_courses_projects_mentors(
    client: TestClient, unique_email: str
) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])

    courses = client.get("/api/v1/courses", headers=headers)
    assert courses.status_code == 200, courses.text
    course_rows = page_items(courses)
    assert len(course_rows) >= 20
    titles = {row["title"] for row in course_rows}
    assert "Retrieval-Augmented Generation" in titles
    rag = next(
        row for row in course_rows if row["title"] == "Retrieval-Augmented Generation"
    )
    names = {item["skill"]["name"] for item in rag["skills"]}
    assert names == {"RAG", "Vector Databases", "LLMs"}

    projects = client.get("/api/v1/projects", headers=headers)
    assert projects.status_code == 200, projects.text
    assert len(page_items(projects)) >= 10

    mentors = client.get("/api/v1/mentors", headers=headers)
    assert mentors.status_code == 200, mentors.text
    mentor_rows = page_items(mentors)
    assert len(mentor_rows) >= 8
    assert any(row["name"] == "Sara Chen" for row in mentor_rows)


def test_resource_filter_by_skill(client: TestClient, unique_email: str) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    skill_id = str(catalog_skill_id("MLOps"))
    courses = client.get(
        "/api/v1/courses", headers=headers, params={"skill_id": skill_id}
    )
    assert courses.status_code == 200, courses.text
    rows = page_items(courses)
    assert rows
    for row in rows:
        assert any(item["skill"]["name"] == "MLOps" for item in row["skills"])


def test_course_detail_and_auth(client: TestClient, unique_email: str) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    course_id = catalog_course_id("Machine Learning Foundations")
    detail = client.get(f"/api/v1/courses/{course_id}", headers=headers)
    assert detail.status_code == 200, detail.text
    body = detail.json()["data"]
    assert body["provider"] == "SkillPath Academy"
    assert body["format"] == "video"
    assert any(item["skill"]["name"] == "Machine Learning" for item in body["skills"])

    missing = client.get("/api/v1/courses", headers=headers)
    assert missing.status_code == 200
    unauth = client.get("/api/v1/courses")
    assert unauth.status_code == 401
