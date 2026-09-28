# Recommendation ranking (Phase 8 + 10)

Catalog resources are ranked against **open** skill gaps. Baselines remain
available. Hybrid is the default. The LLM is not used as the ranking engine.

## Candidate retrieval

1. Run gap analysis for the employee’s target role or job description.
2. Keep the top `REC_TOP_GAP_COUNT` gaps with priority other than `NONE`.
3. Score only courses / projects / mentors that teach at least one of those skills.

## Baselines (Phase 8)

### Popularity

No click log exists yet. Catalog proxy in `[0, 1]`:

- course: `rating / 5`
- mentor: `years_experience / 15` (capped)
- project: `skill_count / 6` (capped)

### Content-based / skill-gap relevance

```text
gap_vector[s]      = Gap(s) for each top open gap
resource_vector[s] = taught_level(s) / 5
score              = cosine(gap_vector, resource_vector)
```

### Semantic

```text
score = cosine(embed(gap_summary), embed(title + description + skills))
```

Intended encoder: Sentence Transformers `all-MiniLM-L6-v2`. Default runtime
encoder is a stable hashing bag-of-words (`REC_SEMANTIC_BACKEND=hashing`) so
tests and offline machines do not download Torch. Set
`REC_SEMANTIC_BACKEND=minilm` after `pip install sentence-transformers`.

## Hybrid (Phase 10)

Seven independent signals, then a weighted mean:

```text
Score = Σ w_i s_i / Σ w_i
```

| Signal | Meaning |
| --- | --- |
| semantic | embedding cosine of gap summary vs resource text |
| gap | same cosine as the content baseline |
| prerequisite | fraction of immediate DAG parents of taught gap skills that are *not* still open gaps (1.0 if no parents) |
| difficulty | `1 − \|resource_difficulty − learner_level\| / 4` |
| preference | course `format` vs `learning_preferences.formats`; projects map to hands-on; mentors to live/hands-on |
| collaborative | Jaccard of the employee’s declared skill ids vs the resource’s skill ids (cold-start proxy; no click log) |
| kg | max over taught skills: 1.0 if a top gap, 0.75 if an ancestor of a top gap, 0.4 if related/complement |

Weights `REC_W_SEMANTIC`, `REC_W_GAP`, `REC_W_PREREQUISITE`, `REC_W_DIFFICULTY`,
`REC_W_PREFERENCE`, `REC_W_COLLABORATIVE`, `REC_W_KG` default to 1.0.

Prerequisite and KG signals read the same DAG as Neo4j
(`datasets/processed/skill_prerequisites.json`). They do not call the LLM.

## Persistence

Each request writes a `recommendation_results` batch with rank, final score,
JSON component scores, matched gap skills, and a deterministic reason string.

Hybrid rows store `semantic`, `gap`, `prerequisite`, `difficulty`, `preference`,
`collaborative`, `kg`, `final`, plus `popularity`, `content`, and `weights`.

Phase 18 adds `explanation.facts` and `explanation.verbalization` from those
stored values. See `docs/architecture/explainability.md`.

## APIs

```text
GET /api/v1/recommendations/courses
GET /api/v1/recommendations/projects
GET /api/v1/recommendations/mentors
```

Query: `method=HYBRID|CONTENT|POPULARITY|SEMANTIC|KG` (default `HYBRID`),
optional `role_id` or `job_description_id`, `limit` 1–50.

`KG` uses only the knowledge-graph signal (gap / ancestor / related).
It is a research baseline, not the default ranker. See
`docs/research/evaluation.md`.

## Practice pairs (Phase 11)

For each **major** gap (Critical / High; Medium if none), pick one catalog
course then one project that both teach that skill:

```text
Skill gap  →  course  →  project
```

Example: RAG → Retrieval-Augmented Generation → Document Q&A System.

Project ranking (weighted mean, weights `REC_P_*`):

- skills addressed (taught level / 5)
- gap priority
- difficulty vs current level
- proficiency stretch (prefer about +1 level)
- duration vs weekly hours
- technologies vs known skill names
- overlap with the target role skill set

Courses are chosen among those that teach the same skill, preferring
`course.difficulty <= project.difficulty`. Each course and project is used
at most once per batch. Assessments and ordered learning paths are not in
this phase.

```text
GET /api/v1/recommendations/practice-pairs
```

Persists `practice_pairings` with rank, score, JSON components, and reason.

## Mentor matches (Phase 12)

Dedicated matching, separate from the hybrid mentor list. Signals (weights
`REC_M_*`):

- skill overlap with the top open gaps
- domain overlap with the target role category
- experience (`years / 15`)
- availability (`hours per month / 12`)
- learning goals (role-skill coverage plus live/hands-on preference)
- workload (open mentee slots / `max_mentees`; no assignment log yet)

The `why` payload is machine-readable:

```text
matched_gap_count, top_gap_count, matched_skills,
available_hours_per_month, open_mentee_slots, domains
```

Example: Sara Chen for a GenAI Engineer — 4 of 5 top gaps (RAG, LLMs,
Vector Databases, Prompt Engineering), 10 hours/month, 4 open slots.

```text
GET /api/v1/recommendations/mentor-matches
```

Persists `mentor_matches`. This is still a ranked match list, not a path.

## Learning path (Phase 13)

Take the top open gaps, expand every ancestor in
`datasets/processed/skill_prerequisites.json`, drop skills the learner
already has, then Kahn-sort the rest.

```text
Statistics → Machine Learning → Deep Learning → Transformers → LLMs → RAG
```

`prerequisite_violation_count` counts DAG edges whose source appears at
or after the destination in the path. It must be `0`. Known foundations
are omitted rather than reordered.

Each step maps at most one unused catalog course and project.

Query `method=ORTOOLS|GREEDY|TOPOLOGICAL` (default `ORTOOLS`) and
optional `deadline_weeks`. Weekly hours come from the employee profile.

## Path optimization (Phase 14)

OR-Tools CP-SAT selects a subset of the topological candidate list:

- If skill B is selected, every still-missing prerequisite A is selected
- Sum of course + project hours <= `hours_per_week * deadline_weeks`
- Resources stay unique from the Phase 13 mapper
- Assessments are duration 0 (not generated yet)

Greedy walks the same order and stops when the next skill does not fit.
Topological keeps every missing skill and may exceed the hour budget
(`hours_violation_count`).

The response includes a comparison of total hours, estimated weeks,
skill coverage, prerequisite violations, hour violations, and path
efficiency (`coverage / weeks`).

Each selected step also gets a **stage** from depth in the selected DAG:

- `FOUNDATION` — depth 0 (Learn first)
- `ADVANCED` — the deepest skills when selected depth ≥ 2 (Later)
- `CORE` — everything in between

A lone foundation-kind skill with no selected parents stays `FOUNDATION`.
`kind=FOUNDATION` on a deeper ancestor does not pull it into Learn first.
If the selected DAG is only one hop deep, an independent skill that the
sort placed after Core is tagged `ADVANCED` so the timeline does not
repeat Learn first.

Status is `NOT_STARTED` until a quiz is attempted, then `IN_PROGRESS`
or `COMPLETED` from the latest attempt. After a quiz, GET `/learning-paths`
adapts the candidate list (review hours or skip) and re-runs the
hour-budget optimizer.

See `docs/architecture/assessment.md`.

```text
GET /api/v1/learning-paths
```

Persists `learning_paths` and `learning_path_steps` with week spans.
Stage, status, and difficulty are stored on each step's `why` JSON.




