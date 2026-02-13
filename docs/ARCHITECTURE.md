# FastAPI Starter Kit - Complete Architecture

## Overview

This is a production-ready FastAPI starter kit designed for large-scale applications. It demonstrates a microservices architecture with asynchronous task processing, inter-service communication via RabbitMQ, and comprehensive observability.

**Note:** This is an **API-only** project. There is no frontend application included. The API can be consumed by any client (web applications, mobile apps, other services, etc.) via HTTP/REST.

**Key Features:**
- RESTful API with FastAPI (API-only, no frontend)
- Asynchronous task processing with Celery
- Microservices communication via RabbitMQ (RPC pattern)
- Observability with OpenTelemetry and SigNoz
- Docker Compose for local development
- Kubernetes-ready deployment configurations

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    EXTERNAL CLIENTS (Not Part of Project)              │
│          (Web Apps, Mobile Apps, Other Services, API Clients)          │
│                    This project provides API endpoints only             │
└──────────────────────────────┬────────────────────────────────────────┘
                                │
                                │ HTTP/REST
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        GATEWAY LAYER                                    │
│                            Nginx                                        │
│                    Reverse Proxy (Host 8081)                           │
│                    - Request Routing                                    │
│                    - Load Balancing (when scaled)                      │
└──────────────────────────────┬────────────────────────────────────────┘
                                │
                                │ HTTP
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        API LAYER                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  FastAPI Application (Port 8000)                                  │  │
│  │  - RESTful API Endpoints                                         │  │
│  │  - Request Validation (Pydantic)                                 │  │
│  │  - CORS Middleware                                               │  │
│  │  - OpenAPI Documentation                                          │  │
│  │                                                                   │  │
│  │  Endpoints:                                                       │  │
│  │  - POST /api/v1/data/process (sync)                            │  │
│  │  - POST /api/v1/data/process-async (async)                     │  │
│  │  - GET /api/v1/data/process-async/{task_id} (status)            │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                │                                        │
│                    ┌───────────┴───────────┐                            │
│                    │                       │                            │
│            Synchronous              Asynchronous                        │
│            (Direct)                 (Celery Task)                       │
│                    │                       │                            │
│                    ▼                       ▼                            │
│  ┌─────────────────────────┐  ┌─────────────────────────┐              │
│  │  EventProducer          │  │  Celery Task Queue     │              │
│  │  (kombu)                 │  │  → Redis               │              │
│  └─────────────────────────┘  └─────────────────────────┘              │
└──────────────────────────────┬────────────────────────────────────────┘
                                │
                                │ RabbitMQ / Redis / PostgreSQL
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    DATA & MESSAGE BROKER LAYER                         │
│  ┌──────────────────────┐  ┌──────────────────────┐                   │
│  │  RabbitMQ            │  │  Redis                │                   │
│  │  (Port 5672)         │  │  (Port 6379)          │                   │
│  │  - Service Queue     │  │  - Celery Broker      │                   │
│  │  - RPC Messages      │  │  - Task Results       │                   │
│  └──────────────────────┘  └──────────────────────┘                   │
│  ┌──────────────────────┐                                              │
│  │  PostgreSQL          │                                              │
│  │  (Port 5432)         │                                              │
│  │  - Persistent Storage│                                              │
│  │  - SQLModel ORM     │                                              │
│  └──────────────────────┘                                              │
└──────────────────────────────┬────────────────────────────────────────┘
                                │
                                │ RabbitMQ Queue: data_queue
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    BACKGROUND PROCESSING                                │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Celery Worker                                                   │  │
│  │  - Picks up tasks from Redis                                     │  │
│  │  - Uses EventProducer (kombu)                                    │  │
│  │  - Sends messages to RabbitMQ                                    │  │
│  │  - Stores results in Redis                                       │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬────────────────────────────────────────┘
                                │
                                │ RabbitMQ Queue: data_queue
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    MICROSERVICES LAYER                                  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Data Service                                                    │  │
│  │  - Listens to RabbitMQ queue: data_queue                         │  │
│  │  - Processes data (transformation, validation)                  │  │
│  │  - Returns processed data                                        │  │
│  │  - Uses EventReceiver (kombu)                                    │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬────────────────────────────────────────┘
                                │
                                │ HTTP (optional)
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY LAYER                                 │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  OTel Collector (4317/4318) → SigNoz (run separately)             │  │
│  │  - Traces, metrics, logs via OTLP                               │  │
│  │  - Tracks correlation IDs                                        │  │
│  │  - Event tracking for debugging                                  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Backend Service (`backend/`)

