# Phase 0 + 1 complete

Stopped here. Phase 2 (skill taxonomy) is not started.

## What works

- PostgreSQL 15 via Docker (host port 5435)
- Alembic migration `0001_phase1`
- Register, login, JWT access/refresh, logout, RBAC
- Employee profile, education, experience, self-declared skills, target role
- React: `/login`, `/register`, `/dashboard`, `/profile`
- OpenAPI at `/docs`
- pytest, Ruff, Black, mypy

## Commands used

```powershell
docker compose up -d postgres
cd backend
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\pytest.exe
.\.venv\Scripts\ruff.exe check app tests
.\.venv\Scripts\black.exe --check app tests
.\.venv\Scripts\mypy.exe app
.\.venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000

cd ..\frontend
npm run dev
```

## Next

Phase 2 — Skill taxonomy: canonical names, aliases, and normalization so later extraction maps to one `skill_id`.
