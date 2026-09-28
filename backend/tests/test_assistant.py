from fastapi.testclient import TestClient
from llm.assistant import answer, classify_intent
from llm.client import complete, grounded_prompt
from llm.retrieve import Chunk, retrieve
from llm.verbalize import verbalize

from app.db.seed import catalog_role_id
from tests.conftest import auth_header, register_user


def _chunk(
    source_type: str,
    title: str,
    text: str,
    score: float = 0.5,
    facts: dict[str, str] | None = None,
) -> Chunk:
    return Chunk(
        source_type=source_type,
        title=title,
        text=text,
        score=score,
        facts=facts or {},
    )


def test_next_step_uses_stored_path_not_catalog() -> None:
    result = answer(
        "What should I learn next?",
        [
            _chunk("PROFILE", "Learner profile", "Target role is ML Engineer."),
            _chunk(
                "PATH",
                "Statistics",
                "Position 1: Statistics. Statistics is a missing foundation.",
            ),
            _chunk(
                "COURSE",
                "Transformers and Attention",
                "Self-attention stacks.",
            ),
        ],
    )
    assert result.unavailable is False
    assert "Statistics" in result.text
    assert "Transformers and Attention" not in result.text
    assert "I think" not in result.text.lower()


def test_explain_uses_catalog_and_does_not_invent() -> None:
    result = answer(
        "Explain transformers.",
        [
            _chunk(
                "SKILL",
                "Transformers",
                "Transformers: Attention-based sequence models.",
            ),
            _chunk("GAP", "Python", "Python is an open skill gap."),
        ],
    )
    assert result.unavailable is False
    assert result.text.startswith("Transformers are")
    assert "attention-based sequence models" in result.text.lower()
    assert "From the catalog" not in result.text
    assert "Python" not in result.text
    assert classify_intent("Explain transformers.") == "EXPLAIN"


def test_unknown_topic_is_unavailable() -> None:
    result = answer(
        "Explain quantum basketweaving.",
        [
            _chunk(
                "SKILL",
                "Transformers",
                "Transformers: Attention-based sequence models.",
            )
        ],
    )
    assert result.unavailable is True
    assert "invent" in result.text.lower() or "don't have" in result.text.lower()
    assert "Attention-based" not in result.text


def test_project_for_rag_uses_catalog_title() -> None:
    result = answer(
        "Give me a project for RAG.",
        [
            _chunk(
                "SKILL",
                "RAG",
                "Retrieval-Augmented Generation: Retrieval-augmented generation.",
            ),
            _chunk(
                "PROJECT",
                "Document Q&A System",
                "Document Q&A System: Index a handbook. "
                "Skills: Retrieval-Augmented Generation.",
            ),
        ],
    )
    assert result.unavailable is False
    assert result.text.startswith("The catalog project for RAG")
    assert "Document Q&A System" in result.text
    assert "From the catalog" not in result.text
    assert "Invented RAG App" not in result.text


def test_why_need_statistics_from_gap() -> None:
    result = answer(
        "Why do I need Statistics?",
        [
            _chunk(
                "GAP",
                "Statistics",
                "Statistics is an open skill gap for Data Scientist. "
                "Current 0.0/5, required 4/5, priority Critical.",
                facts={
                    "skill": "Statistics",
                    "role": "Data Scientist",
                    "current": "0.0",
                    "required": "4",
                    "priority": "Critical",
                },
            )
        ],
    )
    assert "Statistics" in result.text
    assert "Data Scientist" in result.text
    assert "critical gap" in result.text.lower()
    assert result.unavailable is False


