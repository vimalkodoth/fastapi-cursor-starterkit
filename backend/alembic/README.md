# Database migrations (Alembic)

This project uses **Alembic** for schema migrations. The database name is **`fastapi_db`** (see `POSTGRES_DB` in `docker-compose.yml` and `DATABASE_URL` in `app.core.database`). If you see Postgres errors like `FATAL: database "fastapi" does not exist`, some client is using the wrong database name—use **`fastapi_db`** or create a database named `fastapi` if that client cannot be changed.

## Run migrations

From the **backend** directory (or with `PYTHONPATH` set so `app` is importable):

```bash
cd backend
# Optional: set DB URL (default: postgresql://fastapi:fastapi@localhost:5432/fastapi_db)
# export DATABASE_URL=postgresql://fastapi:fastapi@postgres:5432/fastapi_db  # when running in Docker host network
alembic upgrade head
```

Inside Docker (e.g. same env as the API):

```bash
docker compose run --rm api alembic upgrade head
```

## Create a new migration (autogenerate)

After changing models in `app.models.database`:

```bash
cd backend
alembic revision --autogenerate -m "Describe your change"
alembic upgrade head
```

## Downgrade one revision

```bash
alembic downgrade -1
```

## Current schema

- **data_processing_records** – data processing requests and outcomes  
- **task_logs** – task execution logs with correlation IDs  

Defined in `app.models.database`; migrations live in `alembic/versions/`.
