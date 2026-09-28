# SkillPath AI — what was built

SkillPath AI is an evidence-based, prerequisite-aware learning-path recommender for employee competency development. An employee brings evidence (a profile, a resume, later a quiz). The system estimates a skill profile, compares it to a target role or job description, ranks courses, projects, and mentors, and builds an ordered plan that respects prerequisites and a weekly hour budget. Quizzes add new evidence and can change that plan.

The language model is not the recommendation engine. Ranking, gaps, paths, and explanations come from deterministic formulas, catalog data, a skill graph, and a constraint solver. An optional NVIDIA NIM model may only rephrase an answer that was already grounded in stored facts.

This document describes the system as it exists in the repository: phases 0–19 and 21–27 are implemented. Phase 20 (GitHub evidence) is deferred. Phase 28 (final deployment polish and a scripted demo) is not done. Catalog data is synthetic.

Section 14 explains every feature in detail: what it is for, what the screen does, what the server calculates, what is stored, and what that feature does not do.

Product requirements: `docs/prd/AI-Learning-Path-Recommender-PRD.pdf`.  
Implementation playbook: `docs/prd/SkillPath_AI_Implementation_Plan.md`.  
Phase checklist: `docs/phases/roadmap.md`.

---

## 1. Product loop

```text
Employee evidence
        ↓
Current skill profile (level, confidence, conflict)
        ↓
Target role or job description
        ↓
Weighted skill gaps
        ↓
Prerequisite graph
        ↓
Courses + projects + mentors
        ↓
Hybrid ranking and a constrained learning path
        ↓
Assessment
        ↓
New evidence → updated profile → rebuilt path
```

A typical walkthrough:

1. Register and set a profile (title, department, years, hours per week, learning format).
2. Declare skills and pick a target role such as ML Engineer.
3. Upload a PDF, DOCX, or TXT resume. Known terms map onto the skill catalog. Unknown terms are dropped.
4. Open Skills to see an estimated level, confidence, evidence sources, and a conflict flag when sources disagree.
5. Open Gaps to compare current levels with the role (or a pasted job description).
6. Open Recommend, Practice, and Mentors for ranked resources and a machine-readable reason.
7. Open Path for a week-by-week plan that fits weekly hours and a deadline.
8. Take an MCQ. A weak score adds review hours. A strong score can drop that skill so later skills start sooner.
9. Ask the Assistant what to learn next. The answer is the stored path step, or an explicit “I don’t have that.”
10. Compare other catalog roles without changing the saved target.
11. A manager or HR admin can open Analytics for department or organization aggregates. Names and evidence text are not included.

---

## 2. Architecture

The application is a **modular monolith**. FastAPI owns HTTP, authentication, persistence, and orchestration. Algorithm packages sit beside the API and are imported as libraries. They are not separate deployable services.

```text
Browser (React, Vite, port 5173)
        │  REST /api/v1  +  JWT
        ▼
FastAPI (port 8000)
        │
        ├── app/api          routes, auth dependencies, pagination
        ├── app/services     use cases (profile, resume, gap, path, …)
        ├── app/models       SQLAlchemy tables
        │
        ├── ml/              taxonomy, resume/JD extraction, evidence, gaps, quiz scoring, evaluation
        ├── recommendation/  baselines, hybrid signals, practice pairs, mentors, path order
        ├── knowledge_graph/ Neo4j projection, cycle check, graph queries
        ├── optimization/    greedy, topological, OR-Tools CP-SAT
        └── llm/             grounded answers and optional rephrase
                │
                ├── PostgreSQL 15   system of record (host port 5435)
                └── Neo4j 5         skill graph projection (Bolt 7688, browser 7475)
```

PostgreSQL is the source of truth. Neo4j is rebuilt from PostgreSQL and from `datasets/processed/skill_prerequisites.json` when the API starts (`NEO4J_SYNC_ON_STARTUP=true`). Path generation can use that same JSON DAG even when it is reasoning about prerequisites; the graph API reads Neo4j.

pgvector and Redis appear in the original plan. They are not in the running stack. Semantic similarity uses an in-process encoder. Rate limiting is in-memory.

### Request path

```text
HTTP handler
    → Pydantic schema
    → service (owns the transaction and authorization)
    → ml / recommendation / optimization / llm
    → PostgreSQL (and Neo4j for graph reads)
    → { "data": ..., "message": null }
```

Business rules do not live in route functions. Routes validate input, call a service, and wrap the result.

### Why decisions stay out of the LLM

| Decision | Owner |
| --- | --- |
| Which catalog skill a mention maps to | Taxonomy dictionary (`ml/skill_extraction`) |
| Estimated proficiency and confidence | Evidence aggregation (`ml/evidence`) |
| Which gaps matter | Gap formula (`ml/gap`) |
| Which course ranks higher | Weighted signals (`recommendation/`) |
| What order to learn in | DAG topological order, then OR-Tools |
| Why a row was recommended | Stored scores turned into numbered facts |
| What the assistant may say | Retrieved passages; optional rephrase must stay inside those passages |

---

## 3. Repository layout

```text
frontend/            React UI
backend/             FastAPI app, Alembic, pytest
ml/                  Extraction, evidence, gaps, evaluation
recommendation/      Ranking, pairing, mentor match, path construction
knowledge_graph/     Neo4j client, schema, seed, queries, cycle detection
optimization/        Greedy, schedule, OR-Tools, comparison metrics
llm/                 Retrieval, verbalization, assistant, NIM client
database/            Schema notes
datasets/            Taxonomy, prerequisites, resources, quizzes, eval sets
docs/                Architecture, API notes, phase reports, research
scripts/             Utilities
tests/               Cross-package tests
docker-compose.yml   Postgres, Neo4j, backend, frontend
```

Backend internals:

```text
backend/app/
├── api/v1/          one router per area
├── core/            settings, enums, security, evidence reliability
├── db/              session, seed
├── models/          SQLAlchemy
├── schemas/         Pydantic
├── services/        use cases
└── middleware/      rate limit
```

---

## 4. Technology

| Layer | Choice |
| --- | --- |
| UI | React 18, TypeScript, Tailwind CSS, React Query, Zustand, React Router, Vite |
| API | Python 3.11, FastAPI, Pydantic, SQLAlchemy, Alembic |
| Auth | bcrypt (cost 12), JWT access token (15 minutes), refresh token (7 days, stored by `jti`) |
| Relational store | PostgreSQL 15 |
| Graph store | Neo4j 5.26 Community |
| Optimization | OR-Tools CP-SAT |
| Optional LLM | NVIDIA NIM, model `openai/gpt-oss-20b`, off unless `LLM_ENABLED` and an API key are set |
| Quality | pytest, Ruff, Black, mypy |
| Containers | Docker Compose |

Semantic embeddings are designed for Sentence Transformers `all-MiniLM-L6-v2`. The default encoder is a stable hashing bag-of-words (`REC_SEMANTIC_BACKEND=hashing`) so tests do not download Torch. Set `REC_SEMANTIC_BACKEND=minilm` after installing `sentence-transformers`.

---

## 5. Identity and security

Two different “roles” exist:

- **Application role** on `users`: `EMPLOYEE`, `MANAGER`, `MENTOR`, `HR_ADMIN`, `SYSTEM_ADMIN`. This is authorization.
- **Target role** in the career catalog (`roles`): ML Engineer, Data Scientist, and so on. This is a competency profile, not a login role.

Rules:

