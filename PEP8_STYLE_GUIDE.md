# Code style guide

This project follows **PEP 8** with tool-driven enforcement.

## Tools and config

- **Black** (line length 88) — formatting. Config: `pyproject.toml` if present, else defaults.
- **isort** — import sorting.
- **flake8** — linting. Config: [.flake8](.flake8) (max-line-length 88, extend-ignore E203, E266, E501, W503).
- **mypy** — type checking (backend). Run via `make lint` from repo root or `backend/`.
- **Pre-commit** — `.pre-commit-config.yaml` runs black, isort, flake8 on commit.

## Scope

Format and lint apply to **backend** Python only (`backend/`). Run `make format` then `make lint` from the repo root (or `cd backend && make format && make lint`).

## References

- [PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008/)
- Project config: [.flake8](.flake8), [.pre-commit-config.yaml](.pre-commit-config.yaml), [backend/Makefile](backend/Makefile)