**Technology:** FastAPI, Python 3.x

**Architecture Pattern:** MVC-like (Model-View-Controller)
- **Controllers (Endpoints)**: Handle HTTP requests/responses (`app/api/v1/endpoints/`)
- **Services**: Business logic layer (`app/services/`)
- **Repositories**: Data access layer (`app/repositories/`)
- **Models**: Data models (`app/models/`)
- **Core**: Configuration and dependencies (`app/core/`)
- **Infrastructure**: RabbitMQ, Celery (`app/infrastructure/`)
- **Tasks**: Celery tasks (`app/tasks/`)

**Responsibilities:**
- Expose RESTful API endpoints
- Request validation using Pydantic
- Business logic separation
- Support both synchronous and asynchronous processing

**Key Files:**
- `main.py` - FastAPI application entry point
- `app/api/v1/endpoints/` - Controllers (HTTP handlers)
  - `data.py` - Data processing endpoints
  - `database.py` - Database query endpoints
- `app/services/` - Business logic layer
  - `data_service.py` - Data processing business logic
- `app/repositories/` - Data access layer
  - `data_repository.py` - Data records repository
  - `task_repository.py` - Task logs repository
- `app/core/` - Core configuration
  - `database.py` - Database setup and session management
  - `dependencies.py` - Service communication helpers
  - `idempotency.py` - Idempotency middleware (optional Idempotency-Key, Redis, 1h TTL)
- `app/models/` - All data models
  - `schemas.py` - Pydantic models (API request/response)
  - `database.py` - SQLModel database models
- `app/tasks/` - Celery tasks
  - `data.py` - Data processing tasks
- `app/infrastructure/` - Infrastructure code
  - `rabbitmq.py` - RabbitMQ client (EventProducer/EventReceiver using kombu)
  - `celery.py` - Celery worker configuration

**Endpoints:**
- `GET /` - Root endpoint (API information)
- `GET /health` - Health check
- `POST /api/v1/data/process` - Synchronous data processing (saves to DB). Optional `Idempotency-Key` header.
- `POST /api/v1/data/process-async` - Asynchronous data processing. Optional `Idempotency-Key` header.
- `GET /api/v1/data/process-async/{task_id}` - Get async task status
- `GET /api/v1/database/records` - Get data processing records from DB
- `GET /api/v1/database/records/{task_id}` - Get specific record
- `GET /api/v1/database/logs` - Get task logs from DB
- `DELETE /api/v1/database/records/{task_id}` - Delete record
- `GET /api/v1/docs` - Swagger UI (interactive API explorer - can test endpoints)
- `GET /api/v1/redoc` - ReDoc (clean documentation view)
- `GET /api/v1/openapi.json` - OpenAPI schema (JSON format)

**Container:**
- Container name: `fastapi-api`
- Image: `fastapi-starter-api`
- Port: 8000

### 2. Celery Worker (`api-celery`)

**Technology:** Celery, Redis

**Responsibilities:**
- Process asynchronous tasks from Redis queue
- Communicate with microservices via RabbitMQ
- Store task results in Redis

**Configuration:**
- Broker: Redis
- Result Backend: Redis
- Task Modules: `app.tasks.data`
- Container name: `fastapi-celery-worker`
- Image: `fastapi-starter-api` (same as backend service)

### 3. Data Service (`services/dataservice/`)

**Technology:** Python 3.x, kombu

**Responsibilities:**
- Listen to RabbitMQ queue (`data_queue`)
- Process incoming data requests
- Transform/validate data based on input type
- Return processed data via RabbitMQ RPC

**Key Files:**
- `main.py` - Service entry point
- `app/data_service.py` - Data processing logic
- `rabbitmq_client.py` - RabbitMQ client (EventReceiver)