- Passwords are hashed with bcrypt. They are never stored in plaintext.
- Access tokens carry `type=access`. Refresh tokens are persisted and revoked on logout.
- An employee can only read and write `/employees/me` and the resumes, job descriptions, and recommendations that belong to them.
- Profiles do not store demographic attributes.
- Analytics responses omit names, emails, user ids, and evidence text.
- Resume text and email are not sent to an external model.
- If an optional LLM rewrite introduces tokens that are not in the retrieved passages, the system keeps the stored-fact answer.

API envelope:

```text
Success: { "data": ..., "message": null }
Error:   { "error": { "code": "...", "message": "...", "details": [] } }
```

List endpoints for roles, skills, courses, projects, mentors, and assessments return `{ items, page, page_size, total, total_pages, sort, order }`. Page size is 1–100 (default 50). A per-IP rate limit returns HTTP 429 with the same error envelope.

OpenAPI is at `http://localhost:8000/docs`. Health is `GET /health`.

---

## 6. Data model

Alembic migrations `0001` through `0017` create the tables below. PostgreSQL is authoritative.

### People and profile

| Table | Purpose |
| --- | --- |
| `users` | Email, password hash, full name, application role |
| `refresh_tokens` | Revocable refresh JWTs |
| `employees` | Job title, department, years, weekly hours, learning preferences, selected target role |
| `education` | Degrees, owned by the employee |
| `work_experience` | Jobs, owned by the employee |
| `employee_skills` | Self-declared catalog skills at a level 1–5 |

Declaring a skill also writes a `SELF` evidence row. It does not replace resume or quiz rows.

### Taxonomy and targets

| Table | Purpose |
| --- | --- |
| `skills` | Canonical name, category, difficulty 1–5, description |
| `skill_aliases` | Alternate mentions (`ML`, `K8s`, `Postgres`) |
| `roles` | Ten career targets |
| `role_skills` | Required level, importance, criticality for each skill on a role |
| `job_descriptions` | Pasted or uploaded JD text owned by an employee |
| `job_description_skills` | Required / preferred / mentioned catalog matches |

The seed catalog has **32 skills** and **10 target roles**: Software Engineer, Backend Engineer, Data Analyst, Data Engineer, Data Scientist, ML Engineer, AI Engineer, NLP Engineer, GenAI Engineer, MLOps Engineer.

Requirement weights (configurable):

```text
Required  = 1.0
Preferred = 0.6
Mentioned = 0.4
```

### Evidence

`evidence` is append-only in spirit: a new quiz inserts a new row. Older self-declarations and resume hits stay.

| Column | Meaning |
| --- | --- |
| `source_type` | `SELF`, `RESUME`, `GITHUB`, `COURSE`, `ASSESSMENT`, `PROJECT`, `CERT`, `WORK` |
| `source_id` | Resume id, attempt id, and so on |
| `extracted_level` | Estimated level on a 1–5 scale |
| `reliability` | How much this source type is trusted |
| `strength` | How strong this particular hit is |
| `recency` | How recent the evidence is |
| `inferred` | Resume hits are inferred, not verified facts |

`GITHUB` is a configured source type. Nothing writes GitHub rows yet.

`resumes` stores the file path and extracted text.

### Learning resources

Seeded from `datasets/processed/resource_catalog.json` (synthetic):

| Table | Seed size |
| --- | --- |
| `courses` + `course_skills` | 26 courses |
| `projects` + `project_skills` | 14 projects |
| `mentors` + `mentor_skills` | 10 mentors |

Catalog mentors are people in the resource catalog. They are not `users` with application role `MENTOR`.

### Decisions that are stored

| Table | What is kept |
| --- | --- |
| `recommendation_results` | Rank, final score, component scores, matched gaps, reason, explanation facts |
| `practice_pairings` | Course-then-project pair for a major gap |
| `mentor_matches` | Overlap, hours, open slots, machine-readable `why` |
| `learning_paths` + `learning_path_steps` | Chosen method, deadline, stages, adaptations |
| `assessments`, `assessment_questions`, `assessment_attempts`, `assessment_answers` | Quiz bank and attempts |
| `assistant_turns` | Question, grounded answer, whether an LLM rewrote it |

Gaps themselves are computed on read. They are not stored as their own table.

---

## 7. Algorithms

### 7.1 Skill normalization

`ML`, `machine-learning`, and `MachineLearning` must become one skill. The normalizer lowercases, strips punctuation, and splits camel case. The mapper then returns:

```text
{ skill_id, canonical_name, confidence }
```

or unmatched. Exact catalog names score higher than aliases. The API does not invent a skill for an unknown string.

### 7.2 Resume extraction

```text
File (PDF, DOCX, TXT)
    → text extraction
    → cleaning and section split
        (skills, experience, projects, certifications, education, summary, other)
    → dictionary match against the taxonomy
    → proficiency estimate and confidence
    → RESUME evidence row (inferred = true)
```

Section weights (skills 1.0, experience 0.9, projects 0.85, down to other 0.45) and mention frequency adjust confidence. Proficiency uses deterministic cues such as wording and section, and is an estimate, not a verified level.

Layer 3 (sentence-transformer fallback) and layer 4 (LLM for ambiguous mentions) are not in the extractor. If the catalog does not know the term, it is omitted.

Job descriptions use the same taxonomy. A pasted or uploaded JD becomes required, preferred, and mentioned skills with the weights above.

### 7.3 Evidence aggregation

For each skill with at least one evidence row:

```text
w_e = reliability × strength × recency          (clamped to 0–1)

C(s) = 1 − Π (1 − w_e)                          confidence

L_cur(s) = Σ (w_e × level_e) / Σ w_e            current level, clamped to 0–5
```

Self-declaration reliability defaults to 0.3, so a resume or quiz can outweigh a self-claim. If two or more levels disagree enough (variance at or above the configured threshold), the skill is flagged `conflict` and the UI suggests an assessment.

Confidence labels: HIGH ≥ 0.7, MEDIUM ≥ 0.4, otherwise LOW.

### 7.4 Skill gaps

```text
Gap_basic(s) = max(0, L_required − L_current)

Gap(s) = Gap_basic × I × C × R × E
```

`I` is role importance, `C` is confidence, `R` is criticality, `E` is evidence strength. Each factor is clamped to 0–1. Extra research weights default to 1.0 so the formula matches the product definition until an experiment changes them.

If the employee has no evidence for a required skill, `L_cur = 0` and `C` and `E` are set to 1 so the missing skill is not multiplied down to zero.

Priority bands (thresholds are configurable):

| Band | Gap |
| --- | --- |
| None | 0 |
| Low | above 0 up to 0.5 |
| Medium | above 0.5 up to 1.0 |
| High | above 1.0 up to 2.0 |
| Critical | above 2.0 |

For a job description, criticality `R` uses the same value as importance `I`.

### 7.5 Recommendation

Only resources that teach at least one of the top open gaps are scored (`REC_TOP_GAP_COUNT`).

**Baselines**

| Method | Score |
| --- | --- |
| Popularity | Catalog proxy: course rating / 5, mentor years / 15, project skill count / 6. There is no click log. |
| Content | Cosine of the gap vector and the resource’s taught-level vector |
| Semantic | Cosine of embeddings of the gap summary and the resource text |
| Knowledge graph | 1.0 if the skill is a top gap, 0.75 if it is an ancestor of a top gap, 0.4 if it is only related |

**Hybrid (default)** is a weighted mean of seven signals. Weights `REC_W_*` default to 1.0.

