# Phase 6 API — skill-gap analysis

`GET /api/v1/gap-analysis`

Auth required. Compares the current skill profile to one target:

- `role_id` — a catalog role
- `job_description_id` — a job description owned by the employee
- neither — uses the employee’s `target_role_id`

Provide `role_id` or `job_description_id`, not both. If neither is set and the employee has no target role, the API returns 422.

Gaps are computed on the fly and are not stored.

```json
{
  "data": {
    "target": { "type": "ROLE", "id": "...", "title": "ML Engineer" },
    "gap_count": 5,
    "critical_count": 2,
    "high_count": 1,
    "medium_count": 1,
    "low_count": 1,
    "none_count": 1,
    "gaps": [
      {
        "skill": { "canonical_name": "Deep Learning" },
        "required_level": "4.0",
        "current_level": "0.0",
        "gap_basic": "4.0",
        "gap": "3.4",
        "priority": "CRITICAL",
        "importance": "1.00",
        "criticality": "0.85",
        "confidence": "1.00",
        "evidence_strength": "1.00",
        "requirement": "REQUIRED",
        "inferred_only": false,
        "conflict": false
      }
    ]
  }
}
```

Formulas:

```text
Gap_basic = max(0, L_req − L_cur)
Gap = Gap_basic × I × C × R × E × configurable weights
```

Priority bands (PRD):

```text
CRITICAL  Gap > 2.0
HIGH      1.0 < Gap ≤ 2.0
MEDIUM    0.5 < Gap ≤ 1.0
LOW       0 < Gap ≤ 0.5
NONE      Gap = 0
```

Missing required skills use `L_cur = 0`, `C = 1`, `E = 1` so they still rank. Using `C = 0` would hide them. Job descriptions have no separate criticality column; `R` uses the JD importance weight.
