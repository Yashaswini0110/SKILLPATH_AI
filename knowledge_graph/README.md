# Knowledge graph

Phase 9 stores skills, resources, roles, and employees in Neo4j so later
phases can walk prerequisites instead of treating the catalog as flat lists.

PostgreSQL remains the system of record. The graph is a projection.

## Prerequisite DAG

Edges live in `datasets/processed/skill_prerequisites.json` using taxonomy
`name` keys:

```text
(Statistics)-[:PREREQUISITE_OF]->(Machine Learning)
```

Cycle detection runs before those edges are written. A cycle fails the seed.

## Queries

- Immediate prerequisites of a skill
- Full prerequisite chain (topological)
- Courses that `TEACHES` a skill
- Projects that `PRACTICES` a skill
- Mentors `EXPERT_IN` a skill or a set of gap skills

Assessment and Certification node labels exist but have no rows yet.
`COMPLETED`, `MENTORS`, `RECOMMENDED_FOR`, and `PART_OF` are reserved.

Hybrid ranking uses this DAG. Learning-path generation lives in
`recommendation/path/` and reads the same JSON edges.
