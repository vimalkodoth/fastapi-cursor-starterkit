# FastAPI patterns

Supplement to `.cursor/rules/fastapi-python-best-practices.md`. Project-specific details (DB name, DLQ, endpoints) stay in that file and in `standards.md`.

## Project structure

- Use a clear directory structure; keep routes organized by domain (e.g. under `api/v1/endpoints/`).
- Use **dependency injection** (`Depends`) for session, services, and shared resources. For data domains, inject **command** services for write operations and **query** services for read operations (CQRS). See `.cursor/rules/cqrs.md`.
- Use a **config** module or env for settings; keep middleware and startup logic in one place.

## API design

- Use correct **HTTP methods** and **status codes**.
- Use **Pydantic models** for request and response; validate input via Pydantic.
- Document APIs with **OpenAPI** (FastAPI generates this); keep descriptions and examples useful.

## Models and validation

- Use **Pydantic** (or SQLModel schemas) for validation and serialization.
- Use **type hints** on route handlers and dependencies; keep models in dedicated modules.

## Startup and shutdown

- Prefer **lifespan** context managers over `@app.on_event("startup")` and `@app.on_event("shutdown")` for multi-step setup/teardown.
- For simple one-off init (e.g. create_all), `on_event("startup")` is acceptable.

## Middleware

- Use middleware for **cross-cutting concerns**: logging, error handling, idempotency, performance.
- Keep middleware focused; avoid heavy logic in middleware.

## Performance

- Use **async** for I/O in the request path (DB, HTTP); avoid blocking the event loop (see fastapi-python-best-practices for `asyncio.to_thread` when blocking is required).
- Use **connection pooling**; optimize queries and serialization; consider caching for hot data.

## Security

- Use **CORS** appropriately; validate and sanitize input; use security headers where needed.
- Handle auth and errors consistently; log security-relevant events.

## Testing and docs

- Write **unit and integration tests**; use fixtures and mocking where appropriate.
- Use **docstrings** and type hints; keep API docs and README in sync with behavior.
