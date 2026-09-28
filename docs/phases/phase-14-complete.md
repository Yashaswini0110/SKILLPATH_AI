# Phase 14 complete

Stopped here. Phase 15 (learning-path UI timeline) is not started.

## What works

- OR-Tools CP-SAT subset under weekly hours and a deadline
- Greedy and topological baselines in the same response
- Unique resources, `prerequisite_violation_count == 0` on feasible methods
- UI at `/path` with method switch and week spans
- `GET /api/v1/learning-paths?method=ORTOOLS|GREEDY|TOPOLOGICAL`

## Known limits

- Assessments are duration 0 and not generated
- The Path page is not the foundation/core/advanced timeline
- Deadline is a query/config value, not a separate profile field

## Next

Phase 15 — Learning-path UI. Do not start it until Phase 14 is accepted.