**Processing Capabilities:**
- **String processing**: uppercase, reverse, or transform with prefix
- **Number processing**: square, double, or echo
- **List processing**: reverse, sort, or add metadata (count, items)
- **Dictionary processing**: add metadata (processed flag, keys count)
- **Generic data transformation**: handles any data type with metadata

**Container:**
- Container name: `data-service`
- Image: `data-service`

### 4. RabbitMQ (`rabbitmq/`)

**Technology:** RabbitMQ

**Responsibilities:**
- Message broker for inter-service communication
- Queue management for RPC pattern
- Message routing

**Configuration:**
- Port: 5672 (AMQP), 15672 (Management UI)
- User: `guest`
- Password: `welcome1`
- Default Queue: `data_queue`
- Container: `rabbitmq-service`

### 5. Redis (`redis`)

**Technology:** Redis 7

**Responsibilities:**
- Celery task broker
- Celery result backend
- Task state storage

**Configuration:**
- Port: 6379
- Database: 0
- Container: `redis`
- Image: `redis:7-alpine`

### 7. Observability (OpenTelemetry + SigNoz)

**Technology:** OpenTelemetry (OTel) in API, Celery, Data service; OTel Collector; SigNoz.

**Responsibilities:**
- Traces, metrics, and logs exported via OTLP to the Collector, then to SigNoz
- See `observability/README.md` and `docs/OBSERVABILITY_PLAN.md`. Logger service removed.

**Components:** OTel Collector (see docker-compose `otel-collector`); SigNoz run separately. Env: `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_SERVICE_NAME`.

The former **logger** HTTP service has been **removed**. Observability is via **OpenTelemetry** (traces, metrics, logs) to the OTel Collector and SigNoz. See `observability/README.md`.

### 8. Nginx (`nginx`)

**Technology:** Nginx

**Responsibilities:**
- Reverse proxy for API gateway
- Load balancing (when scaled)
- Request routing

**Configuration:**
- Host port: 8081 (container listens 8080)
- Routes to: FastAPI API (port 8000)
- Paths: `/api/v1/` and `/` (root)
- Proxy headers: Host, X-Real-IP, X-Forwarded-For, X-Forwarded-Proto
- Paths: `/api/v1/` and `/` (root)
- Proxy headers: Host, X-Real-IP, X-Forwarded-For, X-Forwarded-Proto

## Communication Patterns

### 1. Synchronous Processing (RPC Pattern)

```
Client → Nginx → FastAPI → EventProducer → RabbitMQ (data_queue)
→ Data Service (EventReceiver) → Processes → RabbitMQ (reply_to queue)
→ EventProducer (callback queue) → FastAPI → Client
```

**Flow:**
1. Client sends POST request to `/api/v1/data/process`
2. FastAPI creates EventProducer and sends message to RabbitMQ
3. EventProducer creates temporary callback queue
4. Data Service receives message from `data_queue`
5. Data Service processes data
6. Data Service sends response to callback queue
7. EventProducer receives response and returns to FastAPI
8. FastAPI returns response to client

**Duration:** ~2-5 seconds (blocking)

### 2. Asynchronous Processing (Celery + RabbitMQ)

```
Client → FastAPI → Celery Task → Redis → Worker → EventProducer 
→ RabbitMQ → Data Service → RabbitMQ → Worker → Redis → Client polls
```

**Flow:**
1. Client sends POST request to `/api/v1/data/process-async`
2. FastAPI creates Celery task and returns task ID immediately
3. Celery worker picks up task from Redis
4. Worker uses EventProducer to send message to RabbitMQ
5. Data Service processes and responds
6. Worker stores result in Redis
7. Client polls `/api/v1/data/process-async/{task_id}` for status
8. When ready, client receives result

**Duration:** Immediate response, processing in background

## Technology Stack

### Core Framework
- **FastAPI** 0.65.2 - Modern Python web framework
- **Python** 3.x - Programming language

### Task Processing
- **Celery** 4.4.7 - Distributed task queue
- **Redis** 7 - Message broker and result backend

### Messaging
- **kombu** 5.3.4 - Messaging library for RabbitMQ
- **RabbitMQ** - Message broker for inter-service communication

