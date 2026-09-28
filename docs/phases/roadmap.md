# SkillPath AI — phase-wise task list

Source of truth: `docs/prd/AI-Learning-Path-Recommender-PRD.pdf`  
Playbook: `docs/prd/SkillPath_AI_Implementation_Plan.md`  
Checked against the repo on 2026-09-20 after Phase 0 + 1.

Do **not** skip ahead. Each phase depends on the previous one producing real data, not placeholders.

---

## Current system — what we can do today

A user can:

1. Register and log in (JWT, bcrypt cost 12, five application roles).
2. View and edit an employee profile (job title, department, years, weekly hours, learning preferences).
3. Add / list / update / delete education and work experience.
4. Pick self-declared skills from a seeded catalog (1–5) and a target career role.
5. See a profile completeness score on dashboard and profile.
6. Upload a resume and see inferred catalog skills.
7. Browse a catalog role skill profile, or paste/upload a job description.
8. See an estimated current skill profile with confidence, evidence sources, and conflict flags.
9. Compare current vs required skills for a catalog role or job description.
10. Browse synthetic courses, projects, and mentors mapped to catalog skills.
11. Rank those resources against open skill gaps (hybrid default, or a baseline).
12. Inspect skill prerequisites, teaching courses, practice projects, and mentors on Graph.
13. See a course → project pair for each major skill gap.
14. See mentors matched to those gaps, with overlap count, hours, and open slots.
15. See a topological learning path: missing foundations before the skills that need them.
16. Compare OR-Tools, greedy, and topological plans against weekly hours and a deadline.
17. See that path as a Learn first / Core / Later timeline with duration, difficulty, and why.
18. Take an MCQ; a new assessment evidence row updates proficiency, confidence, and gap.
19. Re-optimize the path after a quiz (weak score adds a refresher; strong score can skip basics).
20. Ask a grounded learning assistant about the stored path, gaps, and recommendations.
21. Compare catalog roles on coverage, missing skills, effort, projects, and mentors without changing the saved target.
22. Open Twin for current, required, gap, confidence, evidence, and stored trend per skill.
23. Managers and HR can see department or org aggregates without individual names.
24. Use a grouped navigation (You, Skills, Learn, Explore) instead of a long tab list.
25. Page catalog and assessment lists; rate-limited `/api/v1` returns a 429 envelope.
26. Use OpenAPI at `/docs`.
27. Run the automated learner pipeline and PRD latency checks.
28. Compare ranking methods on labeled synthetic sets (not real employees).

We **cannot** yet: collect GitHub repo evidence (Phase 20 skipped, still listed). GitHub is not required for profile, gaps, path, assistant, or what-if.

---

## Coverage snapshot

| Band | Phases | Status |
| --- | --- | --- |
| Done | 0–19, 21–27 | Complete |
| Skipped (listed) | 20 | GitHub evidence deferred; not removed |
| Unlocked next | 28 | Not started; no blockers |
| Blocked | 28 | Wait for prior phase |

Starter skill/role **catalog** exists (~32 skills, 10 target roles). That is inventory, not taxonomy.

---

## Phase 0 — Foundation — DONE

- [x] Repository layout (frontend, backend, ml, recommendation, knowledge_graph, optimization, llm, database, datasets, tests, docs, scripts)
- [x] Git init, README, `.gitignore`, `.env.example`, LICENSE, docker-compose
- [x] FastAPI + Python 3.11, `/health`, OpenAPI
- [x] React + TypeScript + Tailwind + React Query + Zustand
- [x] PostgreSQL 15 in Docker
- [x] pytest, Ruff, Black, mypy
- [x] Naming, `/api/v1`, error envelope, env-based config

---

## Phase 1 — Auth and employee profile — DONE

- [x] Users vs employees; roles EMPLOYEE / MANAGER / MENTOR / HR_ADMIN / SYSTEM_ADMIN
- [x] Register, login, refresh, logout, `/auth/me`
- [x] Password hashing, JWT, RBAC, ownership on `/employees/me`
- [x] Profile GET/PUT, completeness score
- [x] Education CRUD, experience CRUD
- [x] Employee skills CRUD from catalog; target role selection
- [x] Pages: `/login`, `/register`, `/dashboard`, `/profile`
- [x] Alembic `0001_phase1`
- [x] Auth / profile / validation tests (35 passing)

