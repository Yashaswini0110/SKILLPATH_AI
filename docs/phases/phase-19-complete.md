# Phase 19 complete

Stopped here. Phase 20 (GitHub evidence) is not started.

## What works

- Answers are plain sentences from stored facts, not raw catalog dumps
- Unavailable when the passages do not contain the answer
- Optional NIM rephrase (`openai/gpt-oss-20b`) when a key is set; otherwise stored facts only
- Chat UI on /assistant with source labels

## Known limits

- No external LLM call unless LLM_ENABLED and LLM_API_KEY are set
- NIM rephrase is discarded if it drifts from retrieved facts
- Does not rebuild the path; it reads the last stored path
- GitHub evidence is not a source

## Next

Phase 21 — what-if comparison (Phase 20 GitHub skipped, still listed on the roadmap).
