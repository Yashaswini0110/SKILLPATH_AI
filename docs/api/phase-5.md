# Phase 5 API — skill profile

## Aggregated profile

`GET /api/v1/employees/me/skill-profile`

Auth required. Combines `SELF` and `RESUME` evidence. Does not compute gaps.

```json
{
  "data": {
    "skill_count": 8,
    "conflict_count": 1,
    "skills": [
      {
        "skill": { "canonical_name": "Python" },
        "current_level": 3.2,
        "confidence": 0.55,
        "confidence_label": "MEDIUM",
        "conflict": true,
        "recommend_assessment": true,
        "inferred_only": false,
        "evidence": [
          { "source_type": "SELF", "extracted_level": 4.0, "inferred": false },
          { "source_type": "RESUME", "extracted_level": 3.5, "inferred": true }
        ]
      }
    ]
  }
}
```

Formulas:

```text
w = reliability × strength × recency
C(s) = 1 − Π(1 − w)
L_cur(s) = Σ(w × level) / Σ(w)
```

Self-declaration reliability defaults to 0.3. Resume reliability defaults to 0.6. Both are configurable.
