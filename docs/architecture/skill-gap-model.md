# Skill-gap model

Phase 6 ranks the difference between the current skill profile and a target competency profile.

## Inputs

- Current profile from Phase 5: `L_cur(s)`, `C(s)`, evidence strength
- Target from Phase 4: catalog `role_skills` or analyzed job-description skills

## Formulas

```text
Gap_basic(s) = max(0, L_required(s) − L_current(s))

Gap(s) =
  Gap_basic(s)
  × I(s)    importance
  × C(s)    confidence
  × R(s)    criticality
  × E(s)    evidence strength
  × extra weights (default 1.0)
```

`I`, `C`, `R`, and `E` are clamped to `[0, 1]` before the extra weights are applied.

## Priority bands

```text
NONE     Gap = 0
LOW      0 < Gap ≤ 0.5
MEDIUM   0.5 < Gap ≤ 1.0
HIGH     1.0 < Gap ≤ 2.0
CRITICAL Gap > 2.0
```

Thresholds are configurable (`GAP_CRITICAL_THRESHOLD`, `GAP_HIGH_THRESHOLD`, `GAP_MEDIUM_THRESHOLD`).

## Missing skills

If the employee has no evidence for a required skill, `L_cur = 0`. Confidence and evidence strength are set to 1.0 for that row so the skill is not zeroed out of the ranking.

## Job descriptions

JD rows have importance but no separate criticality column. `R(s)` uses the same value as `I(s)`.

## What this is not

This model does not recommend courses, projects, or mentors. It does not persist gap rows. Ranking metrics such as NDCG@10 are deferred to evaluation.
