---
name: cqrs-pattern
description: CQRS (Command Query Responsibility Segregation) for this backend. Use when adding or changing API features, services, or repositories so reads and writes are separated and the team can scale and evolve each side independently.
---

## In this repository

- **Scope:** Backend API in `backend/`. Apply CQRS to `backend/app/services/`, `backend/app/repositories/`, and `backend/app/api/v1/endpoints/`. See `.cursor/rules/cqrs.md` for the canonical rule.
- **Layers:** Endpoints → services → repositories (unchanged). Within that, use **command** service/repo for writes and **query** service/repo for reads. Dependencies in `backend/app/api/v1/deps.py` must expose separate command and query factories where CQRS applies.
- After edits run **`make format`** and **`make lint`** from repo root. Full context: `.cursor/skills/README.md` and `.cursor/rules/project.md`.

---

# CQRS pattern (team standard)

Use this skill when implementing or refactoring features that read or write data so the codebase stays aligned with CQRS and ready for scaling.

## When to use this skill

- Adding new API endpoints that create, update, delete, or read data
- Adding new business logic or data access (new service methods, new repository methods)
- Refactoring existing domains (e.g. data processing records, task logs) to separate read and write paths
- Deciding where to put a new method (command vs query service/repository)

## Core idea

- **Commands** = operations that **change state** (create, update, delete, or trigger side effects like enqueueing a task). Use a **command service** and **write repository**.
- **Queries** = operations that **return state** and have no side effects (list, get by id, get status). Use a **query service** and **read repository**.

Same **domain** (e.g. “data records”) can have both; they live in separate classes so we can later point reads at a replica or cache and keep writes on the primary.

## Where to put code

| Operation type | Service | Repository | Endpoint uses |
|----------------|---------|------------|----------------|
| Create/update/delete record, submit async task | Command service (e.g. `DataCommandService`) | Write repository (e.g. `DataWriteRepository`) | `Depends(get_*_command_service)` |
| List records, get record, get task status, get logs | Query service (e.g. `DataQueryService`) | Read repository (e.g. `DataReadRepository`) | `Depends(get_*_query_service)` |

- **New domain:** Add both a command and a query service (and write/read repos). Register `get_*_command_service` and `get_*_query_service` in `deps.py`.
- **New write operation:** Add method to command service and write repository; endpoint that performs the write uses command service.
- **New read operation:** Add method to query service and read repository; endpoint that only reads uses query service.

## Endpoint wiring

- **GET** endpoints → inject **query** service (or query-only repository when no business logic).
- **POST / PUT / PATCH / DELETE** endpoints → inject **command** service.
- Do **not** inject a single “unified” service that does both reads and writes for the same resource; use separate command and query services.

## Repository split

- **Write repository:** `create_*`, `update_*`, `delete_*` only. Used only by command service (and optionally by Celery tasks for writes).
- **Read repository:** `get_*`, `get_*_list`, `get_*_by_*` only. Used only by query service.
- Same DB and session for both is fine initially; when you introduce a read replica, the query service can be configured with a session that uses the replica.

## Alignment with other rules

- **Project structure:** `.cursor/rules/project.md` — CQRS lives within the same layers (endpoints, services, repositories).
- **Design patterns:** `.cursor/skills/python-design-patterns/SKILL.md` — CQRS is separation of concerns and single responsibility applied to read vs write.
- **FastAPI:** `.cursor/rules/fastapi-patterns.md`, `.cursor/skills/fastapi-best-practices/SKILL.md` — keep using `Depends`, async, and response models; CQRS only changes *which* service/repo you inject.