| Signal | Meaning |
| --- | --- |
| semantic | Embedding cosine |
| gap | Same cosine as the content baseline |
| prerequisite | Share of immediate DAG parents of the taught gap skills that are not still open |
| difficulty | `1 − \|resource difficulty − learner level\| / 4` |
| preference | Course format vs the employee’s preferred formats |
| collaborative | Jaccard of declared skill ids and resource skill ids (cold-start proxy) |
| kg | Graph relation to the open gaps |

Every request stores rank, final score, each component, matched skills, and a reason string.

### 7.6 Practice pairs and mentors

Major gaps (Critical and High; Medium if there is no major gap) each get one course and then one project that teach that skill. A course and a project are used at most once in a batch. Project ranking mixes taught level, gap priority, difficulty versus current level, a stretch of about one level, duration versus weekly hours, technology overlap, and overlap with the target role.

Mentor matching is separate from the hybrid mentor list. Signals: skill overlap with top gaps, domain overlap with the role category, years of experience, hours available per month, learning-goal fit, and open mentee slots (`max_mentees` until an assignment log exists). The stored `why` includes matched gap count, skill names, hours, and open slots.

### 7.7 Learning path

```text
Top open gaps
    → expand every ancestor in the prerequisite DAG
    → drop skills the learner already has
    → Kahn topological sort
    → map each step to at most one unused course and project
    → group steps as Learn first / Core / Later
```

`prerequisite_violation_count` counts DAG edges whose prerequisite appears at or after the dependent skill. A valid path has count 0. The prerequisite JSON is rejected if it contains a cycle, so invalid edges are not written to Neo4j.

Example chain the graph is built to support:

```text
Statistics → Machine Learning → Deep Learning → Transformers → LLMs → RAG
```

### 7.8 Hour-budget optimization

The topological sequence is the candidate list. Weekly hours come from the employee profile. Deadline defaults can be overridden with `deadline_weeks`.

| Method | Behavior |
| --- | --- |
| `TOPOLOGICAL` | Keep every missing skill. May exceed the hour budget. |
| `GREEDY` | Walk that order and skip a skill when it or its remaining prerequisites do not fit. |
| `ORTOOLS` (default) | CP-SAT: maximize gap coverage, then minimize hours, subject to prerequisites and `hours_per_week × deadline_weeks`. |

A resource is not selected twice. Comparison metrics: total hours, estimated weeks, skill coverage, prerequisite violations, hour-budget violations, duplicate resources, and path efficiency (coverage / weeks).

### 7.9 Assessments and adaptation

Seeded quizzes are multiple choice (`datasets/processed/assessments.json`, 13 quizzes). The table allows `MCQ`, `CONCEPTUAL`, `CODING`, and `PRACTICAL`. The seeded bank and the scorer are MCQ.

```text
percent = correct / total
extracted_level = 1 + 4 × percent
passed = percent ≥ 0.70
```

`GET` hides `correct_index`. Submit inserts a new `ASSESSMENT` evidence row and returns a path effect:

| Score | Effect |
| --- | --- |
| below 55% | `REFRESHER`: keep the skill, add `max(4, duration / 2)` hours, then re-optimize |
| 55% to below 90% | Evidence updates the profile; the skill stays in the plan |
| 90% or higher | `SKIP`: drop the skill from the candidate list, then re-optimize |

The next `GET /learning-paths` rebuilds from the latest profile and the latest quiz percents. Course completion, project completion, GitHub, and mentor feedback are not triggers, because those completion feeds are not collected.

### 7.10 Explainability and the assistant

`recommendation/explain.py` turns stored scores into numbered facts (gap addressed, priority, similarity, prerequisite fit, difficulty, preference). `llm/verbalize.py` joins those facts into a paragraph. The UI **Why?** button shows the facts.

The assistant (`llm/assistant.py`, `llm/retrieve.py`) loads only what is already stored: profile, gaps, path, quiz percents, ranked resources, and catalog descriptions. It answers in sentences built from those passages. If the passages do not contain the answer, it says so. Optional NIM rephrase is off by default.

### 7.11 What-if, digital twin, analytics

**What-if** (`GET /api/v1/what-if`) compares one to four catalog roles against the current skill profile: coverage, missing skills, estimated hours, a hypothetical path, projects, and mentor overlap. It does not change the saved target or the stored path, and it is not a hiring prediction.

**Digital twin** (`GET /api/v1/twin`) joins the profile, the target requirements, and evidence timestamps. Each skill shows current level, required level, gap, confidence, sources, and a trend:

| Trend | Rule |
| --- | --- |
| `INSUFFICIENT_DATA` | Fewer than two evidence rows |
| `IMPROVING` | Last level minus first ≥ 0.5 |
| `DECLINING` | First minus last ≥ 0.5 |
| `STABLE` | Otherwise |

`TwinPage` implements that view. The router currently sends `/twin` to `/skills`, so the dedicated screen is not in the sidebar. The API remains available.

**Analytics** (`GET /api/v1/analytics`) is limited to `MANAGER`, `HR_ADMIN`, and `SYSTEM_ADMIN`. A manager sees their own department. HR and system admins see the organization, or one department via `?department=`. The payload is skill-level bands, gap counts, and path/quiz participation. It is not a hiring prediction.

---

## 8. Knowledge graph

On startup the backend MERGEs:

- Nodes: Skill, Course, Project, Mentor, TargetRole, Employee. Assessment and Certification labels exist; they are not populated with rows.
- `PREREQUISITE_OF` from `datasets/processed/skill_prerequisites.json` (written only if the DAG is acyclic)
- `TEACHES`, `PRACTICES`, `EXPERT_IN`, `REQUIRES`, `HAS_SKILL`
- `RELATED_TO`, `COMPLEMENTS`

```text
GET /api/v1/graph/status                 acyclic flag and counts
GET /api/v1/graph/skills/{skill_id}      prerequisites, chain, courses, projects, mentors
GET /api/v1/graph/gap-mentors            mentors for the employee’s open gaps
```

The Gaps page has a Graph tab (`/gaps?tab=graph`). `/graph` redirects there.

---

## 9. Frontend

Authenticated pages sit under `AppLayout`. Navigation is grouped.

| Group | Route | Screen |
| --- | --- | --- |
| — | `/login`, `/register` | Auth |
| — | `/dashboard` | Home, profile completeness |
| You | `/profile` | Profile, education, experience, declared skills, target role |
| You | `/resume` | Upload and inferred skills |
| Skills | `/skills` | Estimated levels, confidence, evidence, conflicts |
| Skills | `/gaps` | Gap cards and current vs required bars; Graph tab |
| Learn | `/path` | Foundation / core / later timeline, method comparison, adaptations |
| Learn | `/recommendations` | Hybrid or baseline ranking, component scores, Why? |
| Learn | `/practice` | Course then project for each major gap |
| Learn | `/mentors` | Overlap, hours, slots, Why? |
| Learn | `/assessments`, `/assessments/:id` | Quiz list and attempt |
| Learn | `/resources` | Unranked catalog, filterable by skill |
| — | `/assistant` | Grounded Q&A and recent turns |
| Explore | `/compare` | What-if role comparison |
| Explore | `/roles` | Catalog role skill profiles and job descriptions |
| — | `/analytics` | Manager / HR / system admin only |

Zustand holds the session. React Query loads API data. Protected routes require a valid access token. Analytics uses a role gate.

---

## 10. API catalog

All paths are under `/api/v1`. Authenticated calls send `Authorization: Bearer <access_token>`.

