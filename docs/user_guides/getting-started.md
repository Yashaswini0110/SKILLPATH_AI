# Getting started (Phase 21)

1. Copy `.env.example` to `.env`.
2. Start stores: `docker compose up -d postgres neo4j`
3. Backend: create the venv, `alembic upgrade head`, `uvicorn app.main:app --reload`
4. Frontend: `npm install` then `npm run dev`
5. Open http://localhost:5173/register
6. Set a target role on **Profile**, open **Path**, then **Assistant**
7. Ask “What should I learn next?” and confirm the answer matches the first path step
8. Open **Compare** and select two catalog roles
9. Confirm coverage and effort change by role, and that Profile still shows the same target
10. Optional: set `LLM_ENABLED=true` and `NVIDIA_API_KEY` from
    https://build.nvidia.com/openai/gpt-oss-20b to rephrase assistant answers.

OpenAPI: http://localhost:8000/docs

GitHub evidence is deferred. The rest of the app does not require it.