### Data Validation
- **Pydantic** 1.8.2 - Data validation using Python type hints

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Nginx** - Reverse proxy and load balancer
- **Kubernetes** - Container orchestration (optional)

## API Endpoints

### Root Endpoints
- `GET /` - API information
- `GET /health` - Health check

### Observability
- `GET /api/v1/metrics` - Queue depth (RabbitMQ) and RPC latency/timeouts (for backpressure tuning)

### Data Processing Endpoints

#### Synchronous Processing
```http
POST /api/v1/data/process
Content-Type: application/json

{
  "payload": "hello world",
  "description": "uppercase"
}
```

**Response:**
```json
{
  "task_id": "-",
  "task_status": "Success",
  "outcome": {
    "status": "success",
    "processed_at": "2024-01-01T12:00:00",
    "input": "hello world",
    "output": "HELLO WORLD",
    "metadata": {
      "input_length": 11,
      "processing_time_ms": 10
    }
  }
}
```

#### Asynchronous Processing
```http
POST /api/v1/data/process-async
Content-Type: application/json

{
  "payload": "hello world",
  "description": "reverse"
}
```

**Response:**
```json
{
  "task_id": "abc123-def456-ghi789",
  "task_status": "Processing",
  "outcome": null
}
```

#### Get Async Task Status
```http
GET /api/v1/data/process-async/{task_id}
```

**Response (Processing):**
```json
{
  "task_id": "abc123-def456-ghi789",
  "task_status": "Processing",
  "outcome": null
}
```

**Response (Complete):**
```json
{
  "task_id": "abc123-def456-ghi789",
  "task_status": "Success",
  "outcome": {
    "status": "success",
    "processed_at": "2024-01-01T12:00:00",
    "input": "hello world",
    "output": "dlrow olleh",
    "metadata": {...}
  }
}
```

## Deployment

### Local Development (Docker Compose)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

**Services:**
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/api/v1/docs (interactive - can test endpoints)
- ReDoc: http://localhost:8000/api/v1/redoc (clean documentation view)
- Nginx Gateway: http://localhost:8081
- PostgreSQL: localhost:5432, database **fastapi_db** (user fastapi)
- RabbitMQ Management: http://localhost:15672 (guest/welcome1)

**Container Names:**
- `fastapi-api` - FastAPI application
- `fastapi-celery-worker` - Celery worker
- `data-service` - Data processing microservice
- `rabbitmq-service` - RabbitMQ message broker
- `postgres` - PostgreSQL database
- `redis` - Redis for Celery

### Kubernetes Deployment

See `kubectl-setup.sh` for Kubernetes deployment instructions.

**Components:**
- RabbitMQ StatefulSet (in `rabbitmq/` directory)
- Backend Deployment (`backend/backend-pod.yaml` - to be created)
- Backend Celery Deployment (`backend/backend-celery-pod.yaml` - to be created)
- Backend Ingress (`backend/backend-ingress.yaml` - to be created)
- Data Service Deployment (can be created following the pattern in other services)

## Configuration

### Environment Variables

#### API Service
- `CELERY_BROKER_URL` - Redis broker URL (default: `redis://redis:6379/0`)
- `CELERY_RESULT_BACKEND` - Redis result backend (default: `redis://redis:6379/0`)
- `RABBITMQ_HOST` - RabbitMQ host (default: `rabbitmq`)
- `RABBITMQ_PORT` - RabbitMQ port (default: `5672`)
- `RABBITMQ_USER` - RabbitMQ username (default: `guest`)
- `RABBITMQ_PASSWORD` - RabbitMQ password (default: `welcome1`)
- `DATA_QUEUE_NAME` - Data service queue name (default: `data_queue`)

#### Data Service
- `RABBITMQ_HOST` - RabbitMQ host
- `RABBITMQ_PORT` - RabbitMQ port
- `RABBITMQ_USER` - RabbitMQ username
- `RABBITMQ_PASSWORD` - RabbitMQ password
- `QUEUE_NAME` - Queue name to listen to (default: `data_queue`)
- `SERVICE_NAME` - Service name (default: `data`)

## Scalability Considerations

### Horizontal Scaling