| Area | Methods |
| --- | --- |
| Auth | `POST /auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`; `GET /auth/me` |
| Profile | `GET/PUT /employees/me`; education and experience CRUD under `/employees/me/education` and `/experience`; skill CRUD under `/employees/me/skills` |
| Skill profile | `GET /employees/me/skill-profile` |
| Resume | `GET/POST /employees/me/resumes`, `GET /employees/me/resumes/{id}` |
| Taxonomy | `GET /skills`, `POST /skills/resolve` |
| Roles | `GET /roles`, `GET /roles/{id}` |
| Job descriptions | `GET/POST /job-descriptions`, upload, `GET /job-descriptions/{id}` |
| Gaps | `GET /gap-analysis` |
| Graph | `GET /graph/status`, `/graph/skills/{id}`, `/graph/gap-mentors` |
| Catalog | `GET /courses`, `/projects`, `/mentors` and `/{id}` |
| Recommendations | `GET /recommendations/courses\|projects\|mentors` (`method=HYBRID\|CONTENT\|POPULARITY\|SEMANTIC\|KG`) |
| Practice | `GET /recommendations/practice-pairs` |
| Mentors | `GET /recommendations/mentor-matches` |
| Path | `GET /learning-paths?method=ORTOOLS\|GREEDY\|TOPOLOGICAL&deadline_weeks=` |
| Assessments | `GET /assessments`, `GET /assessments/{id}`, `POST /assessments/{id}/attempts` |
| Assistant | `POST /assistant/ask`, `GET /assistant/turns` |
| What-if | `GET /what-if?role_ids=` |
| Twin | `GET /twin` |
| Analytics | `GET /analytics` |
| Admin | `GET /admin/ping` |

---

## 11. Research evaluation

`ml/evaluation/` compares ranking methods on labeled synthetic sets. Results are recorded in `docs/research/evaluation-results.md`. They do not represent real employees.

On the synthetic recommendation set at K = 5, hybrid NDCG@5 was 0.946. Popularity and semantic scored higher on that small set (NDCG 0.985 and 1.000). An ablation that removed the difficulty signal raised hybrid NDCG, which means that signal hurt this particular labeled set. Collaborative filtering and the graph signal did not change NDCG when removed. Those numbers are a research snapshot, not a claim that one method wins in production.

Other synthetic checks in that file:

- Resume extraction: precision, recall, and F1 of 1.0 on 2 resumes
- Skill-gap ranking: NDCG@10 of 0.978 on 2 personas
- Learning path: 0 prerequisite violations, full coverage of the labeled gaps, 107.5 hours

Automated tests also cover the learner pipeline (register → resume → role → gaps → recommendations → path → quiz → rebuild) and latency checks against the product targets (API p95, extraction, gap analysis, path generation, recommendation).

---

## 12. Configuration

Weights, token lifetimes, bcrypt rounds, CORS origins, gap thresholds, recommendation weights, assessment cutoffs, and seed flags live in environment variables (`backend/app/core/config.py` and `.env.example`). Research weights are not hardcoded inside ranking functions.

Important switches:

| Variable | Effect |
| --- | --- |
| `SEED_ON_STARTUP` | Load skills, roles, resources, and quizzes if missing |
| `NEO4J_SYNC_ON_STARTUP` | Project the catalog into Neo4j |
| `REC_SEMANTIC_BACKEND` | `hashing` (default) or `minilm` |
| `REC_W_*` | Hybrid signal weights |
| `LLM_ENABLED` + `LLM_API_KEY` or `NVIDIA_API_KEY` | Optional assistant rephrase |
| `ASSESSMENT_WEAK_SCORE` / `ASSESSMENT_STRONG_SCORE` | 0.55 and 0.90 by default |

---

## 13. What is intentionally not in the product

- **GitHub evidence (phase 20).** The source type exists. There is no OAuth collector and no repository analysis.
- **Semantic and LLM skill extraction.** Unknown resume terms stay unmatched.
- **Click-based collaborative filtering.** The collaborative signal is a skill-set overlap proxy.
- **Course, project, and mentor-feedback completion** as re-optimization triggers.
- **Conceptual, coding, and practical assessments** beyond the MCQ scorer and the allowed type column.
- **pgvector and Redis.**
- **Hiring or employment predictions.** What-if and analytics report competency coverage and learning effort only.
- **Phase 28.** Compose files for Postgres, Neo4j, backend, and frontend already exist. A finished deployment guide and a scripted demo scenario are still open.

---

## 14. Every feature, in detail

Each feature below is something a person can actually use in the running app. The description covers what it is for, what the screen does, what the server calculates, what gets stored, and the limits of that feature.

### 14.1 Register and log in

**Purpose.** Create an account and prove who is calling the API.

**What you do.** Open `/register`, enter full name, email, password, and an application role (`EMPLOYEE`, `MANAGER`, `MENTOR`, `HR_ADMIN`, or `SYSTEM_ADMIN`). Open `/login` with email and password. The app stores the access token and uses it on later requests. Logout revokes the refresh token.

**What the system does.**

1. Registration creates a `users` row and a linked `employees` row. The password is hashed with bcrypt at cost 12. The plaintext password is never stored.
2. Login checks the hash and returns two JWTs. The access token lasts 15 minutes and carries `type=access` plus the application role. The refresh token lasts 7 days, is stored by its `jti`, and can be revoked.
3. `POST /auth/refresh` issues a new pair if the refresh token is still valid. `POST /auth/logout` revokes it. `GET /auth/me` returns the current user.
4. Every later route that needs a person checks the access token. An employee can only touch their own profile, resumes, job descriptions, and recommendations.

**What is stored.** `users`, `employees` (empty profile at first), `refresh_tokens`.

**Limits.** This role is authorization, not a career target. Choosing `MENTOR` at registration does not put you in the mentor catalog. Session storage is the browser; there is no Redis session store.

### 14.2 Home

**Purpose.** A landing page after login that shows whether the profile is ready to drive the rest of the product.

**What you see.** Your name, profile completeness as a percent, the selected target role (or “Not selected”), and the count of self-declared skills. Shortcuts go to Profile, Gaps, Path, and Recommend. Managers, HR admins, and system admins also see Analytics.

**What the system does.** `GET /employees/me` returns the profile and a completeness score. Completeness is 8 yes/no items: job title, department, years of experience, at least one education row, at least one work-experience row, at least one declared skill, a target role, and learning preferences. The score is `completed / 8`.

**What is stored.** Nothing new. Home only reads the profile.

**Limits.** Completeness does not include resume, quizzes, or gaps. A 100% profile can still have an empty skill estimate if the only “skills” check is a self-declaration that has not been aggregated yet — declaring a skill does write evidence, so the skill profile will have that row.

### 14.3 Employee profile

**Purpose.** Hold the facts later features need: who you are at work, how much time you can study, how you like to learn, and which career role you are aiming at.

**What you do.** On Profile, edit job title, department, years of experience, and available hours per week (1–80, default 10). Pick a target role from the ten catalog roles. Set a free-text pace and check learning formats: video, text, hands-on, live. Full name and email are shown and cannot be edited here. Save writes `PUT /employees/me`.

**Why the fields matter later.**

| Field | Used by |
| --- | --- |
| Department | Manager analytics scope |
| Hours per week | Path capacity (`hours × deadline weeks`) and project duration fit |
| Learning formats | Hybrid preference signal (video courses match a video preference, projects count as hands-on, mentors as live or hands-on) |
| Target role | Default target for gaps, recommendations, practice, mentors, path, and the twin |
| Years of experience | Profile completeness only; it is not a skill level |

