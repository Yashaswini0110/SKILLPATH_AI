# Recommendation engine

Phase 8 implements three independent baselines:

1. Popularity — catalog rating / experience proxy (no click log yet)
2. Content-based — cosine similarity of gap vector vs resource skill vector
3. Semantic — embedding cosine; intended model `all-MiniLM-L6-v2`

Candidate retrieval only scores resources that teach at least one **open**
top skill gap. Component scores are persisted on each recommendation row.

Hybrid seven-signal ranking is not implemented yet.