1. **API Service**: Scale by running multiple instances behind Nginx
2. **Celery Workers**: Add more worker instances for increased throughput
3. **Data Service**: Run multiple instances (RabbitMQ distributes messages)
4. **Redis**: Use Redis Cluster for high availability
5. **RabbitMQ**: Use RabbitMQ Cluster for high availability

### Performance Optimization

1. **Connection Pooling**: Reuse RabbitMQ connections
2. **Task Prioritization**: Use Celery priority queues
3. **Caching**: Add Redis caching layer for frequently accessed data
4. **Database**: Add database layer for persistent storage
5. **Monitoring**: Integrate Prometheus/Grafana for metrics

## Security Considerations

1. **Authentication**: Add JWT or OAuth2 authentication
2. **Authorization**: Implement role-based access control
3. **HTTPS**: Use TLS/SSL for all communications
4. **Secrets Management**: Use Kubernetes secrets or Vault
5. **Input Validation**: All inputs validated via Pydantic
6. **Rate Limiting**: Add rate limiting middleware
7. **CORS**: Configure CORS properly for production

## Monitoring and Observability

1. **OpenTelemetry + SigNoz**: Traces, metrics, logs (see `observability/README.md`)
2. **Health Checks**: `/health` endpoint for service health
3. **OpenAPI Docs**: Auto-generated API documentation
4. **Logging**: Structured logging across all services
5. **Metrics** (`GET /api/v1/metrics`): Observability for backpressure tuning:
   - **Queue depth**: RabbitMQ Management API — `data_queue`, `data_queue_dlq` (messages, messages_ready, messages_unacknowledged). Use when queue is growing to tune capacity or add producer backpressure.
   - **RPC**: In-memory stats — latency (count, avg, p50, p95 in seconds) and `timeouts_total`. Use to detect slow consumers and tune timeouts or concurrency.
6. **Tracing**: Add distributed tracing (Jaeger/Zipkin) as needed

## Adding New Microservices

To add a new microservice:

1. Create service folder under `services/`
2. Implement service class with `call()` method:
   ```python
   def call(self, data: str) -> tuple:
       # Process data
       response = {...}
       return json.dumps(response), task_type
   ```
3. Use `EventReceiver` from `rabbitmq_client.py`:
   ```python
   from rabbitmq_client import EventReceiver
   from app.your_service import YourService
   import os
   
   event_receiver = EventReceiver(
       username=os.getenv('RABBITMQ_USER', 'guest'),
       password=os.getenv('RABBITMQ_PASSWORD', 'welcome1'),
       host=os.getenv('RABBITMQ_HOST', 'rabbitmq'),
       port=int(os.getenv('RABBITMQ_PORT', '5672')),
       queue_name=os.getenv('QUEUE_NAME', 'your_service_queue'),
       service=YourService,
       service_name=os.getenv('SERVICE_NAME', 'your_service'),
   )
   event_receiver.run()
   ```
4. Add service to `docker-compose.yml`:
   ```yaml
   your-service:
     image: your-service
     build:
       context: ./services/yourservice
       dockerfile: Dockerfile
     container_name: your-service
     environment:
       - RABBITMQ_HOST=rabbitmq
       - RABBITMQ_PORT=5672
       - RABBITMQ_USER=guest
       - RABBITMQ_PASSWORD=welcome1
       - QUEUE_NAME=your_service_queue
       - SERVICE_NAME=your_service
       - OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
       - OTEL_SERVICE_NAME=your-service
     networks:
       - network1
     depends_on:
       - rabbitmq
       - otel-collector
   ```
5. Create API endpoint in `backend/app/api/v1/endpoints/your_service.py`:
   ```python
   from fastapi import APIRouter
   from app.models.schemas import DataRequest, TaskResult
   from app.core.dependencies import call_service, get_queue_name
   
   router = APIRouter(prefix='/your-service', tags=['your-service'])
   
   @router.post('/process', response_model=TaskResult)
   def process_data(request: DataRequest):
       queue_name = get_queue_name('your_service')
       response = call_service(
           queue_name=queue_name,
           payload=request.dict(),
           use_rabbitmq=True
       )
       return TaskResult(
           task_id='-',
           task_status='Success',
           outcome=response
       )
   ```
