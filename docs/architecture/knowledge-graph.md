# Knowledge graph (Phase 9)

PostgreSQL remains the system of record. Neo4j is a projection used for
prerequisite traversal.

## Runtime

Docker service `neo4j` (image `neo4j:5.26-community`). Host ports:

- Bolt `7688`
- HTTP browser `7475`

## Seed

On API startup (`NEO4J_SYNC_ON_STARTUP=true`) the backend MERGEs:

- Skills, courses, projects, mentors, target roles, employees
- `PREREQUISITE_OF` from `datasets/processed/skill_prerequisites.json`
- `TEACHES` / `PRACTICES` / `EXPERT_IN` / `REQUIRES` / `HAS_SKILL`
- `RELATED_TO` and `COMPLEMENTS`

The JSON DAG is rejected if it contains a cycle.

## APIs

```text
GET /api/v1/graph/status
GET /api/v1/graph/skills/{skill_id}
GET /api/v1/graph/gap-mentors
```

`status.acyclic` must be true. Assessment and Certification labels exist
without rows. Path generation uses this DAG in Phase 13
(`GET /api/v1/learning-paths`).
