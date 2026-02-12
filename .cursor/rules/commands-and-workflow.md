# Commands and workflow

## After editing Python code (any service)

1. Run **format** then **lint** (or **check** if you only want to verify without changing files).
   - From repo root: `make format` then `make lint`, or `make check`.
2. If you added or changed DB models in `backend/`, create/apply migrations: from `backend/`, `alembic revision --autogenerate -m "brief description"` then `alembic upgrade head`.

## Pre-commit

This project uses pre-commit for black, isort, flake8 on **all Python services** (`backend/`, `logger/`, `services/`). After making changes, run `pre-commit run --all-files` from repo root (or rely on git hooks if `pre-commit install` was run). Do not skip lint/format; the agent should run checks after edits.

## Scope

- Format/lint applies to **all backend and API services**: `backend/`, `logger/`, `services/` (entire tree — every service under it, e.g. dataservice and any new one), and any other top-level Python service you add (add it to root `Makefile` `PYTHON_SERVICES` and `.pre-commit-config.yaml`). Same style guides and coding standards everywhere.
- Do not run frontend tooling (no npm/yarn for app UI); this repo is API-only.
