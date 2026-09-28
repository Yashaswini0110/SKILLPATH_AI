# Phase 6 complete

Stopped here. Phase 7 (course, project, and mentor datasets) is not started.

## What works

- `Gap_basic = max(0, L_req − L_cur)`
- Enhanced `Gap = basic × I × C × R × E` with configurable extra weights (default 1.0)
- PRD priority bands Critical / High / Medium / Low / None
- `GET /api/v1/gap-analysis` against a catalog role or an owned job description
- UI at `/gaps` with priority cards and current vs required bars

## Known limits

- Gaps are not persisted
- Radar chart is deferred (CSS bars only; recharts is not in the frontend stack)
- Course / project / mentor recommendations are not implemented
- Job-description criticality reuses importance

## Next

Phase 7 — Course, project, and mentor datasets. Do not start it until Phase 6 is accepted.