6. Add router to `backend/app/api/v1/__init__.py`:
   ```python
   from .endpoints import data, database, your_service
   api_router.include_router(your_service.router)
   ```

## File Structure

```
.
├── backend/                      # FastAPI application (Backend)
│   ├── app/
│   │   ├── api/                 # API layer
│   │   │   └── v1/
│   │   │       └── endpoints/   # Controllers - HTTP request handlers
│   │   │           ├── data.py  # Data processing endpoints
│   │   │           └── database.py  # Database query endpoints
│   │   ├── core/                # Core configuration
│   │   │   ├── database.py      # Database setup and session
│   │   │   └── dependencies.py  # Service communication helpers
│   │   ├── services/            # Business logic layer
│   │   │   └── data_service.py  # Data processing business logic
│   │   ├── repositories/        # Data access layer
│   │   │   ├── data_repository.py    # Data records repository
│   │   │   └── task_repository.py    # Task logs repository
│   │   ├── models/              # All data models
│   │   │   ├── schemas.py       # Pydantic models (API request/response)
│   │   │   └── database.py      # SQLModel database models
│   │   ├── tasks/               # Celery tasks
│   │   │   └── data.py          # Data processing tasks
│   │   └── infrastructure/      # Infrastructure code
│   │       ├── rabbitmq.py      # RabbitMQ client (EventProducer/EventReceiver)
│   │       └── celery.py        # Celery worker config
│   ├── main.py                  # FastAPI app entry point
│   ├── Dockerfile
│   └── requirements.txt
├── services/
│   └── dataservice/             # Data processing microservice
│       ├── app/
│       │   └── data_service.py   # Data processing logic
│       ├── main.py              # Service entry point
│       ├── rabbitmq_client.py   # RabbitMQ EventReceiver
│       ├── Dockerfile
│       └── requirements.txt
├── rabbitmq/                    # RabbitMQ configuration
│   ├── Dockerfile
│   └── *.yaml                  # Kubernetes configs
├── docker-compose.yml           # Local development setup
├── nginx_config.conf            # Nginx reverse proxy config
├── kubectl-setup.sh             # Kubernetes deployment script
├── kubectl-remove.sh            # Kubernetes cleanup script
├── ARCHITECTURE.md              # This file
└── SEQUENCE-DIAGRAMS.md         # Use case sequence diagrams
```

## Architecture Patterns

### MVC-like Structure

The backend follows an MVC-like pattern for clean separation of concerns:

1. **Controllers (Endpoints)**: `app/api/v1/endpoints/`
   - Handle HTTP requests and responses
   - Validate input using Pydantic models
   - Delegate business logic to services
   - Return appropriate HTTP status codes

2. **Services**: `app/services/`
   - Contain business logic
   - Orchestrate repositories and external services
   - Handle business rules and validations
   - Return domain objects

3. **Repositories**: `app/repositories/`
   - Handle all database operations
   - Abstract database access from services
   - Provide clean data access interface
   - Use SQLModel for type-safe queries

4. **Models**: `app/models/`
   - `schemas.py` - Pydantic models for API request/response validation
   - `database.py` - SQLModel models for database entities

5. **Core**: `app/core/`
   - `database.py` - Database configuration and session management
   - `dependencies.py` - Service communication helpers

6. **Infrastructure**: `app/infrastructure/`
   - `rabbitmq.py` - RabbitMQ client (EventProducer/EventReceiver)
   - `celery.py` - Celery worker configuration

7. **Tasks**: `app/tasks/`
   - Celery task definitions organized by domain

**Example Flow:**
```
HTTP Request → Endpoint (Controller) → Service (Business Logic) → Repository (Data Access) → Database
```

**Import Style:**
All imports use absolute imports from the `app` package:
```python
from app.models.schemas import DataRequest
from app.core.database import get_session
from app.services.data_service import DataService
from app.repositories.data_repository import DataRepository
```

