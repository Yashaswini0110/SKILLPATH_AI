# Path optimization (Phase 14)

The Phase 13 topological sequence is the candidate list. Phase 14
selects a subset that respects hours and uniqueness.

## Methods

| Method | Behavior |
| --- | --- |
| `TOPOLOGICAL` | Keep every missing skill. May exceed the hour budget. |
| `GREEDY` | Walk that order; skip a skill if it or its remaining prereqs do not fit. |
| `ORTOOLS` | CP-SAT: maximize gap coverage, then minimize hours, subject to prereqs and `hours_per_week * deadline_weeks`. |

Assessments are not generated; their duration is 0 until a weak quiz
adds review hours (Phase 17).

## Adaptive rebuild (Phase 17)

Latest quiz percents run through `recommendation/path/adapt.py` before
greedy / topological / OR-Tools:

- below 55%: keep the skill, set `kind=REFRESHER`, add
  `max(4, duration // 2)` hours, then re-optimize
- 90% or higher: drop the skill from the candidate list, then re-optimize
- 55%–89%: no skip or review; evidence still updates the profile

`learning_paths.adaptations` stores the skip/review notes. Course or
project completion, GitHub, and mentor feedback are not triggers yet.

## Metrics

- total hours
- estimated weeks (`ceil(hours / weekly)`)
- skill coverage (selected top gaps / top gaps)
- `prerequisite_violation_count`
- `hours_violation_count` (1 if over capacity)
- `duplicate_resource_count`
- path efficiency (`coverage / weeks`)

## API

```text
GET /api/v1/learning-paths?method=ORTOOLS&deadline_weeks=12
```

Default method is `ORTOOLS`. Weekly hours come from the employee
profile. See `docs/architecture/recommendation.md`.
