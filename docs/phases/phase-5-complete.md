# Phase 5 complete

Stopped here. Phase 6 (skill-gap engine) is not started.

## What works

- Self-declared skills write `SELF` evidence
- Resume hits remain `RESUME` evidence
- `GET /api/v1/employees/me/skill-profile` aggregates `C(s)` and `L_cur(s)`
- Conflict flag when level variance is high
- UI at `/skills` with confidence labels; inferred ≠ fact
- Alembic `0005_phase5`

## Known limits

- GitHub, courses, assessments, projects, and certifications are configured but not collected yet
- This is not a comparison to a target role or JD

## Next

Phase 6 — Skill-gap engine. Do not start it until Phase 5 is accepted.
