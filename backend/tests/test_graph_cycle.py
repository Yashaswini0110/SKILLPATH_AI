import json
from pathlib import Path

from knowledge_graph.cycle import ancestor_subgraph, find_cycles, topological_chain


def _edges() -> list[tuple[str, str]]:
    path = (
        Path(__file__).resolve().parents[2]
        / "datasets"
        / "processed"
        / "skill_prerequisites.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [(src, dst) for src, dst in payload["prerequisites"]]


def test_seeded_prerequisite_graph_is_acyclic() -> None:
    assert find_cycles(_edges()) == []


def test_cycle_detection_finds_loop() -> None:
    edges = _edges() + [("RAG", "Statistics")]
    cycles = find_cycles(edges)
    assert cycles
    joined = " ".join("->".join(cycle) for cycle in cycles)
    assert "RAG" in joined and "Statistics" in joined


def test_rag_chain_keeps_playbook_order() -> None:
    chain = topological_chain(_edges(), "RAG")
    assert chain[-1] == "RAG"
    order = {name: index for index, name in enumerate(chain)}
    assert order["Statistics"] < order["Machine Learning"]
    assert order["Machine Learning"] < order["Deep Learning"]
    assert order["Deep Learning"] < order["Transformers"]
    assert order["Transformers"] < order["LLMs"]
    assert order["LLMs"] < order["RAG"]


def test_rag_subgraph_branches_instead_of_a_single_path() -> None:
    layers, edges = ancestor_subgraph(_edges(), "RAG")
    incoming = [src for src, dst in edges if dst == "RAG"]
    assert set(incoming) == {"LLMs", "Vector Databases"}
    assert layers[-1] == ["RAG"]
    assert len(edges) > len(layers) - 1
