# Phase 2 API — skill taxonomy

Phase 1 routes are unchanged. This page covers taxonomy additions.

## Skills catalog

`GET /api/v1/skills`

Optional query: `category` (for example `GenAI`, `DevOps`).

Each skill now includes:

```json
{
  "id": "...",
  "name": "NLP",
  "canonical_name": "Natural Language Processing",
  "category": "NLP",
  "description": "Natural language processing.",
  "difficulty": 4,
  "aliases": ["nlp", "natural language processing"]
}
```

`name` is the stable catalog key (used for seed IDs). `canonical_name` is the normalization key.

## Resolve mentions

`POST /api/v1/skills/resolve`

Auth required.

```json
{ "mentions": ["ML", "machine-learning", "K8s", "quantum knitting"] }
```

```json
{
  "data": {
    "results": [
      {
        "raw": "ML",
        "skill_id": "...",
        "canonical_name": "Machine Learning",
        "confidence": 0.9,
        "matched_term": "ML",
        "match_type": "alias"
      },
      {
        "raw": "machine-learning",
        "skill_id": "...",
        "canonical_name": "Machine Learning",
        "confidence": 1.0,
        "matched_term": "Machine Learning",
        "match_type": "exact"
      },
      {
        "raw": "quantum knitting",
        "skill_id": null,
        "canonical_name": null,
        "confidence": 0.0,
        "matched_term": null,
        "match_type": "unmatched"
      }
    ]
  },
  "message": null
}
```

`match_type` is `exact`, `alias`, `collision`, or `unmatched`. Collisions and unknown terms do not invent a skill.

Confidence: exact canonical/name = `1.0`, alias = `0.9`, unmatched/collision = `0.0`.
