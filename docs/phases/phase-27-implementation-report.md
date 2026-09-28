# Phase 27 implementation report

## Current phase

Phase 27 — Research evaluation

## Objective

Compare recommendation approaches and report PRD metrics on synthetic
labels. Do not change hybrid ranking weights. Do not add GitHub.

## PRD / playbook requirements implemented

- Popularity, content, semantic, KG, hybrid
- Precision@K, Recall@K, NDCG@K, MAP@K, coverage, diversity
- Extraction Precision / Recall / F1
- Gap ranking NDCG@10
- Path violations, coverage, time, efficiency
- Ablation of seven hybrid signals
- User-study protocol (not executed)
- Synthetic data labeled as synthetic

## Files created or changed

- `ml/evaluation/`
- `datasets/synthetic/recommendation_eval.json`
- `datasets/synthetic/gap_ranking_eval.json`
- `datasets/synthetic/path_eval.json`
- `scripts/run_evaluation.py`
- `docs/research/evaluation.md`
- `backend/app/services/recommendation_service.py` (KG method)
- `frontend/src/pages/RecommendationsPage.tsx`

## Known issues

The labeled set is small. Ablation deltas can be zero. Results must not
be reported as real-world employee performance.

## Next phase

Phase 28 — Deployment and documentation. Do not start it until Phase 27
is accepted.
