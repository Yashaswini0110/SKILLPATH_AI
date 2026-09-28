# API hardening (Phase 25)

List endpoints for roles, skills, courses, projects, mentors, and
assessments return a page:

```text
{ items, page, page_size, total, total_pages, sort, order }
```

Query params: `page`, `page_size` (1–100, default 50), `sort`, `order`.
Existing filters (`category`, `skill_id`) still apply. Default page size
covers the current catalog in one request.

`GET /api/v1/learning-paths` is a single plan, not a list.

Rate limit: `RATE_LIMIT_REQUESTS` per `RATE_LIMIT_WINDOW_SECONDS` per
client IP. Exceeding it returns `429` with `RATE_LIMIT_EXCEEDED`.
Unknown HTTP errors now use the same `{ error }` envelope.