def test_path_for_now_uses_stored_path_not_catalog() -> None:
    question = "what is my learning path for now?"
    assert classify_intent(question) == "PATH"
    result = answer(
        question,
        [
            _chunk(
                "PATH_OVERVIEW",
                "Learning path",
                "Stored learning path for ML Engineer starts with Statistics.",
                facts={
                    "target": "ML Engineer",
                    "start": "Statistics",
                    "sequence": "Statistics → Python → Machine Learning",
                    "hours_per_week": "10",
                    "weeks": "8",
                },
            ),
            _chunk(
                "PATH",
                "Statistics",
                "Position 1: Statistics. Missing foundation.",
                facts={"skill": "Statistics", "reason": "Missing foundation."},
            ),
            _chunk(
                "SKILL",
                "Transformers",
                "Transformers: Attention-based sequence models.",
            ),
        ],
    )
    assert result.unavailable is False
    assert "ML Engineer" in result.text
    assert "Statistics" in result.text
    assert "catalog description" not in result.text.lower()
    assert "From the catalog" not in result.text


def test_why_rec_skips_tiny_semantic_dump() -> None:
    result = answer(
        "Why was Git Collaboration recommended?",
        [
            _chunk(
                "RECOMMENDATION",
                "Git Collaboration",
                "Git Collaboration is stored at rank 1 because it addresses "
                "the Git gap (critical).",
                facts={
                    "title": "Git Collaboration",
                    "gap": "Git",
                    "priority": "Critical",
                    "rank": "1",
                    "prerequisite": "Prerequisites are satisfied.",
                    "difficulty": "Difficulty matches learner level.",
                    "verbalization": (
                        "Stored ranking facts, not an LLM guess. "
                        "Semantic similarity = 0.05. Format fit = 0.50."
                    ),
                },
            )
        ],
    )
    assert result.unavailable is False
    assert "top stored course" in result.text.lower()
    assert "Git gap" in result.text
    assert "semantic similarity" not in result.text.lower()
    assert "0.05" not in result.text
    assert "format fit" not in result.text.lower()


def test_complete_without_key_returns_none() -> None:
    prompt = grounded_prompt(
        "What next?", ["Position 1: Docker."], draft="Start with Docker."
    )
    assert "Docker" in prompt
    assert "Draft:" in prompt
    assert complete(prompt, enabled=True, api_key="") is None
    assert complete(prompt, enabled=False, api_key="secret") is None


def test_complete_reads_nim_message_content(monkeypatch) -> None:
    import json

    from llm import client as llm_client

    class _Response:
        def read(self) -> bytes:
            payload = {
                "choices": [{"message": {"content": "Start with Docker."}}]
            }
            return json.dumps(payload).encode()

        def __enter__(self) -> "_Response":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

    monkeypatch.setattr(
        llm_client.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: _Response(),
    )
    text = complete(
        "Rephrase: Start with Docker.",
        enabled=True,
        api_key="test-key",
        timeout=5,
    )
    assert text == "Start with Docker."


def test_complete_http_error_returns_none(monkeypatch) -> None:
    import urllib.error

    from llm import client as llm_client

    def _raise(*_args: object, **_kwargs: object) -> None:
        raise urllib.error.URLError("timeout")

    monkeypatch.setattr(llm_client.urllib.request, "urlopen", _raise)
    assert complete("Start with Docker.", enabled=True, api_key="test-key") is None


def test_retrieve_ranks_transformers_for_explain() -> None:
    chunks = [
        _chunk("SKILL", "SQL", "SQL: Query language.", 0),
        _chunk(
            "SKILL",
            "Transformers",
            "Transformers: Attention-based sequence models.",
            0,
        ),
    ]
    ranked = retrieve("explain transformers", chunks, keep_learner=False, limit=3)
    assert ranked
    assert ranked[0].title == "Transformers"


def test_verbalize_still_does_not_invent() -> None:
    class Fact:
        text = "Addresses RAG gap."

    assert "Document Q&A" not in verbalize([Fact()], use_llm=True)


def _set_role(client: TestClient, headers: dict[str, str], title: str) -> None:
    client.put(
        "/api/v1/employees/me",
        headers=headers,
        json={"target_role_id": str(catalog_role_id(title))},
    )