**What is stored.** Columns on `employees`, including `learning_preferences` as structured JSON.

**Limits.** Changing the target role does not delete old recommendation rows. The next gap, recommend, or path request rebuilds against the new target. There are no demographic fields.

### 14.4 Education and work experience

**Purpose.** Record background on the profile. These rows are part of completeness. They are not, by themselves, skill evidence.

**What you do.** Add, edit, and delete education (institution, degree, field, dates) and work experience (employer, title, dates, description) on the same Profile page.

**What the system does.** Standard CRUD under `/employees/me/education` and `/employees/me/experience`. Rows are owned by the logged-in employee. Another user cannot read them.

**What is stored.** `education` and `work_experience`.

**Limits.** The text in a job description on the experience form is not run through the skill extractor. Only an uploaded resume or a job-description analysis extracts skills. There is no `WORK` evidence row written from these forms unless a later feature adds one. The source type exists; this screen does not emit it.

### 14.5 Self-declared skills

**Purpose.** Let the employee claim a catalog skill at a level from 1 to 5. The claim is evidence with low reliability, not a verified fact.

**What you do.** On Profile, pick a skill that is not already on the profile and set a level. The dropdown is the seeded catalog (canonical names). You can remove a declaration. The form also has a mention lookup: type `ML` or `K8s` and the API resolves it to one catalog skill or says it is unmatched.

**What the system does.**

1. `POST /employees/me/skills` inserts `employee_skills` and a `SELF` evidence row.
2. Reliability for self-declaration defaults to 0.3, so a later resume hit or quiz can outweigh it when levels are aggregated.
3. `POST /skills/resolve` runs the same normalizer the resume pipeline uses. Exact names get a higher mapping confidence than aliases. Unknown strings return unmatched. The API does not create a new skill.

**What is stored.** `employee_skills` and an evidence row with `source_type=SELF`.

**Limits.** You cannot declare a skill that is not in the catalog. Removing a declaration removes that self row; it does not delete resume or quiz evidence for the same skill.

### 14.6 Skill taxonomy

**Purpose.** One vocabulary for the whole product. `ML`, `machine learning`, and `machine-learning` must be the same skill, or gaps and courses cannot line up.

**What you do.** You do not edit the taxonomy in the UI. You see canonical names everywhere: profile, resume hits, gaps, catalog filters, graph, quizzes.

**What the system does.** Each skill has a canonical name, a display name, a category, a difficulty from 1 to 5, a description, and aliases in `skill_aliases`. The normalizer lowercases, strips punctuation, and splits camel case. The mapper returns `{ skill_id, canonical_name, confidence }` or unmatched. `GET /skills` lists the catalog and can filter by category. Lists are paginated.

**What is stored.** `skills`, `skill_aliases`, seeded from `datasets/processed/skill_taxonomy.json` (32 skills) on startup when `SEED_ON_STARTUP=true`.

**Limits.** The catalog is a starter inventory, not a full industry taxonomy. A term that is not seeded is invisible to extraction, gaps, and recommendations.

### 14.7 Resume upload and skill extraction

**Purpose.** Turn a resume file into inferred skill evidence without overwriting what the employee declared.

**What you do.** On Resume, choose a PDF, DOCX, or TXT file and submit. The page lists previous uploads with status and inferred-skill count. Opening one shows each matched skill, an estimated level out of 5, a confidence, the resume section it came from, and an “inferred” badge. If nothing in the file matches the catalog, the message says unknown terms were left unmatched.

**What the system does.**

1. The file is saved and its text is extracted.
2. The text is cleaned and split into sections: skills, experience, projects, certifications, education, summary, and other.
3. A dictionary matcher finds catalog names and aliases. It does not guess with a language model.
4. Each skill is grouped across mentions. Confidence combines match type (exact vs alias), section weight (skills 1.0, experience 0.9, projects 0.85, certifications 0.8, education 0.65, summary 0.55, other 0.45), and how often the term appears.
5. Proficiency is a rule estimate from wording and context, on a 1–5 scale. It is not a verified level.
6. Each hit is inserted as `RESUME` evidence with `inferred=true` and a snippet. `employee_skills` is left unchanged.

**What is stored.** `resumes` (path, extracted text, status) and one `evidence` row per extracted skill for that upload.

**Limits.** Sentence-transformer fallback and an LLM pass for ambiguous phrases are not implemented. A skill the catalog does not know is dropped. Uploading again adds evidence; it does not delete the previous resume’s evidence. The UI does not show the raw snippet in the card list; the evidence record still keeps it for the skill profile.

### 14.8 Target roles

**Purpose.** A reusable competency profile: which skills a career needs, at what level, and how important each one is.

**What you do.** On Roles, pick a catalog role. The page groups its skills into Required, Preferred, and Mentioned, with the required level. Your saved target is the default selection. Choosing a role here browses the catalog. Saving a target is done on Profile.

**What the system does.** `GET /roles` and `GET /roles/{id}` read `roles` and `role_skills`. Each role skill has a required level (1–5), an importance weight, and a criticality weight. Seeded importance uses 1.0 for required skills and 0.6 for preferred skills. These weights later multiply the gap.

The ten roles are Software Engineer, Backend Engineer, Data Analyst, Data Engineer, Data Scientist, ML Engineer, AI Engineer, NLP Engineer, GenAI Engineer, and MLOps Engineer.

**What is stored.** Seed data in `roles` and `role_skills`. Browsing does not write a user-specific row. Profile save sets `employees.target_role_id`.

**Limits.** You cannot author a new role in the UI. Role skills are the seed, not an HR-edited framework editor.

### 14.9 Job description analysis

**Purpose.** Use a specific posting instead of a catalog role as the target competency profile.

**What you do.** On Roles, paste a title and at least 20 characters of job text, or upload a PDF, DOCX, or TXT file. The result lists mapped skills in the same Required / Preferred / Mentioned groups. Unknown terms are omitted and the page says so. Saved descriptions can be reopened. Gaps can then target one of those saved descriptions instead of a catalog role.

**What the system does.** The same taxonomy mapper used on resumes labels each hit:

| Label | Weight |
| --- | --- |
| Required | 1.0 |
| Preferred | 0.6 |
| Mentioned | 0.4 |

Weights are configurable. The job description is owned by the employee. It does not replace the saved target role, and it does not overwrite resume evidence or self-declared skills. For gap math, a JD has importance but no separate criticality column, so criticality uses the same value as importance.

**What is stored.** `job_descriptions` and `job_description_skills`.

**Limits.** The extractor only keeps catalog skills. A custom tool named in the posting and missing from the taxonomy never becomes a gap.

### 14.10 Evidence-based skill profile

**Purpose.** Answer “what is this person’s estimated level, why, how sure are we, and do the sources disagree?”

**What you see.** Skills shows three counts: skills that have any evidence, how many are in conflict, and the configured self-declaration reliability (default 0.3). Each skill card shows the canonical name, a HIGH / MEDIUM / LOW confidence badge, an “inferred” badge when every supporting row is inferred, and a conflict badge when sources disagree. The line under the name is estimated level out of 5 and the numeric confidence. A conflict suggests a quiz. Every evidence row is listed with its source (self-declared, resume, quiz, and so on), its level, and whether it is inferred.

**What the system does.** `GET /employees/me/skill-profile` loads all evidence for the employee and aggregates per skill:

