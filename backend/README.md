# FastAPI Starter Kit - API Service

This is the main API service (backend only, no frontend). It provides RESTful endpoints for data processing with both synchronous and asynchronous patterns:

- **Synchronous**: RPC via RabbitMQ — client waits for response; record and producer start/end logs are written to PostgreSQL.
- **Asynchronous**: Celery task queue — client receives task ID and polls for results; Celery worker uses RabbitMQ RPC and writes records to PostgreSQL.

The API uses RabbitMQ (RPC), Redis (Celery broker/backend), and PostgreSQL (SQLModel, sync + async engines).

## Instructions

To run all services, see the main [README](../README.md).

### Run the service without Docker

1. Install dependencies (from repo root or `backend/`):

   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. Ensure PostgreSQL, Redis, and RabbitMQ are running (e.g. via `docker compose up -d postgres redis rabbitmq logger data-service`).

3. Start FastAPI:

   ```bash
   uvicorn main:app --reload
   ```

4. Start Celery worker (separate terminal):

   ```bash
   celery -A app.infrastructure.celery worker --loglevel=INFO
   ```

5. API docs:

   - http://localhost:8000/api/v1/docs
   - http://localhost:8000/api/v1/redoc

### Available Endpoints

- `POST /api/v1/data/process` - Synchronous data processing (saves to DB, writes task_logs). Optional `Idempotency-Key` header.
- `POST /api/v1/data/process-async` - Asynchronous data processing. Optional `Idempotency-Key` header.
- `GET /api/v1/data/process-async/{task_id}` - Get async task status
- `GET /api/v1/database/records` - Get data processing records
- `GET /api/v1/database/records/{task_id}` - Get record by task_id
- `GET /api/v1/database/logs` - Get task logs (optional `?correlation_id=`)
- `DELETE /api/v1/database/records/{task_id}` - Delete record
- `GET /health` - Health check

### Build container

```bash
docker build --tag fastapi-starter-api .
```

The same image is used for the API and the Celery worker (different commands in docker-compose).

### Kubernetes

Scripts and manifests use the `fastapi-starter` namespace. Backend manifests (e.g. `backend/backend-pod.yaml`, `backend/backend-celery-pod.yaml`, `backend/backend-ingress.yaml`) are referenced from the root `kubectl-setup.sh`; create them if needed following the patterns in `logger/logger-pod.yaml`.

- Create namespace: `kubectl create ns fastapi-starter`
- Apply backend: `kubectl apply -n fastapi-starter -f backend/backend-pod.yaml`
- Apply Celery: `kubectl apply -n fastapi-starter -f backend/backend-celery-pod.yaml`
- Port-forward for testing: `kubectl port-forward -n fastapi-starter deploy/fastapi-api 8000:8000`

## Structure

```
.
├── app/
│   ├── api/v1/endpoints/   # Controllers (data.py, database.py)
│   ├── core/               # database.py, dependencies.py
│   ├── infrastructure/     # celery.py, rabbitmq.py
│   ├── models/             # schemas.py (Pydantic), database.py (SQLModel)
│   ├── repositories/       # data_repository.py, task_repository.py
│   ├── services/           # data_service.py
│   └── tasks/              # data.py (Celery tasks)
├── alembic/                # Database migrations
├── main.py                 # FastAPI app entry (main:app)
├── Dockerfile
├── requirements.txt
└── README.md
```

## Environment Variables

- `DATABASE_URL` - PostgreSQL sync URL (default: `postgresql://fastapi:fastapi@localhost:5432/fastapi_db`)
- `ASYNC_DATABASE_URL` - Optional; defaults to same URL with `postgresql+asyncpg://`
- `CELERY_BROKER_URL` - Redis broker (default: `redis://redis:6379/0`)
- `CELERY_RESULT_BACKEND` - Redis result backend (default: `redis://redis:6379/0`)
- `IDEMPOTENCY_REDIS_URL` - Optional; Redis URL for idempotency store (defaults to `CELERY_BROKER_URL`). TTL 1h.
- `LOGGER_PRODUCER_URL` - Logger service URL for producer events
- `RABBITMQ_HOST`, `RABBITMQ_PORT`, `RABBITMQ_USER`, `RABBITMQ_PASSWORD`
- `DATA_QUEUE_NAME` - Queue name for data service (default: `data_queue`)

## Database migrations

See [alembic/README.md](alembic/README.md). From `backend/`: `alembic upgrade head`. Database name is **fastapi_db**.

## License

Licensed under the Apache License, Version 2.0.
