# Structure

- **Backend (FastAPI):** `backend/` — main application. Entry: `main.py` (app is `main:app`).
- **Layers:** Controllers in `backend/app/api/v1/endpoints/`, business logic in `backend/app/services/`, data access in `backend/app/repositories/`, infrastructure in `backend/app/infrastructure/`, Celery tasks in `backend/app/tasks/`, core config in `backend/app/core/`.
- **Other services:** `logger/`, `services/` (e.g. `services/dataservice/` and any new service under `services/`), `rabbitmq/` — separate deployables. Do not mix their code with `backend/`. New top-level Python services (same level as backend, logger, services): add to root `Makefile` `PYTHON_SERVICES` and to `.pre-commit-config.yaml` `files` regex.
- **Docs:** `docs/` (ARCHITECTURE.md, FLOW_EXAMPLE.md). Reference these for flows and patterns.

## Where to add code

- New API routes: `backend/app/api/v1/endpoints/` (follow existing `data.py`, `database.py`).
- New business logic: `backend/app/services/` and/or `backend/app/repositories/`.
- New Celery tasks: `backend/app/tasks/` and register in `backend/app/infrastructure/celery.py` if needed.
- New DB models: `backend/app/models/database.py`; then add an Alembic migration under `backend/alembic/versions/`.
- Database name is **fastapi_db** (never `fastapi`). Migrations: run from `backend/` with `alembic upgrade head`.

## Commands (run from repo root or backend as noted)

- Format: `make format` (from repo root; black + isort on all Python services).
- Lint: `make lint` (flake8 + mypy on all Python services).
- Check (no edits): `make check` (black --check, isort --check, flake8).
- Docker: `docker compose up -d`, `docker compose down`, `docker compose logs -f <service>`.
- Migrations: from `backend/`, `alembic upgrade head` or `alembic revision --autogenerate -m "description"`.
- Tests: see `scripts/user-journey-tests.sh`, `scripts/test-async-flow.sh` for flows; prefer running tests after code changes.

Do not invent new commands; use the above. Python scope for lint/format/check and pre-commit: **all services** — `backend/`, `logger/`, `services/` (entire tree; every service under it), and any other top-level Python service added to `Makefile` and pre-commit (same style and coding standards everywhere).

## Rules in this folder

- **project.md** (this file), **commands-and-workflow.md**, **standards.md** — project structure, commands, and enforced patterns.
- **fastapi-python-best-practices.md** — project-specific FastAPI and Python; **fastapi-patterns.md** — general FastAPI patterns.
- **python-style.md** — Python 3.x style; **clean-code.md** — clean code; **error-handling.md** — error handling; **code-quality.md** — edit/change guidelines.
- **database-postgres.md** — PostgreSQL, SQLAlchemy, Alembic.

## Agent skills

For **agent skills** (fastapi-best-practices, python-anti-patterns, python-design-patterns, python-testing-patterns, python-performance-optimization) under `.agents/skills/`, see **`.agents/skills/README.md`** for alignment with this project, these rules, and Cursor commands. **fastapi-best-practices** is the team skill for FastAPI standards and conventions.