```text
weight = reliability × strength × recency
confidence = 1 − product of (1 − weight) over the rows
level = weighted average of the row levels
```

If two or more levels vary at or above the conflict threshold, the skill is flagged and an assessment is recommended. Confidence labels are HIGH at or above 0.7, MEDIUM at or above 0.4, otherwise LOW. Empty evidence means the skill does not appear. Missing skills show up later, in gap analysis, as level 0.

**What is stored.** Nothing on this read. The page is a view over `evidence`.

**Limits.** The number is an estimate. An inferred-only card is explicitly not a verified fact. GitHub, completed courses, projects, certifications, and work evidence types are recognized in the labels, but only self-declaration, resume, and assessment rows are produced by the current app.

### 14.11 Skill gap analysis

**Purpose.** Rank the difference between the estimated profile and a target, so later recommendations know what to teach first.

**What you do.** On Gaps, choose Catalog role or Saved job description. The role list marks your saved target. If you have not analyzed a job description, the JD mode tells you to do that on Roles first. The page then shows the target name and counts of open, critical, high, medium, and low gaps. A bar chart shows the top eight open gaps. Each skill card shows priority, requirement type (required, preferred, or mentioned), inferred and conflict badges when those apply, the numeric gap, and two bars: current level versus required level.

**What the system does.** `GET /gap-analysis` is computed on each request. It is not a stored table.

```text
basic = max(0, required level − current level)
gap   = basic × importance × confidence × criticality × evidence strength
```

Priority is None at 0, Low up to 0.5, Medium up to 1.0, High up to 2.0, and Critical above 2.0. A required skill with no evidence uses current level 0 and confidence and evidence strength of 1, so the gap is not multiplied away to nothing. Skills the learner already meets stay in the list as None so the comparison is visible, and they are excluded from the open-gap chart.

**What is stored.** Nothing. Recommendations and the path call the same calculation when they run.

**Limits.** This screen does not pick courses. Comparing a role here does not change the saved target on the profile. There is no radar chart; the comparison is bars.

### 14.12 Knowledge graph

**Purpose.** Show how a skill depends on other skills, and which courses, projects, and mentors are attached to it.

**What you do.** On Gaps, open the Graph tab (or visit `/graph`, which redirects there). Pick a skill. The panel defaults to RAG when that skill exists. A status line says whether the prerequisite graph is acyclic and how many skill nodes Neo4j has. The view draws the prerequisite chain and lists courses that teach the skill, projects that practice it, and mentors who cover it.

**What the system does.** PostgreSQL remains the source of truth. On API startup, if `NEO4J_SYNC_ON_STARTUP` is true, the backend copies skills, courses, projects, mentors, roles, and employees into Neo4j and writes relationships: `PREREQUISITE_OF` from `datasets/processed/skill_prerequisites.json`, plus `TEACHES`, `PRACTICES`, `EXPERT_IN`, `REQUIRES`, `HAS_SKILL`, `RELATED_TO`, and `COMPLEMENTS`. If the JSON contains a cycle, those prerequisite edges are not written. `GET /graph/status` reports the acyclic flag. `GET /graph/skills/{id}` returns the immediate prerequisites, the full chain, and the linked resources. `GET /graph/gap-mentors` lists mentors for the employee’s open gaps.

**What is stored.** The Neo4j projection. Editing PostgreSQL and restarting (or re-syncing) rebuilds it. The graph is not edited from the UI.

**Limits.** Assessment and Certification labels exist in the schema without rows. If Neo4j is down, the tab shows that it is not reachable. Path ordering can still use the same JSON file inside the recommendation package; the picture on this tab cannot.

### 14.13 Resource catalog

**Purpose.** Browse the inventory of courses, projects, and mentors before any ranking. Ranking is a different screen.

**What you do.** On Catalog, filter by one skill or show everything. Switch among Courses, Projects, and Mentors. A course card shows title, provider, hours, difficulty, format, rating, and the skills it teaches. A project card shows title, hours, difficulty, technologies, and skills. A mentor card shows name, title, expertise, and skills. Nothing on this page is ordered by your gaps.

**What the system does.** `GET /courses`, `/projects`, and `/mentors` read PostgreSQL. Optional `skill_id` keeps resources linked to that skill. Results are paginated, sortable, and filterable. The rows were seeded from `datasets/processed/resource_catalog.json`: 26 courses, 14 projects, and 10 mentors. Descriptions are synthetic. Skill links use taxonomy names, so a course that teaches Python is the same Python as the gap engine.

**What is stored.** `courses`, `course_skills`, `projects`, `project_skills`, `mentors`, `mentor_skills`. Browsing does not write a recommendation.

**Limits.** Catalog mentors are not application users. There is no enrollment, completion, or rating-by-learner. URLs point at example hosts.

### 14.14 Recommendations

**Purpose.** Rank catalog courses, projects, and mentors against the employee’s open skill gaps, and keep every component score so the rank can be explained and compared.

**What you do.** On Recommend, pick a method and a tab: Courses, Projects, or Mentors. Methods are Hybrid (default), Content-based, Popularity, Semantic, and Knowledge graph. The page names the target. Each row shows rank, title, a short meta line, a Why? control, and the gap skills that resource matched, with priority and gap size. If there is no target or no open gap, the page says to select a role or job description first. If nothing in the catalog teaches the top gaps, it says so.

**What the system does.**

1. Run gap analysis for the saved target role, or for a `role_id` or `job_description_id` passed to the API.
2. Keep the top open gaps (priority other than None), limited by `REC_TOP_GAP_COUNT`.
3. Score only resources that teach at least one of those skills.
4. Compute the selected method. Hybrid is a weighted mean of seven signals: semantic similarity, gap relevance (the content cosine), prerequisite fit, difficulty fit, format preference, a collaborative proxy (overlap of declared skills, because there is no click history), and knowledge-graph relation (direct gap, ancestor of a gap, or only related). Weights default to 1.0 and are environment variables.
5. Persist the batch: rank, final score, each component, matched skills, and a deterministic reason.

Popularity is a stand-in, not real popularity: course rating divided by 5, mentor years divided by 15, project skill count divided by 6. Semantic similarity is cosine of a gap summary and the resource text. The default encoder is a hashing bag-of-words so the app runs without downloading a transformer model. `REC_SEMANTIC_BACKEND=minilm` switches to `all-MiniLM-L6-v2`.

The Knowledge graph method ranks with only the graph signal. It is a research baseline, not the default.

**What is stored.** `recommendation_results` for that request, including the explanation facts added in the explainability feature.

**Limits.** The list is not a sequence. A higher rank does not mean “take this before that.” Prerequisite order is the Path feature. The collaborative signal is not collaborative filtering over other employees’ clicks.

### 14.15 Why? explanations

**Purpose.** Show the reason for a recommendation as facts that were actually scored, not as a paragraph invented by a model.

**What you do.** On Recommend, Practice, Mentors, and Path, click Why? on a card. A numbered list opens. Hide why closes it. If a row has no facts, the button is absent.

**What the system does.** `recommendation/explain.py` reads the stored component scores, matched skills, and gap priority and writes short sentences, for example that the item addresses a named gap, that the priority is critical, that semantic similarity is a specific number, that prerequisites are satisfied, that difficulty is close to the learner, or that the format matches a preference. `llm/verbalize.py` can join those same sentences into one paragraph. An optional model may rephrase only those sentences. It is not allowed to add a skill or a score that was not stored. The UI shows the numbered facts.

