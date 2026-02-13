# /check — Verify formatting and lint without editing

1. From the **repository root**, run `make check` (black --check, isort --check, flake8 on all Python services).
2. Report pass/fail and any failure output. Do not modify files; this is verify-only.
3. If the user wants to fix failures, suggest running `/lint` or `make format` then `make lint`.

Scope: all Python services — `backend/`, `services/` (entire tree), and any other top-level service in the Makefile.