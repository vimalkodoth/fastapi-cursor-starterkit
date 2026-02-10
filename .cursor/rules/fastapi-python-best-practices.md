# FastAPI & Python best practices (adapted for this project)

Adapted from [awesome-cursorrules](https://github.com/PatrickJS/awesome-cursorrules) (Python/FastAPI rules). This project is API-only; no frontend.

## Python / FastAPI style

- Use `def` for pure/sync functions and `async def` for I/O (DB, HTTP, etc.). Use type hints for all function signatures.
- Prefer Pydantic models (or SQLModel schemas) over raw dicts for request/response validation.
- Use descriptive names with auxiliary verbs where helpful (e.g. `is_active`, `has_permission`).
- Use lowercase with underscores for modules and files (e.g. `data_service.py`, `task_repository.py`).
- Prefer iteration and small modules over duplication; receive an object, return an object (RORO) where it fits.
- For conditionals: handle errors and edge cases first (early returns, guard clauses); keep the happy path last. Avoid deep nesting; use `if condition: return` instead of unnecessary `else`.

## FastAPI-specific

- Use FastAPI `Depends()` for session, services, and shared resources. See `backend/app/api/v1/endpoints/data.py` and `database.py` for patterns.
- Use `HTTPException` for expected API errors with appropriate status codes; use Pydantic models for request/response schemas.
- Use `async def` for route handlers that do I/O; use async DB session (`get_async_session`) in the API layer. Use sync engine/session only in Celery or init (see `backend/app/core/database.py`).
- Prefer minimal blocking I/O in request path; use async DB and async HTTP where available.
- Middleware: use for cross-cutting concerns (e.g. idempotency, logging, error handling). See `backend/app/core/idempotency.py`.

## Database & performance

- Use async DB operations in API routes (AsyncSession, asyncpg). Use sync Session only in workers or startup (e.g. `init_db`).
- Use connection pooling (already configured in `backend/app/core/database.py`). Optimize queries and avoid N+1.
- Use Pydantic/SQLModel for serialization; keep responses lean.

## Error handling and validation

- Validate input with Pydantic; handle business errors in services and map to HTTPException in endpoints.
- Log errors appropriately; return consistent error shapes to the client.
- In repositories and services, use clear exceptions or return types; let the API layer translate to HTTP.

## Testing and quality

- Run `make format` (black, isort) and `make lint` (flake8, mypy) after editing backend code. See `.cursor/rules/commands-and-workflow.md`.
- Follow PEP 8 and project style (`.flake8`, `PEP8_STYLE_GUIDE.md` in repo root). Use absolute imports; prefer type hints.
- For simple one-off startup (e.g. `init_db` / create_all), `@app.on_event("startup")` is acceptable; prefer lifespan for multi-step startup/shutdown.

## Blocking I/O in request path

- Use `async def` and async session for routes; do not block the event loop.
- If you must call a blocking operation (e.g. a sync RPC over RabbitMQ), run it in a thread pool: `await asyncio.to_thread(blocking_func, ...)` so the event loop stays responsive. See `DataService.process_data_sync_and_save` (blocking RPC run via `asyncio.to_thread`, then async DB write).

## What not to do (this project)

- Do not add frontend or UI code. Do not use Flask-specific patterns (this is FastAPI + SQLModel).
- Do not block the event loop in API handlers; use async I/O or run blocking calls in a thread pool. Do not skip lint/format before committing.
- Do not change the database name from **fastapi_db** or remove DLQ/reject(requeue=False) from RabbitMQ consumers.

Source: [awesome-cursorrules](https://github.com/PatrickJS/awesome-cursorrules) (FastAPI and Python rules), tailored for this starter kit.
