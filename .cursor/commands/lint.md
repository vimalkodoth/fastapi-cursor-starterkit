# /lint — Format and lint backend (enforced workflow)

1. From the **repository root**, run:
   - `make format` (black + isort on backend)
   - `make lint` (flake8 + mypy on backend)
2. If there are errors, fix them in the backend code. Do not change the Makefile or linter config unless the user explicitly asks.
3. Report any remaining errors to the user. Do not commit; the user decides when to commit.

Scope: backend Python only (`backend/`). This project has no frontend.
