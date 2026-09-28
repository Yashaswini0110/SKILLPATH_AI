# Phase 15 complete

Stopped here. Phase 16 (assessment engine) is not started.

## What works

- Path steps are staged as FOUNDATION / CORE / ADVANCED from selected-path depth
- `/path` shows Learn first / Core / Later with duration, difficulty, Not started, and why
- Hour summary and full-list toggle stay; solver names stay off the page
- `GET /api/v1/learning-paths` includes `stage`, `status`, and `difficulty` on each step

## Known limits

- Status is always Not started
- Assessments are not generated
- Stage grouping follows depth in the selected DAG, not a hardcoded ML curriculum

## Next

Phase 16 — Assessment engine. Do not start it until Phase 15 is accepted.
