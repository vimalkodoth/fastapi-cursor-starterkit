# /lint — Format and lint all Python services

1. From the **repository root**, run:
   - `make format` (black + isort on backend, logger, entire services/ tree)
   - `make lint` (flake8 + mypy on all those)
2. If there are errors, fix them in the affected service code. Do not change the Makefile or linter config unless the user explicitly asks.
3. Report any remaining errors to the user. Do not commit; the user decides when to commit.

Scope: all Python services — `backend/`, `logger/`, `services/` (entire tree), and any other top-level service in the Makefile. Same style and standards everywhere.