**Code Quality & PEP 8:**
The project strictly follows [PEP 8](https://pep8.org/) style guidelines with automated enforcement:

- **Black** - Code formatter (88 character line length)
- **isort** - Import sorter (groups: stdlib, third-party, local)
- **flake8** - Linter for PEP 8 compliance
- **Pre-commit hooks** - Automatic checks before commits
- **CI/CD integration** - Automated checks in GitHub Actions

See [PEP8_STYLE_GUIDE.md](../PEP8_STYLE_GUIDE.md) for complete style guide and tool configuration.

**Running Code Quality Checks:**
```bash
# Format code
make format

# Check code quality
make check

# Install development tools
make install-dev
```

## Key Design Decisions

1. **MVC-like Architecture**: Clean separation of controllers, services, and repositories
2. **kombu over pika**: Using industry-standard kombu library instead of custom pika implementation
3. **Redis + RabbitMQ**: Redis for Celery, RabbitMQ for inter-service communication
4. **PostgreSQL + SQLModel**: PostgreSQL for persistent storage with SQLModel ORM (by FastAPI creator)
5. **RPC Pattern**: Synchronous service calls using RabbitMQ RPC pattern
6. **Celery for Async**: Asynchronous processing using Celery with Redis
7. **Microservices**: Modular service architecture for scalability
8. **Observability**: OpenTelemetry (OTel) and SigNoz for traces, metrics, logs
9. **No Skipper Dependencies**: Removed all Skipper-specific code and dependencies

## Database Layer

### SQLModel ORM (not raw SQLAlchemy)

The starter kit uses **SQLModel** as the ORM, not raw SQLAlchemy. SQLModel is a thin layer on top of SQLAlchemy and Pydantic: you define **SQLModel** models (e.g. `class DataProcessingRecord(SQLModel, table=True)`), and SQLModel handles table mapping, validation, and session APIs. Under the hood it uses SQLAlchemy for the engine/session and Pydantic for validation. So we use **SQLModel for the ORM**; the async engine and session types come from SQLAlchemy’s async support, which SQLModel is designed to work with (and in SQLModel 0.0.32+ via `sqlmodel.ext.asyncio.session.AsyncSession`).

**Why you still see SQLAlchemy imports:** Yes, some `sqlalchemy` imports are expected. SQLModel does not replace SQLAlchemy; it builds on it.

| Where | Import | Why |
|-------|--------|-----|
| `app/core/database.py` | `create_async_engine`, `async_sessionmaker` from `sqlalchemy.ext.asyncio` | SQLModel does not provide async engine creation; we use SQLAlchemy’s async engine and then pass it to SQLModel’s `AsyncSession` class. |
| `app/models/database.py` | `func` from `sqlalchemy` | Used for `server_default=func.now()` and `onupdate=func.now()` on timestamp columns. SQLAlchemy’s SQL function helper; standard in SQLModel models for DB-side timestamps. |

Everything else (models, `Session`, `create_engine`, `select`, `AsyncSession`, `Column`, `Field`, etc.) comes from **SQLModel**. So: **ORM and API = SQLModel**; **async engine + session factory + `func` = SQLAlchemy**, by design.

**Benefits:**
- Type-safe database models
- Automatic API documentation
- Validation using Pydantic
- SQLAlchemy power with Pydantic simplicity

### SQLModel version and async (0.0.32+)

We use **SQLModel 0.0.32 or above**. Async is the standard, supported approach:

- **SQLModel 0.0.32+** includes `sqlmodel.ext.asyncio.session.AsyncSession` and is built for async (e.g. with FastAPI and `asyncpg`).
- The async flow: `create_async_engine` (SQLAlchemy) with `postgresql+asyncpg://...`, then **SQLModel’s** `AsyncSession` from `sqlmodel.ext.asyncio.session` so you get SQLModel’s `exec()` and behavior. Connection pooling is configured on the async engine (`pool_size`, `max_overflow`, `pool_pre_ping`).
- So: **ORM = SQLModel**; **async engine/session** = SQLAlchemy async + SQLModel’s `AsyncSession` (0.0.32+).

### Why the Celery task uses the sync engine and inserts directly

- **Celery workers run in separate processes**, not inside FastAPI’s async event loop. They execute plain synchronous Python. Using `AsyncSession` and `await` would require running an event loop inside the task (e.g. `asyncio.run()`), which complicates worker concurrency and is not the usual pattern for Celery.
- **Sync engine + `Session`** is the standard approach for background workers: the worker gets a connection from the **sync** pool and does a short-lived transaction. No async is needed.
- We **insert the record directly** (e.g. `DataProcessingRecord(...)`, `session.add()`, `session.commit()`) in the Celery task instead of calling the async `DataRepository` because:
  - The **repositories were converted to async-only** (they take `AsyncSession` and use `await`). Reusing them from the sync Celery task would require either a duplicate sync repository or running async code inside the task.
  - A small, explicit insert in the task keeps the worker simple and avoids maintaining two repository implementations. So: **Celery = sync process → sync engine → sync `Session` → direct model add/commit** (no async repository).

### Database Models

1. **DataProcessingRecord** - Stores data processing requests and outcomes
   - Fields: id, task_id, payload, description, task_type, task_status, outcome, created_at, updated_at

2. **TaskLog** - Stores task execution logs with correlation IDs (queryable via `GET /api/v1/database/logs`). Producer start/end events from the sync RPC path are written to this table via `EventProducer`'s `on_log_event` callback.
   - Fields: id, task_id, correlation_id, queue_name, service_name, task_type, description, status, created_at

### Connection Pool and Non-Blocking Async DB

The starter kit uses **connection pooling** and **non-blocking async** database access for the FastAPI API:

- **Sync engine** (`engine`): Used for `init_db()` at startup and for the **Celery worker** (separate process). Pool: `pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`.
- **Async engine** (`async_engine`): Used for **FastAPI request handlers** so DB I/O does not block the event loop. Same pool settings. Driver: **asyncpg** (`postgresql+asyncpg://...`).
- **Session per request**: `get_async_session()` yields an `AsyncSession` from the pool; repositories use `await session.commit()`, `await session.execute(select(...))`, etc.

**Environment:** Set `DATABASE_URL` (sync, psycopg2). Optional `ASYNC_DATABASE_URL` (defaults to `DATABASE_URL` with `postgresql+asyncpg://`). Set `SQL_ECHO=true` to log SQL (dev only).

### Using the Database

**In API Endpoints (async, non-blocking):**
```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_session
from app.services.data_service import DataService

@router.get("/records")
async def get_records(service: DataService = Depends(get_data_service)):
    records = await service.get_processing_records(limit=10, offset=0)
    return [r.model_dump() for r in records]
```

**Creating records (async):** Use `DataRepository.create_record()` with an `AsyncSession`; the repository calls `await self.session.commit()` and `await self.session.refresh(record)`.

**Querying (async):**
```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

stmt = select(DataProcessingRecord).where(DataProcessingRecord.task_id == "123")
result = await session.execute(stmt)
record = result.scalar_one_or_none()
```

**Celery worker:** Uses the **sync** `engine` and `Session(engine)` (no async) so the worker process does not require an event loop.

### Database Migrations

Alembic is configured under `backend/` (see [backend/alembic/README.md](backend/alembic/README.md)). The database name is **`fastapi_db`** (not `fastapi`).

```bash
cd backend
# Apply migrations (ensure DATABASE_URL uses fastapi_db)
alembic upgrade head

# Create a new migration after changing app.models.database
alembic revision --autogenerate -m "Describe change"
alembic upgrade head
```

From Docker: `docker compose run --rm api alembic upgrade head`

## Future Enhancements

1. **Authentication**: Implement JWT/OAuth2 authentication
3. **API Gateway**: Enhanced API gateway with rate limiting, caching
4. **Service Mesh**: Consider Istio/Linkerd for advanced service communication
5. **Event Sourcing**: Add event sourcing for audit trails
6. **GraphQL**: Add GraphQL endpoint alongside REST
7. **WebSockets**: Real-time updates via WebSockets
8. **Testing**: Comprehensive test suite (unit, integration, e2e)

## Sequence Diagrams

For detailed sequence diagrams of all use cases, see [SEQUENCE-DIAGRAMS.md](./SEQUENCE-DIAGRAMS.md).

The sequence diagrams document includes:
- Synchronous data processing flow
- Asynchronous task creation and polling
- Event logging and observability
- Error handling scenarios
- Health check flow

## License

Licensed under the Apache License, Version 2.0.
