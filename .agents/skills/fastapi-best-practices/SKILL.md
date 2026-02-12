---
name: fastapi-best-practices
description: FastAPI standards and best practices for this project. Use when adding or changing API routes, services, dependencies, or middleware so the team follows the same patterns and conventions.
---

## In this repository

- **Scope:** FastAPI app lives in `backend/`. Python also in `logger/` and `services/`; same style applies. After edits run **`make format`** and **`make lint`** from repo root.
- **Rules:** `.cursor/rules/fastapi-python-best-practices.md`, `.cursor/rules/fastapi-patterns.md`, `.cursor/rules/standards.md`, `.cursor/rules/project.md`.
- Full context: `.agents/skills/README.md`.

---

# FastAPI best practices (team standards)

Standards derived from this project’s implementation. Follow these so the codebase stays consistent and maintainable.

## 1. Project structure and layers

- **Endpoints (controllers):** `backend/app/api/v1/endpoints/` — one file per domain (e.g. `data.py`, `database.py`, `metrics.py`). Only HTTP concerns: parse request, call service/repo via `Depends`, return response or raise `HTTPException`.
- **Business logic:** `backend/app/services/` — services receive repositories (and optionally other deps) via constructor; use `AsyncSession` for DB when in the API path. No raw request/response objects.
- **Data access:** `backend/app/repositories/` — repositories receive `AsyncSession`; perform queries and commits. No business rules.
- **Shared dependencies:** `backend/app/api/v1/deps.py` — define `get_*` functions that return service or repository instances (injecting `get_async_session`). Use these in route handlers via `Depends(...)`.
- **Models:** `backend/app/models/database.py` (SQLModel table models), `backend/app/models/schemas.py` (Pydantic request/response). DB name is **fastapi_db**.

**Do not:** Put SQL or business logic in endpoint files; put HTTP logic in services or repositories.

## 2. Routers and API design

- Use **APIRouter** with a **prefix** and **tags** for OpenAPI grouping:
  ```python
  router = APIRouter(prefix="/data", tags=["data"])
  ```
- Mount routers in `backend/app/api/v1/__init__.py` on the v1 router (`prefix="/api/v1"`).
- Prefer **explicit `response_model`** and **status_code** on route decorators:
  ```python
  @router.post("/process", response_model=TaskResult, status_code=200)
  async def process_data(request: DataRequest, service: DataService = Depends(get_data_service)) -> TaskResult:
  ```
- Use **async def** for handlers that do I/O (DB, external calls). Use **def** only for handlers that do no I/O (e.g. simple metrics that read in-memory state).
- Document with short **docstrings** on each route; they appear in OpenAPI.

## 3. Dependencies (Depends)

- **Session:** Use `get_async_session` from `app.core.database` for any route or dependency that touches the DB. Never create a raw engine or session in an endpoint.
- **Services and repositories:** Define factory functions in `app.api.v1.deps` that depend on `get_async_session` and return a service or repository instance. Use them in endpoints via `Depends(get_data_service)`, `Depends(get_task_repository)`, etc.

Example (from `deps.py`):

```python
def get_data_service(session: AsyncSession = Depends(get_async_session)) -> DataService:
    """Dependency that returns a DataService instance (async session)."""
    return DataService(session)
```

- In endpoints, inject the **service** (or repository when the endpoint only needs data access) and call methods; do not instantiate services or repos inside the route.

## 4. Request and response models

- **Request bodies:** Use Pydantic models from `app.models.schemas` (e.g. `DataRequest`). Declare them as the route parameter; FastAPI validates and parses.
- **Responses:** Use Pydantic response models (e.g. `TaskResult`, `RecordResponse`, `TaskLogResponse`) and set `response_model=` on the decorator. **Never** return a SQLModel/ORM instance directly; map to a schema and return that (e.g. `RecordResponse.model_validate(r)` or `RecordResponse(**record)`).
- Prefer **model_validate(orm_instance)** (Pydantic v2) when building response models from ORM objects.

## 5. Async in the request path

- Use **async def** for route handlers that perform I/O (DB, HTTP, etc.). Use **AsyncSession** and async repository methods so the event loop is not blocked.
- If you must call a **blocking** operation (e.g. sync RabbitMQ RPC), run it in a thread pool with **`await asyncio.to_thread(blocking_func, ...)`** and keep the rest of the flow async (e.g. DB write). See `DataService.process_data_sync_and_save` in `app.services.data_service`.
- Sync engine/session are only for **Celery tasks** and **startup** (e.g. `init_db`). Do not use them in request handlers.

