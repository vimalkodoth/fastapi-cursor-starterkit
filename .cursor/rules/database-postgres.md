# Database — PostgreSQL

This project uses **PostgreSQL** with **SQLAlchemy** (and SQLModel) and **Alembic**. Apply to backend and any service that touches the DB.

## Schema and design

- Use proper **normalization**; define clear relations and constraints.
- Use appropriate **data types**; define **indexes** for frequent filters and joins.
- Use **constraints** (unique, check, fk) in the schema; implement **cascades** where intended.

## Migrations (Alembic)

- Use **Alembic** for all schema changes; do not change schema without a migration.
- Run migrations from `backend/`: `alembic revision --autogenerate -m "description"`, then `alembic upgrade head`.
- Database name is **fastapi_db** (see `.cursor/rules/standards.md`).

## Connection and sessions

- Use **connection pooling** (configured in `backend/app/core/database.py`).
- In API routes use **async** engine and **AsyncSession**; use sync Session only in workers or startup.

## Queries and performance

- **CQRS:** Use **read** repositories (and query services) for all read operations; use **write** repositories (and command services) for create/update/delete. This allows scaling reads independently (e.g. read replicas, caches). See `.cursor/rules/cqrs.md`.
- **Optimize queries**; avoid N+1 (eager load or batch where needed).
- Use proper **filtering** and **pagination** for list endpoints.
- Prefer **single, clear queries** over many small ones; use transactions for multi-step writes.

## Transactions

- Use **transactions** for operations that must succeed or fail together.
- Commit or rollback explicitly where appropriate; avoid long-lived transactions in request path.

## Security

- Do not expose raw SQL from user input; use ORM or parameterized queries.
- Handle **sensitive data** appropriately; use env-based config for credentials.

## Health and operations

- Handle **database errors** in code (retries, logging, clear responses).
- Document schema and migrations; monitor DB health in production.
