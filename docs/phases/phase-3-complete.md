# Phase 3 complete

Stopped here. Phase 4 (job description analysis) is not started.

## What works

- Upload PDF, DOCX, or TXT
- Text extraction, section split, taxonomy dictionary match
- Inferred skills with snippet, confidence, and `inferred=true`
- Evidence rows stored separately from self-declared profile skills
- UI at `/resume`
- Labeled synthetic eval set; dictionary F1 ≥ 0.85 on that set
- Alembic `0003_phase3`

## Known limits

- No spaCy NER model and no sentence-transformers in the decision path
- No LLM fallback
- Starter catalog only; terms outside it stay unmatched
- Proficiency from resume wording is a hint, not ground truth

## Next

Phase 4 — Target role / job description analysis using this extractor.