**What is stored.** `explanation = { facts, verbalization }` on the recommendation, practice pair, mentor match, or path step.

**Limits.** Why? does not re-rank anything. If the underlying score was a popularity proxy, the facts say that, rather than pretending people clicked the course.

### 14.16 Practice pairs

**Purpose.** For each major gap, propose one course and then one project that both teach that skill, so learning is tied to practice.

**What you see.** Practice lists the target and the number of pairs. Each card is a three-step row: the skill (current level toward required level), a course (hours and difficulty), and a project (hours and technologies). The header shows priority and the pair score. Why? explains the pair.

**What the system does.** `GET /recommendations/practice-pairs` takes Critical and High gaps. If there are none, it uses Medium. For each skill it searches the catalog for a course and a project that teach it, and it will not reuse a course or project inside the same batch. The course is preferred when its difficulty is at or below the project’s difficulty. The project score is a weighted mean of taught level, gap priority, difficulty versus current level, a stretch of about one level above the learner, duration versus weekly hours, overlap of technologies with skills the learner already has, and overlap with the target role’s skill set.

**What is stored.** `practice_pairings` with rank, score, component JSON, and reason.

**Limits.** A pair is not placed on a calendar and is not checked against the full prerequisite chain. That is the path. If the catalog has a course but no project for that skill, there is no pair. This feature does not include the quiz; the path step links to a quiz when one exists.

### 14.17 Mentor matching

**Purpose.** Rank catalog mentors by how well they cover the employee’s open gaps, and say why in numbers.

**What you see.** Mentors shows the target, then a ranked list. Each card has the mentor’s name and title, “N of M gaps,” Why?, and chips for the matched skills. Hours per month and open slots are part of the stored why payload and the explanation facts.

**What the system does.** This matcher is separate from the hybrid mentor list on Recommend. `GET /recommendations/mentor-matches` scores six signals: overlap with the top open gaps, domain overlap with the target role’s category, years of experience divided by 15, available hours per month divided by 12, fit to learning goals (role-skill coverage plus live or hands-on preference), and open mentee slots divided by `max_mentees`. There is no assignment log, so open slots start at the mentor’s maximum. The `why` object stores matched gap count, top gap count, matched skill names, hours, open slots, and domains.

**What is stored.** `mentor_matches`.

**Limits.** Matching does not book a session or notify a person. A catalog mentor has no login. Workload does not decrease when several employees match the same mentor.

### 14.18 Learning path

**Purpose.** Turn gaps into an order: missing foundations first, then the skills that depend on them, with a course and a project on each step when the catalog has one left.

**What you see.** Path shows the target, total hours versus capacity, and an estimated number of weeks. Steps are grouped as Learn first, Core, and Later. Each step has a position, the skill name, a Review prefix if a weak quiz added a refresher, status (Not started, In progress, or Completed), difficulty, the week or week range, and duration. Why? is on the step. Under the skill, the course and project titles appear when they were mapped. If a seeded quiz exists for that skill, the step links to Take quiz or Retake quiz. “Show all skills” switches from the hour-budget plan to the full topological list. “Fit to hours” switches back. If nothing fits, the page says to raise weekly hours on Profile or use a longer deadline.

**What the system does.** `GET /learning-paths` rebuilds the plan from the current profile. It does not reuse a stale plan blindly.

1. Take the top open gaps for the target.
2. Walk every ancestor in the prerequisite DAG.
3. Drop skills the learner already has, so known foundations are not assigned again.
4. Topologically sort the remainder. `prerequisite_violation_count` must be 0: a prerequisite never appears at or after the skill that needs it.
5. Map each step to at most one unused course and one unused project.
6. Label stages Foundation, Core, and Advanced, which the UI calls Learn first, Core, and Later.
7. Before the solver runs, apply quiz adaptations (see 14.20).

**What is stored.** `learning_paths` and `learning_path_steps`, including adaptations.

**Limits.** “Show all skills” may exceed the hour budget; the summary says so when the full list is longer than capacity. Status is not a full progress tracker for courses. A step becomes completed when assessment evidence says the skill is satisfied, not when someone clicks a course URL.

### 14.19 Path optimization

**Purpose.** Choose a subset of that ordered list that respects weekly hours and a deadline, and show how three algorithms differ.

**What you do.** The default Path request uses OR-Tools. The API accepts `method=ORTOOLS|GREEDY|TOPOLOGICAL` and `deadline_weeks`. Weekly hours always come from the profile. The response includes a comparison of the three methods: total hours, coverage, violations, and efficiency. The screen’s “Show all skills” control is the topological method; the default view is the optimized subset.

**What the system does.**

| Method | Rule |
| --- | --- |
| Topological | Keep every missing skill. Hours may exceed `hours per week × deadline weeks`. |
| Greedy | Walk the same order and skip a skill when it or a still-missing prerequisite does not fit. |
| OR-Tools | CP-SAT. Maximize coverage of the important gaps, then minimize hours. If a skill is selected, its missing prerequisites are selected. A resource is not used twice. |

Reported metrics are total hours, estimated weeks, skill coverage, prerequisite violations, an hours-violation flag, duplicate resource count, and path efficiency (coverage divided by weeks).

**What is stored.** The chosen method’s steps, plus the comparison payload on the path record.

**Limits.** Assessments do not add duration until a weak quiz creates a refresher. The solver does not know about meetings, holidays, or a real calendar. Deadline weeks default from configuration when the client does not send one.

### 14.20 Assessments and adaptive rebuild

**Purpose.** Check a skill with a quiz, record the result as new evidence, and let a very weak or very strong score change the next path.

**What you do.** Assess lists seeded quizzes: skill name, question count, pass percent (default 70), and either “not started” or the last score. Take quiz opens the questions. Choices are hidden from the answer key. You must answer every question before submit. The result shows percent, pass or fail, and per-question feedback. The skill profile, gaps, and path queries are refreshed. A score under 55% makes the next Path show a Review step with extra hours. A score of 90% or higher drops that skill so later steps can start sooner. Between those cutoffs the evidence updates and the skill stays in the plan without a special skip or review.

**What the system does.**

```text
percent = correct / total
level   = 1 + 4 × percent
passed  = percent ≥ 0.70
```

`GET /assessments/{id}` does not return `correct_index`. `POST .../attempts` scores the submission, stores each answer, and inserts a new `ASSESSMENT` evidence row pointing at the attempt. Older self-declarations and resume rows remain. The attempt response includes `path_effect`: `REFRESHER`, `SKIP`, or null. The next path GET runs `recommendation/path/adapt.py` before the optimizer:

- Below 55%: keep the skill, mark it as a refresher, add `max(4, duration / 2)` hours, then re-optimize.
- At or above 90%: remove the skill from the candidate list, then re-optimize.
- Otherwise: no structural change.

The database allows assessment types MCQ, CONCEPTUAL, CODING, and PRACTICAL. The seeded bank and the scorer are multiple choice (13 quizzes in `datasets/processed/assessments.json`).

**What is stored.** `assessments`, `assessment_questions`, `assessment_attempts`, `assessment_answers`, a new evidence row, and `learning_paths.adaptations` on the next path build.

**Limits.** Retaking adds another evidence row; it does not erase the previous attempt. Course completion, project completion, GitHub activity, and mentor feedback do not trigger a rebuild. A manual skill update does, because the path is rebuilt from the profile on the next GET. There is no proctoring.

### 14.21 Learning assistant

**Purpose.** Answer questions about this employee’s stored situation, and refuse when the answer is not in that material.