def test_assistant_requires_auth(client: TestClient) -> None:
    response = client.post("/api/v1/assistant/ask", json={"question": "What next?"})
    assert response.status_code == 401


def test_assistant_next_without_role_does_not_invent(
    client: TestClient, unique_email: str
) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    response = client.post(
        "/api/v1/assistant/ask",
        headers=headers,
        json={"question": "What should I learn next?"},
    )
    assert response.status_code == 200, response.text
    body = response.json()["data"]
    assert body["unavailable"] is True
    assert "deep learning" not in body["answer"].lower()
    assert unique_email not in body["answer"]
    assert unique_email not in str(body["sources"])


def test_assistant_next_after_path(client: TestClient, unique_email: str) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    _set_role(client, headers, "ML Engineer")
    path = client.get("/api/v1/learning-paths", headers=headers)
    assert path.status_code == 200, path.text
    first = path.json()["data"]["steps"][0]["skill"]["canonical_name"]
    response = client.post(
        "/api/v1/assistant/ask",
        headers=headers,
        json={"question": "What should I learn next?"},
    )
    assert response.status_code == 200, response.text
    body = response.json()["data"]
    assert body["unavailable"] is False
    assert first in body["answer"]
    assert "i think" not in body["answer"].lower()

    path_now = client.post(
        "/api/v1/assistant/ask",
        headers=headers,
        json={"question": "what is my learning path for now?"},
    )
    assert path_now.status_code == 200, path_now.text
    path_body = path_now.json()["data"]
    assert path_body["unavailable"] is False
    assert first in path_body["answer"]
    assert "catalog description" not in path_body["answer"].lower()


def test_assistant_explain_and_project_and_unknown(
    client: TestClient, unique_email: str
) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    explain = client.post(
        "/api/v1/assistant/ask",
        headers=headers,
        json={"question": "Explain transformers."},
    )
    assert explain.status_code == 200, explain.text
    explain_body = explain.json()["data"]
    assert explain_body["unavailable"] is False
    assert "attention" in explain_body["answer"].lower()
    assert "from the catalog" not in explain_body["answer"].lower()

    project = client.post(
        "/api/v1/assistant/ask",
        headers=headers,
        json={"question": "Give me a project for RAG."},
    )
    assert project.status_code == 200, project.text
    project_body = project.json()["data"]
    assert project_body["unavailable"] is False
    assert "Document Q&A System" in project_body["answer"]

    unknown = client.post(
        "/api/v1/assistant/ask",
        headers=headers,
        json={"question": "Explain quantum basketweaving."},
    )
    assert unknown.status_code == 200, unknown.text
    assert unknown.json()["data"]["unavailable"] is True
    assert "Document Q&A" not in unknown.json()["data"]["answer"]


def test_assistant_why_need_and_why_recommended(
    client: TestClient, unique_email: str
) -> None:
    created = register_user(client, unique_email)
    headers = auth_header(created["tokens"]["access_token"])
    _set_role(client, headers, "Data Scientist")
    need = client.post(
        "/api/v1/assistant/ask",
        headers=headers,
        json={"question": "Why do I need Statistics?"},
    )
    assert need.status_code == 200, need.text
    need_body = need.json()["data"]
    assert need_body["unavailable"] is False
    assert "Statistics" in need_body["answer"]

    ranked = client.get("/api/v1/recommendations/courses", headers=headers)
    assert ranked.status_code == 200, ranked.text
    title = ranked.json()["data"]["items"][0]["course"]["title"]
    why = client.post(
        "/api/v1/assistant/ask",
        headers=headers,
        json={"question": f"Why was {title} recommended?"},
    )
    assert why.status_code == 200, why.text
    why_body = why.json()["data"]
    assert why_body["unavailable"] is False
    assert title in why_body["answer"] or "gap" in why_body["answer"].lower()

    turns = client.get("/api/v1/assistant/turns", headers=headers)
    assert turns.status_code == 200, turns.text
    assert len(turns.json()["data"]) >= 2
