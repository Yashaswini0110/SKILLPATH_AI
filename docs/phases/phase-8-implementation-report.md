# Phase 8 implementation report

## Current phase

Phase 8 — Baseline recommendation engine

## Objective

Rank catalog courses, projects, and mentors against open skill gaps using
three independent research baselines, and persist per-component scores.

## PRD / playbook requirements implemented

- Popularity baseline (catalog proxy: rating / years / skill coverage)
- Content-based cosine of gap vector vs resource skill vector
- Semantic cosine; intended model `all-MiniLM-L6-v2`, default hashing encoder
- Candidate retrieval limited to resources teaching top open gaps
- Persist rank, score, components, matched skills, deterministic reason
- APIs for courses, projects, and mentors
- UI ranked list with method, scores, and why-this text
- LLM is not the recommendation engine
- No hybrid ranking, Neo4j, or path generation

## Files created or changed

- `recommendation/baselines/` (vectors, popularity, content, semantic)
- `backend/app/models/recommendation.py`
- `backend/alembic/versions/0007_phase8_recommendations.py`
- `backend/app/services/recommendation_service.py`
- `backend/app/api/v1/recommendations.py`
- `frontend/src/pages/RecommendationsPage.tsx`
- `docs/architecture/recommendation.md`

## Tests

pytest 100 passed. ruff, black, mypy, frontend `tsc --noEmit`. Alembic `0007_phase8`.

## Known issues

Popularity has no interaction log. Semantic MiniLM is opt-in via
`REC_SEMANTIC_BACKEND=minilm`.

## Next phase

Phase 9 — Neo4j knowledge graph.
