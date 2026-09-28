"""Upsert catalog nodes and PRD relationships into Neo4j."""

from __future__ import annotations

from typing import Any

from knowledge_graph.client import GraphClient
from knowledge_graph.schema import apply_schema

CATALOG_RELS = (
    "PREREQUISITE_OF",
    "RELATED_TO",
    "COMPLEMENTS",
    "TEACHES",
    "PRACTICES",
    "EXPERT_IN",
    "REQUIRES",
    "HAS_SKILL",
)


def sync_graph(client: GraphClient, payload: dict[str, Any]) -> None:
    def run(query: str, **params: Any) -> list[dict[str, Any]]:
        return client.run(query, **params)

    apply_schema(run)
    _clear_catalog_rels(run)
    _merge_nodes(run, "Skill", payload.get("skills", []))
    _merge_nodes(run, "Course", payload.get("courses", []))
    _merge_nodes(run, "Project", payload.get("projects", []))
    _merge_nodes(run, "Mentor", payload.get("mentors", []))
    _merge_nodes(run, "TargetRole", payload.get("roles", []))
    _merge_nodes(run, "Employee", payload.get("employees", []))
    _merge_rels(
        run, "Skill", "PREREQUISITE_OF", "Skill", payload.get("prerequisites", [])
    )
    _merge_rels(run, "Skill", "RELATED_TO", "Skill", payload.get("related", []))
    _merge_rels(run, "Skill", "COMPLEMENTS", "Skill", payload.get("complements", []))
    _merge_rels(run, "Course", "TEACHES", "Skill", payload.get("teaches", []))
    _merge_rels(run, "Project", "PRACTICES", "Skill", payload.get("practices", []))
    _merge_rels(run, "Mentor", "EXPERT_IN", "Skill", payload.get("expert_in", []))
    _merge_rels(run, "TargetRole", "REQUIRES", "Skill", payload.get("requires", []))
    _merge_rels(run, "Employee", "HAS_SKILL", "Skill", payload.get("has_skill", []))


def _clear_catalog_rels(run) -> None:
    for rel in CATALOG_RELS:
        run(f"MATCH ()-[r:{rel}]->() DELETE r")


def _merge_nodes(run, label: str, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    run(
        f"""
        UNWIND $rows AS row
        MERGE (n:{label} {{id: row.id}})
        SET n += row
        """,
        rows=rows,
    )


def _merge_rels(
    run, src_label: str, rel: str, dst_label: str, pairs: list[dict[str, str]]
) -> None:
    if not pairs:
        return
    run(
        f"""
        UNWIND $pairs AS pair
        MATCH (a:{src_label} {{id: pair.src}})
        MATCH (b:{dst_label} {{id: pair.dst}})
        MERGE (a)-[:{rel}]->(b)
        """,
        pairs=pairs,
    )
