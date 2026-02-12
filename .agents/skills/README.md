# Agent skills — project alignment

Skills in this folder are **aligned with this repository**. When using any skill, apply it in the context below so there are no conflicts with Cursor rules or project code.

## Repository context

- **Python scope:** All Python lives under `backend/`, `logger/`, and `services/` (entire tree). Same style and standards everywhere.
- **Stack:** FastAPI, Pydantic v2, SQLModel (SQLAlchemy + Pydantic), PostgreSQL, Alembic. Async in the API path; sync only in Celery tasks and init. RabbitMQ for RPC/DLQ.
- **No frontend:** API-only. Do not add UI, npm, or frontend tooling.
- **Structure:** API endpoints in `backend/app/api/v1/endpoints/`, business logic in `backend/app/services/`, data access in `backend/app/repositories/`. See `.cursor/rules/project.md`.

## Commands and workflow

- **Format/lint:** From **repo root**: `make format` then `make lint`, or `make check` (verify only). Applies to all Python services. See `.cursor/commands/lint.md` and `.cursor/commands/check.md`.
- **Migrations:** From `backend/`: `alembic revision --autogenerate -m "description"` then `alembic upgrade head`. DB name is **fastapi_db**.
- **Tests:** Flow tests live in `scripts/user-journey-tests.sh` and `scripts/test-async-flow.sh`. If you add pytest, use `backend/tests/` or per-service; for DB use PostgreSQL or mocks (project uses PostgreSQL, not SQLite).

## Rules to follow

- **Project & workflow:** `.cursor/rules/project.md`, `.cursor/rules/commands-and-workflow.md`, `.cursor/rules/standards.md`
- **CQRS:** `.cursor/rules/cqrs.md` — separate command (write) and query (read) services and repositories for API features.
- **FastAPI & Python:** `.cursor/rules/fastapi-python-best-practices.md`, `.cursor/rules/fastapi-patterns.md`, `.cursor/rules/python-style.md`
- **Clean code & quality:** `.cursor/rules/clean-code.md`, `.cursor/rules/error-handling.md`, `.cursor/rules/code-quality.md`
- **Database:** `.cursor/rules/database-postgres.md` (PostgreSQL, SQLModel, Alembic, connection pooling)

## Alignment with skills

| Skill | Aligns with |
|-------|-------------|
| **fastapi-best-practices** | **Team standards for FastAPI.** Project structure, Depends(), async/AsyncSession, asyncio.to_thread for blocking, request/response models, error handling, middleware, DB/migrations. Use when adding or changing API routes, services, or dependencies. See `.cursor/rules/fastapi-python-best-practices.md` and `standards.md`. |
| **cqrs-pattern** | **CQRS for API features.** Separate command (write) and query (read) services and repositories; endpoints inject the appropriate service. Use when adding or changing API features, new endpoints, or data access. See `.cursor/rules/cqrs.md` and `standards.md`. |
| **python-anti-patterns** | error-handling, clean-code, fastapi-python-best-practices (no blocking in async; use `asyncio.to_thread` if blocking required). Use Pydantic **model_validate** (v2), not from_orm. |
| **python-design-patterns** | project structure (endpoints → services → repositories), Depends() for DI in FastAPI, clean-code (SRP, separation of concerns). This repo also uses CQRS (command vs query); see cqrs-pattern skill. |
| **python-testing-patterns** | Test error paths and edge cases (error-handling, anti-patterns). In this repo, flow tests are in scripts/; pytest would go under backend/tests/ or per-service. |
| **python-performance-optimization** | Async I/O in API path; blocking only via `asyncio.to_thread`. DB: use AsyncSession, pooling, batching; see database-postgres.md. CQRS allows scaling reads (replicas, caches) independently. After changes: run `make format` and `make lint`. |

No skill should suggest: a different project layout, npm/frontend, SQLite as the app DB, or skipping format/lint. When in doubt, prefer `.cursor/rules` and this README.
