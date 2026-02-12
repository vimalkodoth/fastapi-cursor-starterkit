# Python 3.x style

Python and FastAPI; no Flask. Applies to all services under `backend/`, `logger/`, `services/`.

## Project layout

- Use clear module organization; see `.cursor/rules/project.md` for this repo's layout.
- Keep config in environment or a config module; requirements in `requirements.txt` or `pyproject.toml`.

## Code style

- **Black** for formatting, **isort** for import sorting. Line length 88.
- **PEP 8:** `snake_case` for functions and variables, `PascalCase` for classes, `UPPER_CASE` for constants.
- Use **absolute imports** over relative imports.
- Use **lowercase with underscores** for modules and files (e.g. `data_service.py`, `task_repository.py`).

## Type hints

- Use type hints for all function parameters and return values.
- Prefer `Optional[T]` or `T | None` (Python 3.10+).
- Use `typing` (e.g. `TypeVar`, `Protocol`) where helpful.

## Naming and structure

- Use descriptive names; auxiliary verbs where helpful (e.g. `is_active`, `has_permission`).
- Prefer **functional, declarative** style; avoid classes where a function is enough.
- Prefer iteration and small modules over duplication.
- Use **Receive an Object, Return an Object (RORO)** where it fits.

## Conditionals

- Use simple one-line style when clear: `if condition: do_something()`.
- Handle errors and edge cases first; keep the happy path last (see `.cursor/rules/error-handling.md`).
- Avoid deep nesting; use early returns and guard clauses instead of long `else` chains.

## Database (Python/ORM)

- Use SQLAlchemy (or SQLModel) and Alembic for migrations.
- Use connection pooling; define models in clear modules. See `.cursor/rules/database-postgres.md`.

## Error handling

- Use try/except where needed; log appropriately.
- Return or raise clear errors; let the API layer map to HTTP. See `.cursor/rules/error-handling.md`.

## Documentation

- Use docstrings for public APIs (e.g. Google or NumPy style).
- Keep README and docs updated; document non-obvious behavior.

## Tooling

- Use a virtual environment; run `make format` and `make lint` from repo root (see `.cursor/rules/commands-and-workflow.md`).
