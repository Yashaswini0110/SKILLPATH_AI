# Phase 7 API — resource catalogs

Auth required. These endpoints list inventory. They do not rank or recommend.

| Method | Path |
| --- | --- |
| GET | `/api/v1/courses` |
| GET | `/api/v1/courses/{id}` |
| GET | `/api/v1/projects` |
| GET | `/api/v1/projects/{id}` |
| GET | `/api/v1/mentors` |
| GET | `/api/v1/mentors/{id}` |

Optional query: `skill_id` filters to resources mapped to that catalog skill.

Skill keys in `datasets/processed/resource_catalog.json` are taxonomy `name` values. Unknown names are skipped at seed time; the API does not invent skills.

The catalog is labeled `synthetic: true`.
