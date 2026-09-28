# Phase 11 implementation report

## Current phase

Phase 11 — Project recommendation

## Objective

Connect each major skill gap to hands-on practice by pairing a catalog
course with a catalog project. Do not generate a learning path or
assessment.

## PRD / playbook requirements implemented

- Skill → course → project pairing for Critical/High gaps
- Project ranking: skills addressed, gap priority, difficulty, current
  proficiency, duration, technologies, target role
- Deterministic reason
- Example path in catalog: RAG → Retrieval-Augmented Generation →
  Document Q&A System
- No mentor-only matching, path optimizer, or assessments

## Files created or changed

- `recommendation/projects/` signals and greedy pairing
- `backend/app/services/practice_service.py`
- `backend/app/api/v1/recommendations.py` `GET /practice-pairs`
- `backend/alembic/versions/0009_phase11_practice.py`
- `frontend/src/pages/PracticePage.tsx`
- `docs/architecture/recommendation.md`

## Tests

pytest 117 passed. ruff, black, mypy, frontend `tsc --noEmit`.

## Known issues

If two major gaps share the only strong RAG project, greedy unique
assignment gives Document Q&A System to the first gap (RAG) and a
different project to the next.

## Next phase

Phase 12 — Mentor recommendation.
