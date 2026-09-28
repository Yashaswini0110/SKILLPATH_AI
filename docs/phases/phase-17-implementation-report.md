# Phase 17 implementation report

## Current phase

Phase 17 — Adaptive re-optimization

## Objective

Make the path dynamic after an assessment. A weak score adds a refresher
and delays dependents. A strong score skips basics so later skills can
start sooner. Re-run the hour-budget optimizer. Do not use an LLM as
the recommendation engine.

## PRD / playbook requirements implemented

- Assessment result trigger
- Score below 55% → review hours, then re-optimize
- Score 90% or higher → skip the skill, then re-optimize
- Manual skill update already retriggers via GET `/learning-paths`

Not implemented (no data; not faked):

- Course completion
- Project completion
- New GitHub evidence
- Mentor feedback

## Files created or changed

- `recommendation/path/adapt.py`
- `backend/alembic/versions/0014_phase17_adapt.py`
- `backend/app/services/path_service.py`
- `backend/app/services/assessment_service.py`
- `frontend/src/pages/PathPage.tsx`
- `frontend/src/pages/AssessmentTakePage.tsx`

## Tests

pytest 155 passed. ruff, black, frontend `tsc --noEmit`.

## Known issues

A 100% quiz can also close the gap, so the skill may already be absent
before skip runs. Skip is still recorded on `adaptations`. Review hours
are extra duration on the same step, not a second unique course.

## Next phase

Phase 18 — Deterministic explainability.
