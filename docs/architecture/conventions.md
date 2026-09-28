# Local setup

See the root `README.md` for the shortest path. This page records conventions used from Phase 0.

## Environment variables

Copy `.env.example` to `.env`. Required for the backend:

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | SQLAlchemy URL (`postgresql+psycopg2://...`) |
| `SECRET_KEY` | JWT signing key |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Default 15 (PRD §32.4) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Default 7 |
| `BCRYPT_ROUNDS` | Default 12 |
| `BACKEND_CORS_ORIGINS` | Comma-separated browser origins |
| `SEED_ON_STARTUP` | Seed skill/role catalog if empty |
| `JD_WEIGHT_REQUIRED` | Default 1.0 |
| `JD_WEIGHT_PREFERRED` | Default 0.6 |
| `JD_WEIGHT_MENTIONED` | Default 0.4 |
| `SELF_DECLARATION_RELIABILITY` | Default 0.3 |
| `RESUME_RELIABILITY` | Default 0.6 |
| `EVIDENCE_CONFLICT_VARIANCE` | Default 1.0 |
| `GAP_WEIGHT_IMPORTANCE` | Default 1.0 |
| `GAP_WEIGHT_CONFIDENCE` | Default 1.0 |
| `GAP_WEIGHT_CRITICALITY` | Default 1.0 |
| `GAP_WEIGHT_EVIDENCE` | Default 1.0 |
| `GAP_CRITICAL_THRESHOLD` | Default 2.0 |
| `GAP_HIGH_THRESHOLD` | Default 1.0 |
| `GAP_MEDIUM_THRESHOLD` | Default 0.5 |
| `REC_TOP_GAP_COUNT` | Open gaps used for candidate retrieval (default 5) |
| `REC_RESULT_LIMIT` | Ranked rows returned (default 10) |
| `REC_SEMANTIC_BACKEND` | `hashing` (default) or `minilm` |
| `REC_SEMANTIC_MODEL` | Default `all-MiniLM-L6-v2` |
| `REC_W_SEMANTIC` | Hybrid weight for semantic cosine (default 1.0) |
| `REC_W_GAP` | Hybrid weight for skill-gap cosine (default 1.0) |
| `REC_W_PREREQUISITE` | Hybrid weight for DAG prerequisite fit (default 1.0) |
| `REC_W_DIFFICULTY` | Hybrid weight for difficulty fit (default 1.0) |
| `REC_W_PREFERENCE` | Hybrid weight for learning-format preference (default 1.0) |
| `REC_W_COLLABORATIVE` | Hybrid weight for skill-set Jaccard (default 1.0) |
| `REC_W_KG` | Hybrid weight for knowledge-graph reasoning (default 1.0) |
| `REC_P_SKILLS` | Practice-pair weight for skills addressed (default 1.0) |
| `REC_P_PRIORITY` | Practice-pair weight for gap priority (default 1.0) |
| `REC_P_DIFFICULTY` | Practice-pair weight for difficulty fit (default 1.0) |
| `REC_P_PROFICIENCY` | Practice-pair weight for proficiency stretch (default 1.0) |
| `REC_P_DURATION` | Practice-pair weight for duration vs weekly hours (default 1.0) |
| `REC_P_TECHNOLOGIES` | Practice-pair weight for technology overlap (default 1.0) |
| `REC_P_ROLE` | Practice-pair weight for target-role skill overlap (default 1.0) |
| `REC_M_SKILL` | Mentor-match weight for top-gap overlap (default 1.0) |
| `REC_M_DOMAIN` | Mentor-match weight for domain overlap (default 1.0) |
| `REC_M_EXPERIENCE` | Mentor-match weight for years / 15 (default 1.0) |
| `REC_M_AVAILABILITY` | Mentor-match weight for hours / 12 (default 1.0) |
| `REC_M_GOALS` | Mentor-match weight for role-skill coverage and format fit (default 1.0) |
| `REC_M_WORKLOAD` | Mentor-match weight for open mentee slots (default 1.0) |
| `REC_PATH_FOUNDATION_LEVEL` | Non-role ancestor treated as known at or above this level (default 3.0) |
| `REC_PATH_DEADLINE_WEEKS` | Default path deadline in weeks (default 12) |
| `NEO4J_URI` | Bolt URL (default `bolt://localhost:7688`) |
| `NEO4J_USER` | Default `neo4j` |
| `NEO4J_PASSWORD` | Default `skillpath` |
| `NEO4J_SYNC_ON_STARTUP` | Project PostgreSQL catalog into Neo4j |

Frontend: `VITE_API_URL` (default `http://localhost:8000`).

## Naming

- Python modules and functions: `snake_case`
- Pydantic schemas and SQLAlchemy models: `PascalCase`
- API paths: plural nouns, `/api/v1/...`
- Database tables: plural `snake_case`
- Commits (when requested): `feat(auth): ...`, `test(profile): ...`

## Branching (when using Git)

- `main` — stable increments
- `phase/N-short-name` — one implementation phase

## Logging

Python `logging` with logger name `skillpath`. Request errors include an error `code`. Do not log passwords or raw JWTs.

## Database

PostgreSQL is the system of record for transactional data. Alembic is the only PostgreSQL schema change mechanism. Neo4j holds the Phase 9 skill/resource graph projection.
