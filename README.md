# SkillPath AI

Evidence-based, prerequisite-aware, adaptive learning-path recommender for employee competency development.

This is **not** a resume-to-LLM course list. Core decisions use deterministic logic, NLP/ML, semantic similarity, knowledge-graph reasoning, and constraint optimization. The LLM is limited to interaction, explanation verbalization, and ambiguous extraction.

```text
Employee Evidence → Current Skill Profile → Target Role
        → Evidence-Based Skill Gaps → Knowledge Graph
        → Hybrid Recommendation → Learning Path Optimization
        → Assessment → Updated Evidence → Adaptive Re-optimization
```

The product requirements live in `docs/prd/AI-Learning-Path-Recommender-PRD.pdf`. The implementation sequence lives in `docs/prd/SkillPath_AI_Implementation_Plan.md`.

**Current milestone:** Phase 19 (grounded learning assistant). Ask on Assistant; it answers from stored profile, path, and catalog, or says it does not know.

## Stack

| Layer | Technology |
| --- | --- |
| Frontend | React 18, TypeScript, Tailwind CSS, React Query, Zustand |
| Backend | Python 3.11, FastAPI, Pydantic, SQLAlchemy, Alembic |
| Database | PostgreSQL 15, Neo4j 5 |
| Tooling | Docker Compose, pytest, Ruff, Black, mypy |

## Repository layout

```text
frontend/            React UI
backend/             FastAPI modular monolith
ml/                  Skill extraction, embeddings, evidence (later)
recommendation/      Baseline, hybrid, project pairing, mentor matching, and topological paths
knowledge_graph/     Neo4j client, DAG, traversal (Phase 9)
optimization/        OR-Tools path optimizer (Phase 14)
llm/                 RAG assistant and explanation verbalization
database/            Schema notes and seed SQL
datasets/            Taxonomies, resources, evaluation data
tests/               Cross-cutting test suites
docs/                Architecture, API, research, user guides
scripts/             Seed and utility scripts
```

The backend is a **modular monolith**. Service boundaries are Python packages, not separate deployable microservices.

## Prerequisites

- Python 3.11
- Node.js 20+
- Docker Desktop
- Git

## Quick start (local development)

### 1. Clone and configure

```powershell
cd "C:\Users\Jyothi\Yashu NVIDIA Proj"
copy .env.example .env
```

Edit `.env` and set a long random `SECRET_KEY`.

### 2. Start PostgreSQL and Neo4j

```powershell
docker compose up -d postgres neo4j
```

PostgreSQL is published on **port 5435**. Neo4j Bolt is on **7688** (browser 7475).

### 3. Backend

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- API: http://localhost:8000
- Health: http://localhost:8000/health
- OpenAPI: http://localhost:8000/docs

On first start the API seeds a small skill catalog and target-role catalog when `SEED_ON_STARTUP=true`.

### 4. Frontend

```powershell
cd frontend
npm install
npm run dev
```

UI: http://localhost:5173

### 5. Optional full stack via Docker

```powershell
docker compose up --build
```

## Tests and quality checks

From `backend/` with the virtualenv active and PostgreSQL running:

```powershell
pytest
ruff check .
black --check .
mypy app
```

Integration tests use the database in `DATABASE_URL`. They create and roll back transactions per test.

## Phase 1 capabilities

A user can:

1. Register with an application role
2. Log in and receive a JWT access token (15 minutes) and refresh token (7 days)
3. View and edit their employee profile
4. Add education and work experience
5. Add self-declared skills (1–5) from the catalog
6. Select a target role
7. See a profile completeness score on the dashboard

## Phase 2 capabilities

A user can:

1. Browse the skill catalog with canonical names, aliases, difficulty, and category filter
2. Resolve free-text mentions (`ML`, `K8s`, `machine-learning`) to one catalog skill
3. See unmatched mentions left unmatched (the API does not invent skills)
4. Use the profile “Lookup a mention” tool

Self-declared skills remain self-declaration evidence. Later phases will extract skills from resumes using this mapper.

## Phase 3 capabilities

A user can:

1. Upload a PDF, DOCX, or TXT resume
2. See inferred catalog skills with snippets and confidence
3. Keep those extractions separate from self-declared profile skills

Extracted skills are labeled inferred. They are not verified facts.

## Phase 4 capabilities

A user can:

1. Browse a catalog role’s required / preferred skills
2. Paste or upload a job description (PDF, DOCX, or TXT)
3. See skills mapped through the taxonomy with PRD weights 1.0 / 0.6 / 0.4

Unknown terms are omitted. The job profile is not compared to the employee yet.

## Phase 5 capabilities

A user can:

1. See an estimated current level per skill
2. See why: self-declared vs resume evidence
3. See confidence and a conflict flag when sources disagree

Inferred resume hits are still not verified facts.