## 6. Error handling

- **API boundary:** Use **HTTPException** with the appropriate status code (400, 404, 503, etc.) and a clear `detail`. Do not let uncaught exceptions bubble to the client without mapping.
- **Services/repositories:** Raise domain-friendly exceptions or return `None`/result; let the **endpoint** translate to HTTP (e.g. `if not record: raise HTTPException(status_code=404, detail="Record not found")`).
- **External calls:** When a dependency (e.g. `call_service_via_rabbitmq`) raises `ValueError`, catch it in the endpoint and map to `HTTPException(status_code=503, detail=str(e))` (or another suitable code).
- Handle errors and edge cases **first** (early returns, guard clauses); keep the happy path last. See `.cursor/rules/error-handling.md`.

## 7. Middleware and app setup

- **CORS:** Configure in `main.py` (e.g. `CORSMiddleware`). Keep origins/methods/headers explicit for production.
- **Idempotency:** Optional `Idempotency-Key` header on POST endpoints that support it; implemented in middleware (`IdempotencyMiddleware`). Do not duplicate idempotency logic in services. Paths are listed in the middleware (e.g. `/api/v1/data/process`, `/api/v1/data/process-async`).
- **Startup:** For simple one-off init (e.g. `init_db()`), `@app.on_event("startup")` is acceptable. For multi-step startup/shutdown, prefer a **lifespan** context manager.

## 8. Database (PostgreSQL, SQLModel, Alembic)

- **In routes:** Always use **async** session via `get_async_session` and pass it to services/repositories. Use connection pooling (already configured in `app.core.database`).
- **Repositories:** Accept `AsyncSession` in the constructor; use `await session.commit()`, `await session.refresh(record)` after writes; use `select(Model).where(...)` and `await session.execute()` / `session.get()` for reads. Avoid N+1; batch or eager load when needed.
- **Migrations:** Add or change models in `app.models.database`; then from `backend/` run `alembic revision --autogenerate -m "description"` and `alembic upgrade head`. Do not change the database name from **fastapi_db**.

## 9. Naming and style

- **Files and modules:** Lowercase with underscores (e.g. `data_service.py`, `task_repository.py`, `data.py` for the data router).
- **Routers:** Name the router variable `router`. Group related routes in one file (e.g. all `/data/*` in `data.py`).
- **Schemas:** Clear names for request (e.g. `DataRequest`) and response (e.g. `TaskResult`, `RecordResponse`). Use type hints and optional fields where appropriate.
- **Docstrings:** Short module docstring and route docstrings so OpenAPI and readers understand purpose. Document parameters and return values in Pydantic models if non-obvious.

## 10. Team checklist (before merging)

- [ ] New routes live under `backend/app/api/v1/endpoints/` and are mounted in `api/v1/__init__.py`.
- [ ] Handlers use `Depends(get_async_session)` or `Depends(get_*_service)` / `Depends(get_*_repository)` from `deps.py`; no ad-hoc session or service creation in routes.
- [ ] Request/response use Pydantic models from `schemas.py`; responses use `response_model=` and never return raw ORM instances.
- [ ] I/O in the request path is **async** (AsyncSession, async repo methods); any blocking call is wrapped in `asyncio.to_thread`.
- [ ] Errors are mapped to **HTTPException** in endpoints; services/repos do not raise HTTP-specific errors.
- [ ] New or changed DB models have an Alembic migration; DB name remains **fastapi_db**.
- [ ] `make format` and `make lint` have been run from repo root and pass.

## Quick reference (this project)

| Concern | Where / how |
|--------|-------------|
| Add route | `backend/app/api/v1/endpoints/<domain>.py` + include in `api/v1/__init__.py` |
| Add dependency | `backend/app/api/v1/deps.py` (e.g. `get_*_service`, `get_*_repository`) |
| Request/response models | `backend/app/models/schemas.py` |
| DB models | `backend/app/models/database.py` + Alembic migration |
| Business logic | `backend/app/services/` (accept session/repos in constructor) |
| Data access | `backend/app/repositories/` (accept AsyncSession) |
| Blocking in request path | `await asyncio.to_thread(sync_func, ...)` then continue async |
| Idempotency | Middleware; add path to `IDEMPOTENT_PATHS` if needed |

For more detail, see `.cursor/rules/fastapi-python-best-practices.md` and `.cursor/rules/standards.md`.
