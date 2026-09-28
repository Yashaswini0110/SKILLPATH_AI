# Phase 23 implementation report

## Current phase

Phase 23 — Manager / HR analytics

## Objective

Organizational aggregates after the learner flow. Respect privacy. Do
not invent employee seed data. Do not collect GitHub.

## PRD / playbook requirements implemented

- Team skill heatmap (level bands + missing)
- Top skill gaps and training priorities
- Learning progress (quizzes and stored paths)
- Role competency framework adoption
- Org skill/department distribution for HR
- No unnecessary individual exposure

Not implemented:

- GitHub evidence (Phase 20, deferred)
- Direct-report `manager_id` hierarchy
- Frontend polish (Phase 24)

## Files created or changed

- `backend/app/schemas/analytics.py`, `services/analytics_service.py`, `api/v1/analytics.py`
- `frontend/src/pages/AnalyticsPage.tsx`
- `docs/architecture/analytics.md`
- `docs/phases/roadmap.md`

## Tests

`tests/test_analytics.py`

## Known issues

Department matching is case-insensitive exact text. Empty department
blocks managers.

## Next phase

Phase 24 — Frontend polish.
