# Testing (Phase 26)

Unit coverage already lives under `backend/tests/` from earlier phases.
This phase adds the playbook pipeline and PRD latency checks.

## Unit map

| Playbook topic | Tests |
| --- | --- |
| Skill normalization | `test_normalizer.py`, `test_taxonomy_mapper.py` |
| Gap calculation | `test_gap_engine.py`, `test_gap_analysis.py` |
| Evidence / confidence | `test_evidence_aggregation.py`, `test_skill_profile.py` |
| Recommendation signals | `test_hybrid_signals.py`, `test_recommendation_baselines.py` |
| Graph traversal | `test_graph.py` |
| Topological sort | `test_learning_path.py` |
| Optimization constraints | `test_optimization.py`, `test_path_optimize.py` |

## Integration hops

`backend/tests/test_pipeline_integration.py`

```text
Resume → skill profile
Skill profile → gap
Gap → recommendations
Recommendations → path
Assessment → profile update
Profile update → re-optimize
```

## End-to-end

`backend/tests/test_pipeline_e2e.py`

```text
Register → resume → ML Engineer → gaps → courses → path → quiz → rebuilt path
```

Uses the synthetic sample resume. GitHub is not part of the flow.

## Performance (PRD)

`backend/tests/test_performance.py`

| Target | Limit |
| --- | --- |
| Catalog list p95 | < 500 ms |
| Skill extraction | < 10 s |
| Gap analysis | < 2 s |
| Recommendation | < 1 s |
| Path generation | < 3 s |
| Page load | < 2 s if `FRONTEND_URL` (default `http://localhost:5173/`) is up |

API timings use the in-process TestClient after a warmup request.
Page load is skipped when the frontend is not running.

```text
cd backend
.\.venv\Scripts\python -m pytest -m "integration or e2e or performance"
```
