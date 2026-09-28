# Phase 18 implementation report

## Current phase

Phase 18 — Deterministic explainability

## Objective

Every recommendation has an auditable reason from stored scores and
evidence. Do not use an LLM as the ranking engine. Optional
verbalization may only rephrase those facts.

## PRD / playbook requirements implemented

- Numbered facts: gap addressed, priority, similarity, prerequisites,
  difficulty, preference, rank
- Store score components, matched skills, gap, rank
- Why? in the UI
- Verbalization after facts exist (deterministic join)

Not implemented:

- RAG assistant (Phase 19)
- External LLM API calls

## Files created or changed

- `recommendation/explain.py`
- `llm/verbalize.py`
- `backend/alembic/versions/0015_phase18_explain.py`
- `frontend/src/components/common/WhyButton.tsx`
- recommendation, practice, mentor, and path services/schemas
- `docs/architecture/explainability.md`

## Tests

pytest 158 passed. ruff/black on Phase 18 files. frontend `tsc --noEmit`.
Browser: Why? on Recommend, Practice, Mentors, and Path shows numbered
stored facts (no invented “I think” copy; no solver-method labels).

## Known issues

An unused LLM rephrase flag still returns the fact paragraph. That is
intentional until a client is configured without sending extra PII.

## Next phase

Phase 19 — RAG learning assistant.