## Phase 6 capabilities

A user can:

1. Compare the current skill profile to a catalog role or a job description
2. See current vs required level per skill
3. See ranked gaps with Critical / High / Medium / Low / None priority

This is not a course recommendation.

## Phase 7 capabilities

A user can:

1. Browse a synthetic catalog of courses, projects, and mentors
2. See which catalog skills each resource covers
3. Filter resources by skill

Resources are not a learning path. Ranking uses independent baselines or the hybrid score.

## Phase 8 capabilities

A user can:

1. Rank courses, projects, and mentors against their open skill gaps
2. Switch among popularity, content-based, and semantic baselines
3. See rank, score, component scores, matched gap skills, and a deterministic reason

Hybrid seven-signal ranking is the default on Recommend.

## Phase 9 capabilities

A user can:

1. Inspect a skill’s immediate prerequisites and full prerequisite chain
2. See courses that teach the skill, projects that practice it, and mentors
3. Confirm the prerequisite graph has no cycles

This is not a learning path.

## Phase 10 capabilities

A user can:

1. Rank courses, projects, and mentors with a weighted hybrid of seven signals
2. Switch back to popularity, content, or semantic baselines
3. See each signal score, the configured weights, and a deterministic reason

This is still a ranked list, not a learning path.

## Phase 11 capabilities

A user can:

1. See a course then a project for each major skill gap
2. Confirm the pair teaches that skill, with duration and difficulty on the card
3. Read a deterministic reason (learn X, then practice Y)

This is pairing, not a full path, and not an assessment.

## Phase 12 capabilities

A user can:

1. See mentors ranked by overlap with their open skill gaps
2. Read how many of the top gaps match, hours per month, and open mentee slots
3. Inspect a machine-readable `why` payload

This is still a match list, not a learning path.

## Phase 13 capabilities

A user can:

1. See a topological sequence of missing foundations and open skill gaps
2. Confirm `prerequisite_violation_count` is 0
3. See a catalog course (and project when one remains) on each step

This is ordering, not OR-Tools optimization.

## Phase 14 capabilities

A user can:

1. Generate a path that fits weekly hours and a deadline
2. Compare OR-Tools, greedy, and topological totals, coverage, and violations
3. See which week each step falls in

This is not the foundation/core/advanced timeline.

## Phase 15 capabilities

A user can:

1. See the path grouped as Learn first, Core, and Later
2. Read duration, difficulty, Not started, and why on each step
3. Keep the hour-budget plan or expand the complete list

This is not an assessment or progress tracker.

## Phase 16 capabilities

A user can:

1. Take a multiple-choice quiz for a catalog skill
2. See score, pass/fail, and per-question feedback after submit
3. Add a new assessment evidence row without overwriting older evidence

This does not add refreshers or re-run the path optimizer.

## Phase 17 capabilities

A user can:

1. Score below 55% and see a review step with extra hours on Path
2. Score 90% or higher and skip that skill so later steps can start sooner
3. Rebuild the hour-budget plan from the latest quiz without using an LLM

Course/project completion, GitHub, and mentor feedback are not triggers yet. A manual skill update already rebuilds the path on the next GET.

## Phase 18 capabilities

A user can:

1. Open Why? on a course, project, mentor, practice pair, or path step
2. Read numbered facts built from stored scores, matched skills, and gap priority
3. See a paragraph that only restates those facts

The LLM does not invent recommendations. Optional verbalization is a join of the same facts.

## Phase 19 capabilities

A user can:

1. Ask the assistant what to learn next and get the stored path step
2. Ask why a skill is needed and hear the stored gap or path reason
3. Ask the catalog to explain a topic such as transformers
4. Ask for a project for a catalog skill such as RAG
5. Ask why a ranked course was recommended, using stored Why? facts
6. See “I don’t have that” when the passages do not contain the answer

The assistant is not the ranking engine. Optional NIM rephrase (`openai/gpt-oss-20b`) stays off unless `LLM_ENABLED` and an API key are set. Email and resume text are not sent.

## Phase 21 capabilities

A user can:

1. Compare catalog roles without changing the saved target
2. See coverage, missing skills, estimated hours, a hypothetical path, projects, and mentors
3. Read that this is not a hiring or employment prediction

GitHub evidence is deferred and is not required.

## API conventions

- Prefix: `/api/v1/`
- Auth header: `Authorization: Bearer <access_token>`
- Success: `{ "data": ..., "message": null }`
- Error: `{ "error": { "code": "...", "message": "...", "details": [] } }`

## Research and responsible AI notes

Recommendation scoring uses deterministic baselines and a weighted hybrid. The assistant retrieves stored passages; an external LLM is optional and off by default.

Principle: **the system suggests; the human decides.**

## Next phase

Phase 21 — what-if role comparison. GitHub evidence is deferred.
