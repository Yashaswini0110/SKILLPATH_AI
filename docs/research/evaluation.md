# Research evaluation (Phase 27)

This is an **offline** comparison on **synthetic, labeled** sets. It does
not claim to measure real employee behavior.

The LLM is not the ranking engine. Hybrid scores come from the same seven
signals used in production.

## Data

All files under `datasets/synthetic/` set `"synthetic": true`.

| Set | Purpose |
| --- | --- |
| `recommendation_eval.json` | Relevant catalog courses per gap profile |
| `gap_ranking_eval.json` | Graded relevance for gap order |
| `path_eval.json` | Missing-skill DAGs for path metrics |
| `resume_extraction_eval.json` | Gold skill names for extraction F1 |

The course catalog is also labeled synthetic.

## Recommendation compare

Methods: Popularity, Content, Semantic, Knowledge graph, Hybrid.

Metrics @5: Precision, Recall, NDCG, MAP, catalog coverage, intra-list
skill diversity.

On this small labeled set, popularity can outrank hybrid when the
relevant courses already have high catalog ratings. That is reported,
not hidden.

Run:

```text
python scripts/run_evaluation.py
```

Results: `docs/research/evaluation-results.md`.

## Ablation

Hybrid is rerun with one weight set to 0 at a time. Δ NDCG@5 is vs the
full model. A near-zero delta on this small set means the signal did not
change top-5 on these three queries — not that the signal is useless.

## Other measures

- Extraction: Precision / Recall / F1 (PRD target F1 ≥ 0.85)
- Gap ranking: NDCG@10 vs graded labels
- Path: prerequisite violations, skill coverage, hours, efficiency
  (`coverage / weeks` at 10 hours/week)

## Explainability

Automated faithfulness checks that Why? facts stay on stored scores.
A user study protocol is in `docs/research/explainability-protocol.md`.
No user-study scores are invented here.
