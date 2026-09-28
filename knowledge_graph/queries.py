"""Read-only graph queries used by Phase 9 APIs."""

from __future__ import annotations

from typing import Any

from knowledge_graph.client import GraphClient


def immediate_prerequisites(client: GraphClient, skill_id: str) -> list[dict[str, Any]]:
    return client.run(
        """
        MATCH (p:Skill)-[:PREREQUISITE_OF]->(s:Skill {id: $skill_id})
        RETURN p.id AS id, p.name AS name, p.canonical_name AS canonical_name
        ORDER BY p.canonical_name
        """,
        skill_id=skill_id,
    )


def courses_teaching(client: GraphClient, skill_id: str) -> list[dict[str, Any]]:
    return client.run(
        """
        MATCH (c:Course)-[:TEACHES]->(s:Skill {id: $skill_id})
        RETURN c.id AS id, c.title AS title
        ORDER BY c.title
        """,
        skill_id=skill_id,
    )


def projects_practicing(client: GraphClient, skill_id: str) -> list[dict[str, Any]]:
    return client.run(
        """
        MATCH (p:Project)-[:PRACTICES]->(s:Skill {id: $skill_id})
        RETURN p.id AS id, p.title AS title
        ORDER BY p.title
        """,
        skill_id=skill_id,
    )


def mentors_for_skill(client: GraphClient, skill_id: str) -> list[dict[str, Any]]:
    return client.run(
        """
        MATCH (m:Mentor)-[:EXPERT_IN]->(s:Skill {id: $skill_id})
        RETURN m.id AS id, m.name AS name
        ORDER BY m.name
        """,
        skill_id=skill_id,
    )


def mentors_for_skills(
    client: GraphClient, skill_ids: list[str]
) -> list[dict[str, Any]]:
    return client.run(
        """
        MATCH (m:Mentor)-[:EXPERT_IN]->(s:Skill)
        WHERE s.id IN $skill_ids
        WITH m, collect(DISTINCT s.id) AS matched
        RETURN m.id AS id, m.name AS name, matched AS skill_ids
        ORDER BY size(matched) DESC, m.name
        """,
        skill_ids=skill_ids,
    )


def related_skills(client: GraphClient, skill_id: str) -> list[dict[str, Any]]:
    return client.run(
        """
        MATCH (s:Skill {id: $skill_id})-[r:RELATED_TO|COMPLEMENTS]-(o:Skill)
        RETURN DISTINCT o.id AS id, o.name AS name, o.canonical_name AS canonical_name,
               type(r) AS relation
        ORDER BY o.canonical_name
        """,
        skill_id=skill_id,
    )


def prerequisite_edges(client: GraphClient) -> list[tuple[str, str]]:
    rows = client.run(
        """
        MATCH (a:Skill)-[:PREREQUISITE_OF]->(b:Skill)
        RETURN a.id AS src, b.id AS dst
        """
    )
    return [(row["src"], row["dst"]) for row in rows]


def node_counts(client: GraphClient) -> dict[str, int]:
    labels = (
        "Skill",
        "Course",
        "Project",
        "Mentor",
        "TargetRole",
        "Employee",
        "Assessment",
        "Certification",
    )
    counts: dict[str, int] = {}
    for label in labels:
        rows = client.run(f"MATCH (n:{label}) RETURN count(n) AS count")
        counts[label] = int(rows[0]["count"]) if rows else 0
    return counts
