# CQRS — Command Query Responsibility Segregation

This project uses **CQRS** for the backend API: separate **commands** (writes) from **queries** (reads) so the team can scale and evolve read and write paths independently. Apply this when adding or changing API features, services, or repositories.

## When to use this rule

- Adding new API endpoints that read or write data
- Adding new business logic or data access in `backend/app/services/` or `backend/app/repositories/`
- Refactoring existing data flows (e.g. data processing records, task logs)

## Command vs query

| | **Commands (writes)** | **Queries (reads)** |
|--|------------------------|----------------------|
| **Purpose** | Change state: create, update, delete | Return current state; no side effects |
| **Examples** | Create record, delete record, submit async task | List records, get record by id, get task status, get logs |
| **Service layer** | Command service (e.g. `DataCommandService`) | Query service (e.g. `DataQueryService`) |
| **Repository layer** | Write repository (e.g. `DataWriteRepository`: `create_record`, `delete_*`, `update_*`) | Read repository (e.g. `DataReadRepository`: `get_*`, `get_records`) |
| **Endpoints** | POST, PUT, PATCH, DELETE | GET |

## Where code lives

- **Command side:** `backend/app/services/` (command service classes), `backend/app/repositories/` (write-only repository methods). Use for create/update/delete and for triggering async work (e.g. Celery task enqueue).
- **Query side:** `backend/app/services/` (query service classes), `backend/app/repositories/` (read-only repository methods). Use for list, get-by-id, and any read-only aggregation.
- **Endpoints:** `backend/app/api/v1/endpoints/` — inject **command service** for write operations, **query service** for read operations. Do not inject a single “unified” service that does both reads and writes for the same domain.

## Dependencies (`backend/app/api/v1/deps.py`)

- Provide separate dependencies for command and query (e.g. `get_data_command_service`, `get_data_query_service`). Use the same session for both unless you introduce a read replica (then query service can use a replica session).

## New features checklist

- **New write operation (create/update/delete):** Add or extend a **command** service and **write** repository; endpoint uses command service.
- **New read operation (list/get/search):** Add or extend a **query** service and **read** repository; endpoint uses query service.
- **New domain (e.g. “orders”):** Introduce both `OrderCommandService` + `OrderQueryService` and `OrderWriteRepository` + `OrderReadRepository` (or equivalent names), and wire them in `deps.py` and endpoints.

## Alignment

- **Layers:** Endpoints → services → repositories (unchanged). Within that, commands and queries are separate services/repos. See `.cursor/rules/project.md`.
- **Design patterns:** CQRS is an application of separation of concerns and single responsibility. See `.cursor/skills/python-design-patterns/SKILL.md` and `.cursor/skills/cqrs-pattern/SKILL.md`.
