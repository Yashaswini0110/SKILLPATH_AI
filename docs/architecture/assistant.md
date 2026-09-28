# Grounded learning assistant (Phase 19)

The assistant answers from **retrieved** employee and catalog passages.
It is not the recommendation engine.

```text
User question
    ↓
Retrieve: profile, gaps, path, quizzes, stored ranks, catalog
    ↓
Grounded answer from those passages
    ↓
Optional LLM rephrase (off by default)
```

It knows only what is already stored: current skill estimates, target
role, open gaps, the latest path, quiz percents, ranked resources, and
catalog descriptions.

Answers are plain sentences built from stored facts (role, gaps, path
steps, catalog descriptions, ranking reasons). They are not raw chunk
dumps. Path questions such as “what is my learning path for now?” read
the stored path, not the course catalog.

Optional LLM rephrase is off by default. When `LLM_ENABLED=true` and
`LLM_API_KEY` (or `NVIDIA_API_KEY`) is set, `openai/gpt-oss-20b` on
NVIDIA NIM may rewrite the draft using only the retrieved passages.
If the rewrite adds tokens that are not in those passages, the stored-fact
answer is kept. Email and resume text are never sent.

If a fact is missing it says so. It does not invent employee data.
Email, resume text, and other extra PII are not sent to an external
API. GitHub evidence is a later phase.

`POST /api/v1/assistant/ask` persists the turn. `GET /api/v1/assistant/turns`
returns recent questions for that employee.