**What you do.** Assistant offers six starters: what to learn next, what the current path is, why a skill such as Statistics is needed, explain a topic such as transformers, ask for a project for a skill such as RAG, and why a course was recommended. You can also type a question of at least three characters. Each turn shows the question, the answer, and the source labels (path, gaps, catalog, and so on). Previous turns are loaded when the page opens.

**What the system does.** `POST /assistant/ask` retrieves passages from the stored profile, open gaps, the latest path, quiz percents, saved recommendation reasons, and catalog descriptions. It classifies the question into next-step, full path, why a skill is needed, project, why a recommendation, explain-a-topic, or a generic question. The answer is written from those passages only. Path questions read the stored path, not a fresh course list. If the passages do not contain the fact, the answer is: it does not have that in the profile, path, or catalog, and it will not invent it.

An NVIDIA NIM model (`openai/gpt-oss-20b`) may rephrase the draft only when `LLM_ENABLED` is true and `LLM_API_KEY` or `NVIDIA_API_KEY` is set. If the rewrite introduces tokens that are not in the passages, the original fact answer is kept. Email and resume text are not sent.

**What is stored.** `assistant_turns` for that employee. `GET /assistant/turns` returns them.

**Limits.** The assistant does not change ranks, gaps, or the path. It cannot see GitHub, other employees, or anything you did not already store. A generic question that does not match a skill, path step, or catalog title gets the unavailable sentence.

### 14.22 What-if role comparison

**Purpose.** Compare catalog careers against the current skill profile without committing to a new target.

**What you do.** Compare lets you check up to four roles. If you have not chosen yet, it starts with your current target plus other catalog roles, up to three. The note on the page says this is not a hiring prediction. The table has one row per role: coverage percent and covered/total skills, the first missing skill names (or “None open”), estimated hours and weeks at your weekly availability, a hypothetical path written as skill names joined by arrows, project titles, and how many mentors cover the open gaps, with names. The current target is labeled on its row.

**What the system does.** `GET /what-if?role_ids=` runs gap analysis and a hypothetical path for each selected role using the same current profile. Coverage is how much of that role’s skill list the employee already meets. Effort is the estimated hours of the hypothetical plan. Projects and mentors are catalog matches for that scenario’s gaps. Nothing writes `employees.target_role_id` and nothing replaces the stored learning path.

**What is stored.** The response is computed. It is not a saved simulation history.

**Limits.** One to four roles. The path column is a skill sequence for comparison, not the hour-budget plan saved on Path. It does not predict being hired.

### 14.23 Skill digital twin

**Purpose.** One table of competency state per skill: current, required, gap, confidence, which evidence sources exist, and whether the level is moving.

**What the API returns.** `GET /twin` joins the skill profile, the target role’s requirements, and evidence timestamps. Trend rules: fewer than two evidence rows is “not enough data”; last level at least 0.5 above the first is improving; first level at least 0.5 above the last is declining; otherwise stable. Filters in the page component are all skills, open gaps, and conflicts. GitHub is listed as a possible source and stays absent.

**What you see today.** `TwinPage` implements that table, but the router sends `/twin` to `/skills`. The sidebar does not open the twin. Skills remains the evidence view (levels, confidence, conflict, source chips) without the required-level and trend columns. The twin endpoint still works for a client that calls it.

**What is stored.** Nothing. The twin does not change the target or the path.

**Limits.** Trend only reflects evidence rows that exist, in time order. It is not a forecast. It is not a hiring score.

### 14.24 Manager and HR analytics

**Purpose.** Show department or organization patterns without exposing a person.

**Who can open it.** `MANAGER`, `HR_ADMIN`, and `SYSTEM_ADMIN`. Employees do not see the nav item. A manager must have a department on their profile and only sees that department. HR and system admins see the organization, or one department with `?department=`. The page title is “Team” or “Organization,” with the note “Counts only. No names.”

**What you see.**

- Scope label and headcount.
- A heatmap: for each skill, how many people sit in level bands 1 through 5, and how many are missing it.
- Top skill gaps: people with a gap, average gap, and critical/high counts.
- Training priorities: rank, skill, people, and how many catalog courses and projects teach it.
- Learning progress: how many people have quiz attempts, the pass rate, and how many have a path.
- Role frameworks: each catalog role and how many people currently target it.
- For HR, a department list with headcount.

**What the system does.** `GET /analytics` aggregates stored profiles, gap calculations against each person’s saved target, quiz attempts, and paths. The JSON has no names, emails, user ids, or evidence text.

**What is stored.** Nothing. It is a read model.

**Limits.** There is no manager-to-report assignment. “Team” means “same department string.” It does not recommend firing, promoting, or hiring. GitHub is not in the aggregate.

### 14.25 Research evaluation

**Purpose.** Compare the ranking methods on labeled synthetic data so the hybrid model can be measured against simpler baselines.

**What you do.** This is not a screen. `ml/evaluation/` runs extraction F1, gap-ranking NDCG, recommendation Precision@K, Recall@K, NDCG, MAP, coverage, and diversity, plus an ablation that removes one hybrid signal at a time, plus path violations, coverage, hours, and efficiency. Results are written up in `docs/research/evaluation-results.md`. Inputs are marked synthetic.

**What the latest synthetic snapshot says.** At K = 5, popularity and the semantic baseline outscored hybrid on that small set (NDCG 0.985 and 1.000 versus hybrid 0.946). Removing the difficulty signal raised hybrid NDCG, so on this set that signal hurt. Removing collaborative filtering or the graph signal did not change NDCG. Extraction F1 and a two-persona gap NDCG are perfect or near-perfect because the labeled files are tiny. Path prerequisite violations were zero.

**Limits.** These numbers are not evidence about real employees. The document says so. They exist so the methods can be compared, not so the product can claim a winner.

### 14.26 Platform behavior that every feature shares

**Pagination.** Role, skill, course, project, mentor, and assessment lists return a page object: items, page, page size, total, total pages, sort, and order. Page size is 1–100, default 50, which covers the current catalog in one request.

**Errors.** Failures use `{ error: { code, message, details } }`. Rate limit exceeded is HTTP 429 with that shape. The limit is an in-memory count per client IP over a configurable window.

**Authorization.** Resource ownership is enforced in services. Analytics is the only aggregate view, and it strips identity.

**Startup seed.** With `SEED_ON_STARTUP`, the API loads skills, aliases, roles, resources, and quizzes if they are missing, then optionally syncs Neo4j. Tests roll back database transactions so they do not depend on leftover rows.

---

## 15. Where to read more

| Topic | Document |
| --- | --- |
| Running the app | `README.md`, `docs/user_guides/getting-started.md` |
| Phase-by-phase status | `docs/phases/roadmap.md` |
| Short architecture notes | `docs/architecture/architecture.md` |
| Gaps | `docs/architecture/skill-gap-model.md` |
| Ranking and paths | `docs/architecture/recommendation.md` |
| Graph | `docs/architecture/knowledge-graph.md` |
| Optimizer | `docs/architecture/optimization.md` |
| Quizzes | `docs/architecture/assessment.md` |
| Why? | `docs/architecture/explainability.md` |
| Assistant | `docs/architecture/assistant.md` |
| Role comparison | `docs/architecture/what-if.md` |
| Twin | `docs/architecture/digital-twin.md` |
| Manager / HR | `docs/architecture/analytics.md` |
| Pagination and rate limits | `docs/architecture/api-hardening.md` |
| Evaluation numbers | `docs/research/evaluation-results.md` |
