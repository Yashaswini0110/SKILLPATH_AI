import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.paths import ensure_repo_on_path
from app.db.seed import catalog_skill_id
from app.services.graph_service import graph_service
from tests.conftest import auth_header, register_user

ensure_repo_on_path()

from knowledge_graph.client import GraphClient  # noqa: E402


def _graph_available() -> bool:
    client = GraphClient(
        settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password
    )
    try:
        return client.verify()
    finally:
        client.close()


def test_graph_requires_auth(client: TestClient) -> None:
    response = client.get("/api/v1/graph/status")
    assert response.status_code == 401


def test_graph_skill_neighborhood(
    client: TestClient, unique_email: str, db_session: Session
) -> None:
    if not _graph_available():
        pytest.skip("Neo4j is not available for tests")
    graph_service.sync(db_session)
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    status = client.get("/api/v1/graph/status", headers=headers)
    assert status.status_code == 200, status.text
    body = status.json()["data"]
    assert body["acyclic"] is True
    assert body["nodes"]["Skill"] >= 32

    rag_id = str(catalog_skill_id("RAG"))
    view = client.get(f"/api/v1/graph/skills/{rag_id}", headers=headers)
    assert view.status_code == 200, view.text
    data = view.json()["data"]
    names = [item["name"] for item in data["chain"]]
    assert names[-1] == "RAG"
    assert names.index("Statistics") < names.index("Machine Learning")
    assert names.index("LLMs") < names.index("RAG")
    assert data["prerequisites"]
    sources = {
        item["source"]["name"]
        for item in data["edges"]
        if item["target"]["name"] == "RAG"
    }
    assert sources == {"LLMs", "Vector Databases"}
    assert len(data["layers"][-1]) == 1

    dl_id = str(catalog_skill_id("Deep Learning"))
    dl = client.get(f"/api/v1/graph/skills/{dl_id}", headers=headers)
    assert dl.status_code == 200, dl.text
    payload = dl.json()["data"]
    assert payload["courses"]
    assert payload["projects"]
    assert payload["mentors"]
