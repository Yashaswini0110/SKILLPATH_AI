"""Neo4j constraints for PRD node types."""

CONSTRAINTS = [
    "CREATE CONSTRAINT skill_id IF NOT EXISTS FOR (n:Skill) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT course_id IF NOT EXISTS FOR (n:Course) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT project_id IF NOT EXISTS FOR (n:Project) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT mentor_id IF NOT EXISTS FOR (n:Mentor) REQUIRE n.id IS UNIQUE",
    (
        "CREATE CONSTRAINT employee_id IF NOT EXISTS "
        "FOR (n:Employee) REQUIRE n.id IS UNIQUE"
    ),
    "CREATE CONSTRAINT role_id IF NOT EXISTS FOR (n:TargetRole) REQUIRE n.id IS UNIQUE",
    (
        "CREATE CONSTRAINT assessment_id IF NOT EXISTS "
        "FOR (n:Assessment) REQUIRE n.id IS UNIQUE"
    ),
    (
        "CREATE CONSTRAINT certification_id IF NOT EXISTS "
        "FOR (n:Certification) REQUIRE n.id IS UNIQUE"
    ),
]


def apply_schema(run) -> None:
    for statement in CONSTRAINTS:
        run(statement)