Not in Phase 1 (correctly deferred): resume upload, skill aliases, gap APIs, recommendation APIs.

---

## Phase 2 — Skill taxonomy — DONE

Goal: one canonical skill for `ML` / `Machine Learning` / `machine-learning`.

- [x] Add `aliases` and `difficulty` to the skill model (`skill_aliases`)
- [x] Keep `canonical_name` as the single display/normalization key
- [x] Seed aliases for the catalog (`ML`, `NLP`, `DL`, `K8s`, `Postgres`, case/punctuation variants)
- [x] Normalizer (lowercase, punctuation, camelCase, compact form)
- [x] Mapper: raw string → `{ skill_id, canonical_name, confidence }` or unmatched
- [x] `POST /api/v1/skills/resolve` and `GET /api/v1/skills?category=`
- [x] Taxonomy seed under `datasets/processed/skill_taxonomy.json`
- [x] Mapper in `ml/skill_extraction/`
- [x] Tests: alias collision, case, punctuation, unknown term, exact vs alias confidence
- [x] No resume parsing in this phase

Definition of done: every known mention maps to `skill_id` + `canonical_name` + mapping confidence.

---

## Phase 3 — Resume processing and skill extraction — DONE

- [x] PDF / DOCX / TXT upload and text extraction
- [x] Cleaning and section segmentation
- [x] Layer 1 dictionary match (taxonomy)
- [x] Layer 2 section context (spaCy NER model not required)
- [ ] Layer 3 semantic fallback (sentence transformers) — deferred
- [ ] Layer 4 optional LLM only for ambiguous cases — deferred
- [x] Write evidence snippets; never present inferred skills as facts
- [x] Labeled extraction test set; measure Precision / Recall / F1

---

## Phase 4 — Target roles and job descriptions — DONE

Depends on Phase 3 (extraction). Partial overlap already: role catalog + `role_skills` seed.

- [x] Role catalog list/detail (Phase 1)
- [x] Required level, importance, criticality on `role_skills` (Phase 1 seed)
- [x] Paste/upload JD
- [x] Extract required / preferred / mentioned skills
- [x] Configurable weights (required 1.0, preferred 0.6, mentioned 0.4)
- [x] Map JD skills through taxonomy

---

## Phase 5 — Evidence-based skill profiling — DONE

- [x] Evidence table (source_type, reliability, strength, recency, extracted_level)
- [x] Configurable source reliability (self-declaration 0.3)
- [x] Confidence `C(s) = 1 − Π(1 − r·σ·ρ)`
- [x] Proficiency `L_cur` weighted aggregation
- [x] Conflict flag when variance is high
- [x] UI: evidence list, confidence label, “inferred ≠ fact”

---

## Phase 6 — Skill-gap engine — DONE

- [x] `Gap_basic = max(0, L_req − L_cur)`
- [x] Enhanced `Gap = basic × I × C × R × E` with configurable weights
- [x] Priority bands (Critical / High / Medium / Low / None)
- [x] `GET /api/v1/gap-analysis`
- [x] Gap cards + current vs required (CSS bars; radar later)

---

## Phase 7 — Course, project, mentor datasets — DONE

- [x] Course / project / mentor tables (not hardcoded in rec functions)
- [x] Skill mappings and seed realistic catalogs
- [x] Keep data in `datasets/` + PostgreSQL

---

## Phase 8 — Baseline recommendation engine — DONE

- [x] Popularity
- [x] Content-based (cosine of gap vector vs resource vector)
- [x] Semantic (`all-MiniLM-L6-v2` intended; hashing default)
- [x] Persist component scores; compare later in evaluation

---

## Phase 9 — Neo4j knowledge graph — DONE

- [x] Nodes: Employee, Skill, Course, Project, Mentor, TargetRole, Assessment
- [x] Relationships from PRD (REQUIRES, PREREQUISITE_OF, TEACHES, …)
- [x] Prerequisite DAG + cycle detection
- [x] Queries: prereqs, courses teaching skill, mentors for gaps

---

## Phase 10 — Hybrid recommendation — DONE

