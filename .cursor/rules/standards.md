# Standards

## Code style

- Follow PEP 8 in **all Python services** (backend, logger, entire `services/` tree, and any other top-level Python service in the Makefile). Use **black** (line length 88) and **isort** for formatting. Config: `.flake8`, root `Makefile`, `.pre-commit-config.yaml`.
- Do not copy full style guides into rules; run `make format` and `make lint` from repo root. For detailed style, see `PEP8_STYLE_GUIDE.md` in the repo.

## Patterns to follow

- **API endpoints:** Use FastAPI `Depends` for session and services. See `backend/app/api/v1/endpoints/data.py` and `database.py` for request/response and error handling.
- **Services:** Use async `AsyncSession` in API path; sync `Session` only in Celery tasks and sync helpers. See `backend/app/core/database.py` (sync vs async engines).
- **RabbitMQ consumers:** Use DLQ: declare DLX and DLQ, main queue with `x-dead-letter-exchange` and `x-dead-letter-routing-key`, and on processing failure call `message.reject(requeue=False)`. See `backend/app/infrastructure/rabbitmq.py` and `services/dataservice/rabbitmq_client.py`.
- **Idempotency:** Optional `Idempotency-Key` header on POST data endpoints; handled in middleware. Do not duplicate idempotency logic in services.

## What not to do

- Do not add frontend or UI code.
- Do not change the database name from **fastapi_db** in config or migrations.
- Do not remove or bypass pre-commit hooks or make targets for format/lint; they apply to all services.
- Do not ack failed messages in RabbitMQ consumers; use `reject(requeue=False)` so they go to the DLQ.
