# Phase 4 API — roles and job descriptions

## Catalog role

`GET /api/v1/roles/{role_id}`

Returns the seeded competency profile. `importance` 1.00 is required, 0.60 is preferred. `requirement` is derived from those weights.

## Paste

`POST /api/v1/job-descriptions`

```json
{
  "title": "Senior ML Engineer",
  "text": "Requirements\nPython, Machine Learning\n"
}
```

Auth required.

## Upload

`POST /api/v1/job-descriptions/upload`

Multipart: `file` (PDF, DOCX, or TXT, max 5MB), optional `title`.

## List / detail

| Method | Path |
| --- | --- |
| GET | `/api/v1/job-descriptions` |
| GET | `/api/v1/job-descriptions/{id}` |

Unknown mentions are omitted. JD skills are **not** written onto the employee profile.

Weights are snapshotted on each analysis from `JD_WEIGHT_REQUIRED`, `JD_WEIGHT_PREFERRED`, and `JD_WEIGHT_MENTIONED`.
