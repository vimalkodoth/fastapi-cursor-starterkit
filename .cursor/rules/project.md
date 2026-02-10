# Project context (enforced)

This is an **API-only** starter kit. There is **no frontend**. Do not add UI, frontend frameworks, or browser-only code.

## Structure

- **Backend (FastAPI):** `backend/` — main application. Entry: `main.py` (app is `main:app`).
- **Layers:** Controllers in `backend/app/api/v1/endpoints/`, business logic in `backend/app/services/`, data access in `backend/app/repositories/`, infrastructure in `backend/app/infrastructure/`, Celery tasks in `backend/app/tasks/`, core config in `backend/app/core/`.
- **Other services:** `logger/`, `services/dataservice/`, `rabbitmq/` — separate deployables. Do not mix their code with `backend/`.
- **Docs:** `docs/` (ARCHITECTURE.md, FLOW_EXAMPLE.md). Reference these for flows and patterns.

## Where to add code

- New API routes: `backend/app/api/v1/endpoints/` (follow existing `data.py`, `database.py`).
- New business logic: `backend/app/services/` and/or `backend/app/repositories/`.
- New Celery tasks: `backend/app/tasks/` and register in `backend/app/infrastructure/celery.py` if needed.
- New DB models: `backend/app/models/database.py`; then add an Alembic migration under `backend/alembic/versions/`.
- Database name is **fastapi_db** (never `fastapi`). Migrations: run from `backend/` with `alembic upgrade head`.

## Commands (run from repo root or backend as noted)

- Format: `make format` (from repo root; runs black + isort on backend).
- Lint: `make lint` (flake8 + mypy on backend).
- Check (no edits): `make check` (black --check, isort --check, flake8).
- Docker: `docker compose up -d`, `docker compose down`, `docker compose logs -f <service>`.
- Migrations: from `backend/`, `alembic upgrade head` or `alembic revision --autogenerate -m "description"`.
- Tests: see `scripts/user-journey-tests.sh`, `scripts/test-async-flow.sh` for flows; prefer running tests after code changes.

Do not invent new commands; use the above. Python scope for lint/format: `backend/` (and backend-only hooks in pre-commit).
