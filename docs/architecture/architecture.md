# Architecture

SkillPath AI is implemented as a **modular monolith**. Packages match the PRD service boundaries so Neo4j, OR-Tools, NLP, and RAG can be added without rewriting authentication or profile persistence.

## Current runtime (Phase 0–16)

```text
React (Vite)  --HTTPS/REST-->  FastAPI  -->  PostgreSQL 15
                                   |         Neo4j 5
                                   |
                                   +--> JWT auth, RBAC
                                   +--> Employee profile services
                                   +--> Skill taxonomy mapper
                                   +--> Resume text extraction (ml/skill_extraction)
                                   +--> Job-description requirement extraction
                                   +--> Evidence aggregation (confidence / L_cur)
                                   +--> Skill-gap engine (ml/gap)
                                   +--> Course / project / mentor catalogs
                                   +--> Baseline recommenders (popularity / content / semantic)
                                   +--> Hybrid recommender (seven weighted signals)
                                   +--> Course → project pairing for major gaps
                                   +--> Mentor matching (overlap / hours / slots)
                                   +--> Topological learning path (violation count = 0)
                                   +--> OR-Tools path optimizer (hours / deadline / unique resources)
                                   +--> Path timeline (foundation / core / advanced)
                                   +--> MCQ assessments (new evidence, no path re-opt)
                                   +--> Neo4j skill graph (prerequisites, TEACHES / PRACTICES / EXPERT_IN)
```

## Target runtime (later phases)

```text
Frontend
   → FastAPI API layer
        → Auth / Profile / Skills / Gap / Path / Assessment
        → ml/ (extraction, embeddings, evidence)
        → recommendation/ (hybrid scoring)
        → knowledge_graph/ (Neo4j)
        → optimization/ (OR-Tools)
        → llm/ (RAG + explanation verbalization)
   PostgreSQL | Neo4j | pgvector | Redis/Celery
```

The LLM is never the recommendation engine. Every future recommendation must retain machine-readable score components and evidence.

## Phase 1 data model

Application identity (`users`) is separate from the competency profile (`employees`):

- `users`: email, password hash, full name, application role
- `employees`: job title, department, years of experience, weekly hours, learning preferences, target role
- `education`, `work_experience`
- `skills`, `employee_skills` (self-declared for now)
- `roles`, `role_skills` (target competency profiles)
- `refresh_tokens`

Application roles: `EMPLOYEE`, `MANAGER`, `MENTOR`, `HR_ADMIN`, `SYSTEM_ADMIN`.

Target roles (career catalog) are rows in `roles`, not the same concept as application RBAC.

## Security (Phase 1)

- Passwords hashed with bcrypt, cost 12
- Access JWT: 15 minutes, claim `type=access`
- Refresh JWT: 7 days, persisted by `jti`, revocable on logout
- Resource ownership: employees can only read/write `/employees/me`
- No demographic attributes on the profile
- No PII sent to external LLM APIs (no LLM calls yet)

## Configuration

All durations, bcrypt rounds, CORS origins, and seed flags live in environment variables (`app/core/config.py`). Do not hard-code research weights in later phases.

## Phase 2 skill taxonomy

- `skills.canonical_name` is the single normalization key (not a copy of `name`)
- `skills.difficulty` is 1–5
- `skill_aliases` stores alternate mentions (`ML`, `K8s`, `Postgres`)
- `POST /api/v1/skills/resolve` maps raw text → `{ skill_id, canonical_name, confidence }` or unmatched
- Mapper lives in `ml/skill_extraction/` so Phase 3 extraction can import it
- Unknown terms are not invented

## Phase 3 resume extraction

- `resumes` stores the uploaded file path and extracted text
- `evidence` stores per-skill resume hits (snippet, inferred flag, confidence)
- Self-declared `employee_skills` are not overwritten
- Dictionary matching is Layer 1; section context is Layer 2
- Unknown terms are not invented

## Phase 4 job descriptions

- Catalog `GET /api/v1/roles/{id}` returns a structured skill profile with requirement labels
- `job_descriptions` stores pasted or uploaded JD text owned by the employee
- `job_description_skills` stores required / preferred / mentioned catalog matches
- Weights default to 1.0 / 0.6 / 0.4 and are configurable
- Self-declared `employee_skills` and resume `evidence` are not overwritten
- Unknown terms are not invented

## Phase 5 evidence profile

- `GET /api/v1/employees/me/skill-profile` aggregates evidence into `C(s)` and `L_cur(s)`
- Self-declaration writes a `SELF` evidence row (reliability 0.3, configurable)
- Resume hits remain separate `RESUME` evidence
- High level variance raises a conflict flag and assessment hint
- Inferred ≠ fact on the UI
- Gap analysis is computed in Phase 6

## Phase 6 skill gaps

- `GET /api/v1/gap-analysis` compares `L_cur` to a catalog role or owned JD
- `Gap = max(0, L_req − L_cur) × I × C × R × E` with extra weights defaulting to 1.0
- Missing current skills use `L_cur = 0`, `C = 1`, `E = 1`
- Gaps are ranked into Critical / High / Medium / Low / None
- Gaps are not persisted; no Alembic migration
- See `docs/architecture/skill-gap-model.md`

