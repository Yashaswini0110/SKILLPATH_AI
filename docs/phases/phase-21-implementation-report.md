# Phase 21 implementation report

## Current phase

Phase 21 — What-if career simulation

## Objective

Compare catalog roles using the current skill profile. Do not predict
hiring. Do not change the saved target or path. GitHub is not required.

## PRD / playbook requirements implemented

- Skill coverage and missing skills per role
- Estimated effort and a hypothetical path sequence
- Required catalog projects and mentor overlap
- No employment predictions

Not implemented:

- GitHub evidence (Phase 20, deferred on the roadmap)
- Skill digital twin (Phase 22)

## Files created or changed

- `backend/app/schemas/whatif.py`, `services/whatif_service.py`, `api/v1/whatif.py`
- `frontend/src/pages/WhatIfPage.tsx`
- `docs/architecture/what-if.md`
- `docs/phases/roadmap.md` (Phase 20 stays listed as skipped)

## Tests

`tests/test_whatif.py` plus lint on Phase 21 files.

## Known issues

Hypothetical paths are not persisted. Open Compare to recompute.

## Next phase

Phase 22 — Skill digital twin.