- [x] Seven independent signals (semantic, gap, prerequisite, difficulty, preference, CF, KG)
- [x] Configurable weights; save per-component scores
- [x] Rank + machine-readable reason (no LLM as the engine)

---

## Phase 11 — Project recommendation — DONE

- [x] Rank projects by gap, difficulty, duration, technologies, target role
- [x] Course → project pairing for major gaps

---

## Phase 12 — Mentor recommendation — DONE

- [x] Match on skill overlap, domain, availability, workload
- [x] Deterministic “why this mentor” payload

---

## Phase 13 — Prerequisite-aware learning path — DONE

- [x] Expand prereqs for top gaps
- [x] Topological sort; `prerequisite_violation_count == 0`

---

## Phase 14 — OR-Tools path optimization — DONE

- [x] Constraints: prereqs, weekly hours, deadline, no duplicate resources
- [x] Compare greedy vs topological vs OR-Tools

---

## Phase 15 — Learning-path UI — DONE

- [x] Timeline (foundation → core → advanced)
- [x] Duration, skill, difficulty, status, why-this on each item

---

## Phase 16 — Assessment engine — DONE

- [x] MCQ then conceptual / coding / practical
- [x] Attempts add **new evidence**; do not overwrite history

---

## Phase 17 — Adaptive re-optimization — DONE

- [x] Assessment trigger: weak quiz adds refresher hours; strong quiz skips basics
- [x] Re-run the hour-budget optimizer after that change
- [ ] Course/project completion, GitHub, mentor feedback (no data yet; not faked)
- [x] Manual skill update already retriggers because GET `/learning-paths` rebuilds

---

## Phase 18 — Deterministic explainability — DONE

- [x] Reasons from stored scores/evidence only
- [x] Optional LLM verbalization after facts exist (join by default; no invented claims)

---

## Phase 19 — RAG learning assistant — DONE

- [x] Ground in profile, gaps, path, assessments
- [x] No invented employee data; no unnecessary PII to LLM APIs

---

## Phase 20 — GitHub evidence

Skipped for now (not removed). The app does not depend on GitHub
collection. `GITHUB` remains a configured evidence source with no
collector. A later session can add OAuth-scoped repo analysis.

- [ ] OAuth-scoped repo analysis → skill evidence with strength/confidence

---

## Phase 21 — What-if career simulation — DONE

- [x] Compare target roles: coverage, missing skills, effort
- [x] Hypothetical path skills, catalog projects, mentor overlap
- [x] Does not change the saved target role or stored path
- [x] No hiring/employment predictions

---

## Phase 22 — Skill digital twin — DONE

- [x] Per-skill current/required/gap/confidence/evidence/trend UI
- [x] Read-only snapshot; does not change the saved target or path
- [x] GitHub listed as a source and remains uncollected

---

## Phase 23 — Manager / HR analytics — DONE

- [x] Team heatmap and org aggregates
- [x] Privacy: no unnecessary individual exposure
- [x] Department is the team scope; no names, emails, or evidence text

---

## Phase 24 — Frontend polish — DONE

- [x] Remaining screens from PRD §26 are reachable from grouped nav
- [x] “Why?” on recommendations, practice, mentors, and path steps
- [x] Fewer top-level tabs; skip link and focus outlines

---

## Phase 25 — API hardening — DONE

- [x] Pagination, filtering, sorting on catalog and assessment lists
- [x] Rate limits with a consistent 429 envelope
- [x] HTTP errors use the Phase 1 `{ error: { code, message } }` shape

---

## Phase 26 — Testing expansion — DONE

- [x] Integration: resume → profile → gap → recs → path → assessment
- [x] End-to-end register → resume → role → gaps → recs → path → quiz → rebuild
- [x] Performance vs PRD p95 targets

---

## Phase 27 — Research evaluation — DONE

- [x] Five rec approaches + ablation
- [x] Precision@K, NDCG, F1, path violations
- [x] Synthetic data labeled as synthetic

---

## Phase 28 — Deployment and documentation

- [ ] Docker deployment, architecture/eval docs, demo scenario

---

## Rule for the next implementation session

Implement **only Phase 28**. Do not add GitHub evidence unless that phase is requested. Phase 20 stays on this roadmap as skipped.
