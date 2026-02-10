# Commands and workflow (enforced)

## After editing backend Python code

1. Run **format** then **lint** (or **check** if you only want to verify without changing files).
   - From repo root: `make format` then `make lint`, or `make check`.
2. If you added or changed DB models, create/apply migrations: from `backend/`, `alembic revision --autogenerate -m "brief description"` then `alembic upgrade head`.

## Pre-commit

This project uses pre-commit for black, isort, flake8. After making a series of changes, run `pre-commit run --all-files` from repo root (or rely on git hooks if `pre-commit install` was run). Do not skip lint/format; the agent should run checks after edits.

## Scope

- Format/lint only **backend** Python (`backend/**/*.py`). Ignore `logger/`, `services/dataservice/` for project-wide make targets unless explicitly adding a new target.
- Do not run frontend tooling (no npm/yarn for app UI); this repo is API-only.
