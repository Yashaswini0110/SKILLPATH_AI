# Phase 22 complete

GitHub (Phase 20) remains skipped, still listed on the roadmap.

## What works

- Open Twin (`/twin`) for a per-skill table: current, required, gap,
  confidence, evidence sources, and stored trend
- `GET /api/v1/twin` is read-only; saved target and path are unchanged
- GitHub is shown as not collected
- Disclaimer: not a hiring or employment prediction

## Known limits

- Self-declaration is upserted, so it is one history point, not a series
- Trend needs at least two stored evidence rows (for example a declared
  skill then a quiz)
- Extra sources (course, project, cert, work) have no collectors yet

## Next

Phase 23 — Manager / HR analytics. Do not start it until Phase 22 is
accepted. Do not add GitHub unless asked.
