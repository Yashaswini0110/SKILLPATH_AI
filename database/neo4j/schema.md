# Neo4j schema (Phase 9)

Constraints are applied by `knowledge_graph/schema.py` on sync.

Node labels: Skill, Course, Project, Mentor, TargetRole, Employee,
Assessment, Certification.

Catalog relationships written today:

- `(Skill)-[:PREREQUISITE_OF]->(Skill)`
- `(Skill)-[:RELATED_TO]->(Skill)`
- `(Skill)-[:COMPLEMENTS]->(Skill)`
- `(Course)-[:TEACHES]->(Skill)`
- `(Project)-[:PRACTICES]->(Skill)`
- `(Mentor)-[:EXPERT_IN]->(Skill)`
- `(TargetRole)-[:REQUIRES]->(Skill)`
- `(Employee)-[:HAS_SKILL]->(Skill)`

Reserved until later phases: `COMPLETED`, `MENTORS`, `RECOMMENDED_FOR`, `PART_OF`.
