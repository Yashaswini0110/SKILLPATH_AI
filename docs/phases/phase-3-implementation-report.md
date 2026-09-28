# Phase 3 implementation report

## Current phase

Phase 3 — Resume processing and skill extraction

## Objective

Turn an uploaded resume into structured, inferred skill evidence using the Phase 2 taxonomy.

## PRD / playbook requirements implemented

- PDF / DOCX / TXT text extraction
- Cleaning and section segmentation
- Layer 1 dictionary match through the taxonomy
- Layer 2 section context for confidence (not a spaCy model)
- Evidence snippets; inferred ≠ fact
- Labeled synthetic test set with Precision / Recall / F1
- Do not overwrite self-declared employee skills

## Files created or changed

- `ml/skill_extraction/text_extraction.py`, `segmenter.py`, `dictionary_extractor.py`, `proficiency.py`, `pipeline.py`
- `backend/app/models/resume.py`, `evidence.py`
- `backend/alembic/versions/0003_phase3_resume.py`
- `backend/app/services/resume_service.py`, `api/v1/resumes.py`
- `frontend/src/pages/ResumePage.tsx`
- `datasets/synthetic/sample_resume.txt`, `resume_extraction_eval.json`

## Tests

59 pytest passed. ruff, black, mypy, frontend `tsc --noEmit`.

## Known issues

spaCy and MiniLM are documented stubs/deferrals. Ambiguous English words such as "react" are filtered outside skills sections.

## Next phase

Phase 4 — Target roles and job descriptions.
