# Phase 14 implementation report

## Current phase

Phase 14 — OR-Tools path optimization

## Objective

Constrain the topological candidate path by weekly hours, a deadline,
and unique resources. Compare greedy vs topological vs OR-Tools. Do not
build the Phase 15 timeline.

## PRD / playbook requirements implemented

- Inputs: skill gaps, prerequisites, course/project durations, weekly
  hours, deadline
- Maximize gap coverage and progress; minimize hours
- Constraints: prereqs, weekly budget, deadline, no duplicate resources
- Output: ordered resources, week spans, estimated completion, coverage
- Comparison metrics: total time, coverage, violations, efficiency
- Assessments deferred (duration 0)

## Files created or changed

- `optimization/` greedy, CP-SAT, week packing, metrics
- `backend/app/services/path_service.py`
- `backend/app/api/v1/learning_paths.py` `method` and `deadline_weeks`
- `backend/alembic/versions/0012_phase14_optimize.py`
- `frontend/src/pages/PathPage.tsx`
- `docs/architecture/optimization.md`

## Tests

pytest 133 passed. ruff, black, mypy, frontend `tsc --noEmit`.

## Known issues

On a tight deadline OR-Tools may omit a late gap (for example RAG) to
stay inside the hour budget. Topological still returns the full chain.

## Next phase

Phase 15 — Learning-path UI.
