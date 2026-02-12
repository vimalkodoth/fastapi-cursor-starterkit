# FastAPI Starter Kit

**Production-ready, AI-native backend template for engineering teams.** Start from a clean base—add features and services with Cursor or other AI tools while keeping one standard: layered architecture, observability, and quality checks built in.

---

## Why this backend template?

- **Built for AI-assisted development** — Cursor rules, shared dependencies, and consistent patterns so agents and humans ship the same way. No “AI wrote it, we’ll fix it later.”
- **Production-minded from day one** — Async/sync split, DLQ, idempotency, metrics, and migrations. Scale and operate without rewrites.
- **Backend only, no frontend** — One surface to maintain: a REST API. Consume from web, mobile, or other services. Add a UI when you’re ready.
- **Extend, don’t fight** — Clear places for new routes, services, repos, and tasks. Docs and rules tell the team (and AI) where everything goes.

---

## Features

| Area | What you get |
|------|----------------|
| **API** | FastAPI, Pydantic, async DB (SQLModel + PostgreSQL), REST + OpenAPI (Swagger / ReDoc) |
| **Workloads** | Sync RPC (RabbitMQ) and async jobs (Celery + Redis); non-blocking event loop |
| **Data** | PostgreSQL, Alembic migrations, connection pooling (sync + async) |
| **Messaging** | RabbitMQ (RPC + DLQ), optional idempotency (Redis), observability metrics |
| **Quality** | PEP 8, Black, isort, flake8, mypy, pre-commit; shared deps and response schemas |
| **AI-native** | Cursor rules and commands; patterns aligned so agents follow your standards |
| **Deploy** | Docker Compose for local dev; Kubernetes-ready configs |

---

## Quick start

**Prerequisites:** Docker and Docker Compose; Python 3.9+ for local backend work.

```bash
# Clone and start
git clone <your-repo-url>
cd fastapi-cursor-starterkit
docker compose up -d
```

| Service | URL |
|--------|-----|
| **API** | http://localhost:8000 |
| **API docs (Swagger)** | http://localhost:8000/api/v1/docs |
| **API docs (ReDoc)** | http://localhost:8000/api/v1/redoc |
| **Metrics** | http://localhost:8000/api/v1/metrics |
| **Gateway (Nginx)** | http://localhost:8080 |
| **RabbitMQ Management** | http://localhost:15672 (guest / welcome1) |
| **Logger** | http://localhost:5001 |

```bash
# Logs
docker compose logs -f

# Stop
docker compose down
```

---

## AI-native: built for Cursor and AI engineering teams

This backend repo is set up so **AI tools and humans share one playbook.** Use it as the base for feature work with Cursor (or similar) and keep behavior consistent.

- **`.cursor/rules/`** — Always-on context: API-only, layout (endpoints → services → repos), commands, and patterns (DLQ, idempotency, fastapi_db). FastAPI/Python practices are adapted from [awesome-cursorrules](https://github.com/PatrickJS/awesome-cursorrules). Commit rules so the whole team (and every agent session) sees the same standards.
- **`.cursor/commands/`** — Shortcuts like `/lint` (format + lint) and `/check` (verify only). Run them after backend edits so the agent doesn’t skip quality.
- **Workflow** — After changing backend code, run format and lint (or `/lint`). For larger features, use Plan Mode so the agent plans before coding and stays within the structure in the rules.

**What to tell the team**

1. Open the project in Cursor; rules and commands load from the repo. No extra setup.
2. After editing backend code, run `/lint` (or `make format` then `make lint`).
3. For bigger changes, use Plan Mode (e.g. Shift+Tab in the agent input).
4. If the agent keeps making the same mistake, add or tweak a rule in `.cursor/rules/` and commit it.

Ref: [Cursor – Best practices for coding with agents](https://cursor.com/blog/agent-best-practices).

---

## Project structure

```
.
├── backend/                 # FastAPI app
│   ├── app/
│   │   ├── api/v1/          # Controllers + shared deps (deps.py)
│   │   ├── core/            # Config, DB, dependencies, metrics, idempotency
│   │   ├── services/        # Business logic
│   │   ├── repositories/    # Data access
│   │   ├── models/          # DB + Pydantic schemas
│   │   ├── tasks/           # Celery tasks
│   │   └── infrastructure/  # RabbitMQ, Celery
│   └── main.py
├── services/dataservice/    # Example microservice (RabbitMQ consumer)
├── logger/                  # Event / observability service
├── docs/                    # ARCHITECTURE, flows, sequence diagrams
├── docker-compose.yml
└── .cursor/                 # Rules + commands for AI-assisted dev
```

New API routes → `backend/app/api/v1/endpoints/`. New logic → `services/` or `repositories/`. New DB models → `models/` + Alembic migration. See `.cursor/rules/project.md` for the full “where to add code” guide.

---

## Code quality

- **Tools:** Black, isort, flake8, mypy; pre-commit hooks.
- **Scope:** All Python services: `backend/`, `logger/`, `services/` (entire tree), and any other top-level service added to the root Makefile. Same style and standards everywhere.

```bash
# From repo root
make format    # black + isort
make lint      # flake8 + mypy
make check     # verify only (no edits)
```

Development setup:

```bash
cd backend
pip install -r requirements-dev.txt
pre-commit install
pre-commit install --hook-type pre-push
```

Both hooks (commit: black, isort, flake8 on all Python services; push: uncommitted-changes warning, optional tests) are managed by pre-commit; no manual copy needed.

Details: [PEP8_STYLE_GUIDE.md](./PEP8_STYLE_GUIDE.md).

---

## API at a glance

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/data/process` | Sync processing (RabbitMQ RPC) |
| POST | `/api/v1/data/process-async` | Async processing (Celery; returns task ID) |
| GET | `/api/v1/data/process-async/{task_id}` | Task status |
| GET | `/api/v1/database/records` | List processing records |
| GET | `/api/v1/database/records/{task_id}` | One record |
| GET | `/api/v1/database/logs` | Task logs |
| DELETE | `/api/v1/database/records/{task_id}` | Delete record |
| GET | `/api/v1/metrics` | Queue depth, RPC latency/timeouts |

Optional **`Idempotency-Key`** header on both POST data endpoints (Redis, 1h TTL).

---

## Documentation

| Doc | Description |
|-----|-------------|
| [ARCHITECTURE.md](./docs/ARCHITECTURE.md) | System design, components, flows |
| [FLOW_EXAMPLE.md](./docs/FLOW_EXAMPLE.md) | Sync vs async processing walkthrough |
| [SEQUENCE-DIAGRAMS.md](./docs/SEQUENCE-DIAGRAMS.md) | Use-case sequence diagrams |
| [backend/alembic/README.md](./backend/alembic/README.md) | Migrations (DB name **fastapi_db**) |
| [PEP8_STYLE_GUIDE.md](./PEP8_STYLE_GUIDE.md) | Style and tooling |
| [GIT_SETUP.md](./GIT_SETUP.md) | Git and pre-commit |

---

## Technology stack

- **FastAPI** — Web framework  
- **SQLModel** — ORM (Pydantic + SQLAlchemy)  
- **PostgreSQL** — Database  
- **Celery** + **Redis** — Async task queue and result backend  
- **RabbitMQ** + **kombu** — RPC and DLQ  
- **Docker Compose** — Local dev; Kubernetes configs included  

---

## License

Apache License 2.0. See [LICENSE](./LICENSE).
