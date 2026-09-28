# Datasets

Keep evaluation data separate from application seed data.

- `raw/` — public catalogs (ESCO, O*NET, course metadata)
- `processed/` — normalized taxonomies
- `synthetic/` — labeled synthetic profiles; must be marked synthetic in research writing

Phase 3 adds labeled synthetic resumes in `datasets/synthetic/` for extraction evaluation.
Phase 4 adds `sample_jd.txt` for job-description requirement classification.
Phase 7 adds `processed/resource_catalog.json` (synthetic courses, projects, mentors).
Phase 9 adds `processed/skill_prerequisites.json` (directed DAG over taxonomy names).
Mark them as synthetic in any research write-up.
