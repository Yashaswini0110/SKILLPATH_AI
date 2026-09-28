# Machine learning

This package holds skill extraction, embeddings, evidence aggregation, and gap scoring.

**Phase 2:** `normalizer.py` and `taxonomy_mapper.py`.

**Phase 5:** evidence aggregation in `evidence/aggregation.py`.

**Phase 6:** skill-gap scoring in `gap/engine.py`.

```text
Resume → text → sections → taxonomy dictionary → inferred skills + snippets
JD     → text → sections → taxonomy dictionary → required/preferred/mentioned
Evidence → C(s) = 1 − Π(1 − r·σ·ρ) and L_cur weighted average
Gap    → max(0, L_req − L_cur) × I × C × R × E
```

Extracted skills are always `inferred=true`. The pipeline does not invent skills
outside the catalog. spaCy NER, sentence-transformers, and LLM fallback are not
the decision engine in this phase.

Still later:

- `embeddings/` — sentence-transformer encoders
