# Phase 6 implementation report

## Current phase

Phase 6 — Skill-gap engine

## Objective

Rank competency gaps between the current skill profile and a catalog role or job description.

## PRD / playbook requirements implemented

- `Gap_basic = max(0, L_req − L_cur)`
- Enhanced `Gap = basic × I × C × R × E` with extra weights defaulting to 1.0
- Priority bands Critical / High / Medium / Low / None
- `GET /api/v1/gap-analysis`
- Gap cards, priority list, current vs required bars, confidence on each card
- Configurable weights and thresholds
- LLM is not used as a recommendation engine
- No course, project, or mentor recommendations

## Files created or changed

- `ml/gap/engine.py`
- `backend/app/services/gap_service.py`, `api/v1/gap.py`, `schemas/gap.py`
- `backend/app/core/config.py` gap weights and thresholds
- `frontend/src/pages/GapsPage.tsx`
- `backend/tests/test_gap_engine.py`, `backend/tests/test_gap_analysis.py`

## Tests

88 pytest passed. ruff, black, mypy, frontend `tsc --noEmit`.

## Known issues

Missing current skills are treated as level 0 with C=1 and E=1 so required skills still rank. Radar chart deferred. No Alembic migration (gaps are computed, not stored).

## Next phase

Phase 7 — Course, project, and mentor datasets.
