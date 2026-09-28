# Phase 10 complete

Stopped here. Phase 11 (project recommendation) is not started.

## What works

- Seven independent hybrid signals with configurable weights
- Default `HYBRID` ranking on courses, projects, and mentors
- Component scores and weights persisted on `recommendation_results`
- UI at `/recommendations` with Hybrid first, seven score bars, and reasons
- Phase 8 baselines still selectable

## Known limits

- Collaborative filtering is skill-set Jaccard; there is still no click log
- Results are ranked lists, not a course → project path
- Semantic still defaults to hashing embeddings

## Next

Phase 11 — Project recommendation. Do not start it until Phase 10 is accepted.
