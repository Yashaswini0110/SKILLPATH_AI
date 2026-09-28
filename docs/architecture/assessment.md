# Assessments (Phase 16)

MCQ quizzes live in `datasets/processed/assessments.json` and are seeded
into PostgreSQL. Scoring is deterministic:

```text
percent = correct / total
extracted_level = 1 + 4 × percent
passed = percent ≥ pass_score (default 0.70)
```

Each attempt inserts a **new** `evidence` row with `source_type=ASSESSMENT`
and `source_id=attempt_id`. Self-declared and resume rows stay.

```text
GET  /api/v1/assessments
GET  /api/v1/assessments/{id}
POST /api/v1/assessments/{id}/attempts
```

GET does not return `correct_index`. Submit returns `path_effect`:
`REFRESHER` below 55%, `SKIP` at 90% or higher, otherwise null. The
next path GET applies that effect and re-runs the hour-budget plan.
