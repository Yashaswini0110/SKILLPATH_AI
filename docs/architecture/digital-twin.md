# Skill digital twin (Phase 22)

A read-only per-skill view of competency state.

```text
Stored skill profile + target role requirements
        ↓
Current, required, gap, confidence, evidence, trend
```

`GET /api/v1/twin` joins the existing profile and gap services and the
persisted `evidence` timestamps. It does not change the saved target or
path.

Trend uses stored evidence only:

- fewer than two evidence rows → `INSUFFICIENT_DATA`
- last level minus first ≥ 0.5 → `IMPROVING`
- first minus last ≥ 0.5 → `DECLINING`
- otherwise `STABLE`

GitHub is listed as a source type and stays absent until Phase 20 is
built. This is not a hiring or employment prediction.