## Phase 7 resource catalogs

- `datasets/processed/resource_catalog.json` is the seed source (synthetic)
- `courses`, `projects`, `mentors` plus skill join tables
- List APIs accept optional `skill_id`; they do not rank against gaps
- Mentors are catalog people, not `users` with role MENTOR

## Phase 8 baseline recommendations

- Candidate retrieval uses the top open skill gaps only
- Popularity is a catalog proxy (rating, years, or skill coverage)
- Content score is cosine of the gap vector vs the resource skill vector
- Semantic score is embedding cosine; hashing is the default encoder
- Hybrid score is a configurable weighted mean of seven independent signals
- `recommendation_results` stores rank, score, JSON components, and reasons
- `GET /api/v1/recommendations/courses|projects|mentors` (default `HYBRID`)
- See `docs/architecture/recommendation.md`

## Phase 9 knowledge graph

- Neo4j is a projection of the PostgreSQL catalog
- `PREREQUISITE_OF` comes from `datasets/processed/skill_prerequisites.json`
- Cycle detection must pass before those edges are written
- `GET /api/v1/graph/status` and `GET /api/v1/graph/skills/{id}`
- See `docs/architecture/knowledge-graph.md`

## Phase 11 practice pairs

- Major gaps (Critical / High) each get one course then one project
- Project score uses skills, priority, difficulty, proficiency, duration, technologies, role overlap
- `practice_pairings` stores rank, score, JSON components, and reason
- `GET /api/v1/recommendations/practice-pairs`
- See `docs/architecture/recommendation.md`

## Phase 12 mentor matches

- Dedicated matcher, separate from hybrid `GET /recommendations/mentors`
- Signals: skill overlap, domain, experience, availability, learning goals, workload
- Workload uses `open_slots = max_mentees` until an assignment log exists
- `mentor_matches` stores rank, score, JSON components, and a machine-readable `why`
- `GET /api/v1/recommendations/mentor-matches`
- See `docs/architecture/recommendation.md`

## Phase 13 learning path

- Top open gaps expand through the skill DAG; known skills are skipped
- Kahn topological order; `prerequisite_violation_count == 0`
- Each step maps at most one unused course and project
- `GET /api/v1/learning-paths`
- See `docs/architecture/recommendation.md`

## Phase 14 path optimization

- Default `ORTOOLS` subset under weekly hours and a deadline
- Comparison payload: greedy vs topological vs OR-Tools
- Steps include duration and week span
- See `docs/architecture/optimization.md`

## Phase 15 learning-path UI

- Steps are grouped as Learn first / Core / Later (`FOUNDATION` / `CORE` / `ADVANCED`)
- Each item shows duration, skill, difficulty, status, and why
- Quiz links appear when a seeded MCQ exists
- See `docs/architecture/recommendation.md`

## Phase 16 assessments

- Seeded MCQs; GET hides answers until submit
- Each attempt inserts `ASSESSMENT` evidence; history is kept
- See `docs/architecture/assessment.md`

## Phase 17 adaptive re-optimization

- Weak quiz (<55%) adds a review step with extra hours, then re-optimizes
- Strong quiz (≥90%) skips basics so later skills can start sooner
- Manual skill updates already rebuild on GET `/learning-paths`
- Course/project completion, GitHub, and mentor feedback are not faked

## Phase 18 deterministic explainability

- Why? lists facts from stored scores, matched skills, and gap priority
- Verbalization restates those facts; the LLM is not the ranking engine
- See `docs/architecture/explainability.md`

## Phase 19 grounded assistant

- Retrieves profile, gaps, path, quizzes, stored ranks, and catalog
- Answers or says the information is unavailable
- Optional NIM rephrase (`openai/gpt-oss-20b`) is off by default; no extra PII
- See `docs/architecture/assistant.md`

## Phase 21 what-if comparison

- Compares catalog roles using the current skill profile
- Reports coverage, missing skills, estimated effort, projects, mentors
- Does not change the saved target or path; not a hiring prediction
- See `docs/architecture/what-if.md`

## Phase 22 skill digital twin

- Joins stored profile, target requirements, and evidence timestamps
- Shows current, required, gap, confidence, sources, and trend per skill
- Does not change the saved target or path; GitHub is not collected
- See `docs/architecture/digital-twin.md`

## Phase 23 manager / HR analytics

- Department-scoped or org-wide aggregates
- Heatmap, gaps, training priorities, quiz/path participation
- No names, emails, or evidence text
- See `docs/architecture/analytics.md`

## Phase 24 frontend polish

- Grouped navigation (You, Skills, Learn, Explore)
- Why? on ranked items; skip link and focus outlines

## Phase 25 API hardening

- Page envelope on catalog and assessment lists
- In-memory rate limit; HTTP errors use `{ error }`
- See `docs/architecture/api-hardening.md`

## Deferred by design

Remaining NLP layers (spaCy/MiniLM) and GitHub evidence (skipped, still on
the roadmap).
