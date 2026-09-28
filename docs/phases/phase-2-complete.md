# Phase 2 complete

Stopped here. Phase 3 (resume processing) is not started.

## What works

- Skill model has `canonical_name`, `difficulty` (1–5), and `skill_aliases`
- Seed taxonomy in `datasets/processed/skill_taxonomy.json`
- Normalizer: lowercase, camelCase split, punctuation, compact form
- Mapper: raw mention → `skill_id` + `canonical_name` + confidence, or unmatched
- `GET /api/v1/skills?category=`
- `POST /api/v1/skills/resolve`
- Profile UI shows canonical names/aliases and a mention lookup
- Alembic `0002_phase2`

## Known limits

- Dictionary mapping only. No embeddings, spaCy, or LLM fallback.
- Practical starter taxonomy (~32 skills), not ESCO/O*NET scale.
- Self-declared employee skills are still not verified evidence.

## Next

Phase 3 — Resume processing and skill extraction, using this mapper as Layer 1.
