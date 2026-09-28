# Phase 8 complete

Stopped here. Phase 9 (Neo4j knowledge graph) is not started.

## What works

- Popularity, content-based (cosine), and semantic baselines
- Candidate retrieval on top open skill gaps only
- Component scores persisted on `recommendation_results`
- `GET /api/v1/recommendations/courses|projects|mentors`
- UI at `/recommendations` with method picker, rank, scores, and reasons

## Known limits

- Popularity is a catalog proxy (no click log)
- Semantic defaults to hashing embeddings; MiniLM is opt-in
- Hybrid seven-signal ranking is not implemented
- Results are ranked lists, not a learning path

## Next

Phase 9 — Neo4j knowledge graph. Do not start it until Phase 8 is accepted.
