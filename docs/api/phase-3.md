# Phase 3 API — resume extraction

## Upload

`POST /api/v1/employees/me/resumes`

Multipart form field: `file` (PDF, DOCX, or TXT, max 5MB). Auth required.

Response includes inferred skills. They are **not** written onto the self-declared profile.

```json
{
  "data": {
    "id": "...",
    "original_filename": "resume.txt",
    "status": "processed",
    "skill_count": 8,
    "skills": [
      {
        "skill": { "canonical_name": "Machine Learning" },
        "extracted_level": 3.5,
        "confidence": 0.81,
        "inferred": true,
        "source_type": "RESUME",
        "evidence_snippet": "Skills Python, SQL, Machine Learning",
        "section": "skills",
        "match_type": "exact"
      }
    ]
  },
  "message": "Resume processed. Extracted skills are inferred, not verified facts."
}
```

## List / detail

| Method | Path |
| --- | --- |
| GET | `/api/v1/employees/me/resumes` |
| GET | `/api/v1/employees/me/resumes/{resume_id}` |

Unknown mentions are omitted. The extractor does not invent catalog skills.
