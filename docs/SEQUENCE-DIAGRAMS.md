# FastAPI Starter Kit - Sequence Diagrams

This document provides detailed sequence diagrams for all use cases in the FastAPI Starter Kit architecture.

**Note**: 
- All code references use the current structure with absolute imports from the `app` package (e.g., `app.models.schemas`, `app.services.data_service`).
- "Client" in these diagrams refers to external API clients (web applications, mobile apps, other services, Postman, curl, etc.). This project is API-only and does not include a frontend application.

## Use Case 1: Synchronous Data Processing

**Endpoint:** `POST /api/v1/data/process`

This use case demonstrates synchronous data processing using RabbitMQ RPC pattern. The client waits for the response.

### Sequence Diagram

```
┌──────┐    ┌──────┐    ┌──────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│Client│    │Nginx │    │FastAPI│    │EventProd │    │ RabbitMQ │    │DataSvc   │    │  Logger  │
└───┬──┘    └───┬──┘    └───┬──┘    └────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘
    │           │           │            │               │               │               │
    │──POST /api/v1/data/process────────>│               │               │               │
    │           │           │            │               │               │               │
    │           │           │──Validate Request────────>│               │               │
    │           │           │            │               │               │               │
    │           │           │──Create EventProducer─────>│               │               │
    │           │           │            │               │               │               │
    │           │           │            │──Create callback queue───────>│               │
    │           │           │            │<──callback_queue: amq.gen-xyz─│               │
    │           │           │            │               │               │               │
    │           │           │            │──Start listening on callback──>│               │
    │           │           │            │               │               │               │
    │           │           │            │──Publish to data_queue─────────>│               │
    │           │           │            │  (reply_to: amq.gen-xyz)       │               │
    │           │           │            │  (correlation_id: uuid-1234)    │               │
    │           │           │            │               │               │               │
    │           │           │            │               │──Log Producer Event───────────>│
    │           │           │            │               │               │               │
    │           │           │            │               │──Route to data_queue──────────>│
    │           │           │            │               │               │               │
    │           │           │            │               │               │──Receive message
    │           │           │            │               │               │──Log Receiver Event──>│
    │           │           │            │               │               │               │
    │           │           │            │               │               │──Process data
    │           │           │            │               │               │  (transform, validate)
    │           │           │            │               │               │               │
    │           │           │            │               │<──Publish response─────────────│
    │           │           │            │               │  (to: amq.gen-xyz)            │
    │           │           │            │               │  (correlation_id: uuid-1234) │
    │           │           │            │               │               │               │
    │           │           │            │               │──Log Receiver Event───────────>│
    │           │           │            │               │               │               │
    │           │           │            │<──Receive response on callback───────────────│
    │           │           │            │  (matched by correlation_id)                  │
    │           │           │            │               │               │               │
    │           │           │            │──Log Producer Event───────────────────────────>│
    │           │           │            │               │               │               │
    │           │           │<──Return response─────────│               │               │
    │           │           │            │               │               │               │
    │<──200 OK───────────────│            │               │               │               │
    │  {task_id, status,     │            │               │               │               │
    │   outcome}             │            │               │               │               │
    │           │           │            │               │               │               │
```

### Step-by-Step Flow

1. **Client Request**
   - Client sends POST request to `/api/v1/data/process` with payload
   - Request goes through Nginx to FastAPI

2. **Request Validation**
   - FastAPI validates request using Pydantic `DataRequest` model (`app.models.schemas`)
   - Extracts `payload` and `description`
   - Controller (`app.api.v1.endpoints.data`) delegates to service

3. **Service Layer**
   - `DataService` (`app.services.data_service`) handles business logic
   - Uses `EventProducer` from `app.infrastructure.rabbitmq`
   - Connects to RabbitMQ
   - Creates temporary exclusive callback queue (e.g., `amq.gen-abc123`)
   - Starts listening on callback queue for response

4. **Message Publishing**
   - EventProducer publishes message to `data_queue` with:
     - `routing_key`: `data_queue`
     - `reply_to`: callback queue name
     - `correlation_id`: unique UUID
     - `body`: JSON payload
   - Logs producer event to logger service

5. **Message Routing**
   - RabbitMQ routes message to `data_queue`
   - Data Service's EventReceiver receives message

6. **Data Processing**
   - Data Service logs receiver event start
   - Creates `DataService` instance
   - Calls `data_service.call(body)` with JSON string
   - Processes data based on type and description:
     - String: uppercase, reverse, or transform
     - Number: square, double, or echo
     - List: reverse, sort, or add metadata
     - Dict: add metadata
   - Returns processed data as JSON string

7. **Response Publishing**
   - Data Service publishes response to callback queue:
     - `routing_key`: `reply_to` from original message
     - `correlation_id`: same as request
     - `body`: processed data JSON
   - Logs receiver event end

8. **Response Reception**
   - EventProducer receives response on callback queue
   - Matches response by `correlation_id`
   - Extracts response body
   - Logs producer event end

9. **Client Response**
   - FastAPI returns `TaskResult` with:
     - `task_id`: "-" (synchronous, no task ID)
     - `task_status`: "Success"
     - `outcome`: processed data

---

## Use Case 2: Asynchronous Data Processing (Start Task)

**Endpoint:** `POST /api/v1/data/process-async`

This use case demonstrates asynchronous data processing. The client receives a task ID immediately and can poll for results.

### Sequence Diagram

```
┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐    ┌──────────┐
│Client│    │Nginx │    │FastAPI│    │Redis │    │Worker│    │RabbitMQ│   │DataSvc   │
└───┬──┘    └───┬──┘    └───┬──┘    └───┬──┘    └───┬──┘    └───┬──┘    └────┬─────┘
    │           │           │            │           │           │            │
    │──POST /api/v1/data/process-async───>│           │           │            │
    │           │           │            │           │           │            │
    │           │           │──Validate Request────────>│           │            │
    │           │           │            │           │           │            │
    │           │           │──Create Celery Task───────>│           │            │
    │           │           │  (task_id: abc123)        │           │            │
    │           │           │            │           │           │            │
    │<──202 Accepted─────────│            │           │           │            │
    │  {task_id: abc123,      │            │           │           │            │
    │   status: Processing}   │            │           │           │            │
    │           │           │            │           │           │            │
    │           │           │            │           │           │            │
    │           │           │            │<──Pick up task──────────│            │
    │           │           │            │           │           │            │
    │           │           │            │           │──Create EventProducer──>│
    │           │           │            │           │           │            │
    │           │           │            │           │──Publish to data_queue──>│
    │           │           │            │           │           │            │
    │           │           │            │           │           │──Receive message
    │           │           │            │           │           │──Process data
    │           │           │            │           │           │            │
    │           │           │            │           │<──Response───────────────│
    │           │           │            │           │           │            │
    │           │           │            │<──Store result──────────────────────│
    │           │           │            │  (task_id: abc123)                  │
    │           │           │            │           │           │            │
```

### Step-by-Step Flow

1. **Client Request**
   - Client sends POST request to `/api/v1/data/process-async`
   - Request includes payload and description

2. **Task Creation**
   - FastAPI validates request using `app.models.schemas.DataRequest`
   - Controller (`app.api.v1.endpoints.data`) delegates to `DataService`
   - Service creates Celery task: `app.tasks.data.process_data_task.delay(payload_json)`
   - Celery generates unique task ID (e.g., `abc123-def456-ghi789`)
   - Task is queued in Redis

3. **Immediate Response**
   - FastAPI returns `202 Accepted` immediately with:
     - `task_id`: generated task ID
     - `task_status`: "Processing"
     - `outcome`: null

4. **Background Processing**
   - Celery worker (`app.infrastructure.celery`) picks up task from Redis queue
   - Worker executes `app.tasks.data.process_data_task`
   - Worker creates `EventProducer` instance (`app.infrastructure.rabbitmq`)
   - Worker sends message to RabbitMQ `data_queue`
   - Data Service receives and processes message
   - Data Service sends response back
   - Worker receives response and stores result in Redis with task ID

---

## Use Case 3: Get Asynchronous Task Status

**Endpoint:** `GET /api/v1/data/process-async/{task_id}`

This use case allows clients to poll for the status and result of an asynchronous task.

### Sequence Diagram

```
┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐
│Client│    │Nginx │    │FastAPI│    │Redis │
└───┬──┘    └───┬──┘    └───┬──┘    └───┬──┘
    │           │           │            │
    │──GET /api/v1/data/process-async/abc123──>│            │
    │           │           │            │
    │           │           │──Get AsyncResult───────────>│
    │           │           │  (task_id: abc123)         │
    │           │           │            │               │
    │           │           │            │──Check task status
    │           │           │            │               │
    │           │           │            │<──Return status───│
    │           │           │            │  (ready: false)   │
    │           │           │            │               │
    │           │           │<──Task not ready────────────│
    │           │           │            │               │
    │<──202 Processing───────│            │               │
    │  {task_id, status:      │            │               │
    │   Processing,           │            │               │
    │   outcome: null}        │            │               │
    │           │           │            │               │
    │           │           │            │               │
    │           │           │            │               │
    │──GET /api/v1/data/process-async/abc123──>│            │
    │           │           │            │               │
    │           │           │──Get AsyncResult───────────>│
    │           │           │            │               │
    │           │           │            │──Check task status
    │           │           │            │  (ready: true)   │
    │           │           │            │               │
    │           │           │            │──Get result─────>│
    │           │           │            │               │
    │           │           │            │<──Return result─│
    │           │           │            │  (processed data)│
    │           │           │            │               │
    │           │           │<──Task result───────────────│
    │           │           │            │               │
    │<──200 Success──────────│            │               │
    │  {task_id, status:     │            │               │
    │   Success,              │            │               │
    │   outcome: {...}}       │            │               │
    │           │           │            │               │
```

### Step-by-Step Flow

1. **Client Poll Request**
   - Client sends GET request to `/api/v1/data/process-async/{task_id}`
   - FastAPI extracts task ID from URL

2. **Task Status Check**
   - Controller (`app.api.v1.endpoints.data`) receives request
   - Service (`app.services.data_service`) creates `AsyncResult(task_id)` from Celery
   - Queries Redis for task status via Celery result backend

3. **Response Scenarios**

   **Scenario A: Task Still Processing**
   - `task.ready()` returns `False`
   - FastAPI returns `202 Accepted` with:
     - `task_id`: task ID
     - `task_status`: "Processing"
     - `outcome`: null
   - Client should poll again

   **Scenario B: Task Completed**
   - `task.ready()` returns `True`
   - `task.get()` retrieves result from Redis
   - FastAPI returns `200 OK` with:
     - `task_id`: task ID
     - `task_status`: "Success"
     - `outcome`: processed data

   **Scenario C: Task Failed**
   - `task.failed()` returns `True`
   - FastAPI returns `500 Internal Server Error` with error details

---

## Use Case 4: Logger Service Event Tracking

This use case shows how the logger service tracks events across the system for observability.

### Sequence Diagram - Producer Event

```
┌──────────┐    ┌──────────┐    ┌──────────┐
│EventProd │    │ RabbitMQ │    │  Logger  │
└────┬─────┘    └────┬─────┘    └────┬─────┘
     │               │               │
     │──Publish message─────────────>│
     │               │               │
     │──Log Producer Event───────────>│
     │  POST /api/v1/logger/log_producer
     │  {
     │    correlation_id: uuid-1234,
     │    queue_name: data_queue,
     │    service_name: api_sync,
     │    task_type: start,
     │    description: "-"
     │  }
     │               │               │
     │               │               │──Log event
     │               │               │  (background task)
     │               │               │
     │<──200 OK──────────────────────│
     │               │               │
```

### Sequence Diagram - Receiver Event

```
┌──────────┐    ┌──────────┐    ┌──────────┐
│DataSvc   │    │ RabbitMQ │    │  Logger  │
└────┬─────┘    └────┬─────┘    └────┬─────┘
     │               │               │
     │<──Receive message──────────────│
     │               │               │
     │──Log Receiver Event Start─────>│
     │  POST /api/v1/logger/log_receiver
     │  {
     │    correlation_id: uuid-1234,
     │    queue_name: data_queue,
     │    service_name: data,
     │    task_type: start,
     │    description: "-"
     │  }
     │               │               │
     │               │               │──Log event
     │               │               │
     │<──200 OK──────────────────────│
     │               │               │
     │──Process data                 │
     │               │               │
     │──Log Receiver Event End──────>│
     │  POST /api/v1/logger/log_receiver
     │  {
     │    correlation_id: uuid-1234,
     │    queue_name: data_queue,
     │    service_name: data,
     │    task_type: end,
     │    description: "-"
     │  }
     │               │               │
     │               │               │──Log event
     │               │               │
     │<──200 OK──────────────────────│
     │               │               │
```

### Step-by-Step Flow

1. **Producer Event Logging**
   - When EventProducer publishes a message, it logs:
     - `correlation_id`: unique request ID
     - `queue_name`: target queue
     - `service_name`: producer service name
     - `task_type`: "start" or "end"
     - `description`: optional description
   - Logs are sent asynchronously (non-blocking)

2. **Receiver Event Logging**
   - When EventReceiver receives a message, it logs:
     - `correlation_id`: from message properties
     - `queue_name`: queue name
     - `service_name`: receiver service name
     - `task_type`: "start" (on receive) or "end" (on complete)
     - `description`: optional description or error message
   - Logs are sent asynchronously (non-blocking)

3. **Event Tracking Benefits**
   - Track request flow across services
   - Debug issues using correlation IDs
   - Monitor service performance
   - Audit trail for all operations

---

## Use Case 5: Error Handling

This use case demonstrates error handling scenarios.

### Sequence Diagram - Service Unavailable

```
┌──────┐    ┌──────┐    ┌──────────┐    ┌──────────┐
│Client│    │FastAPI│    │EventProd │    │ RabbitMQ │
└───┬──┘    └───┬──┘    └────┬─────┘    └────┬─────┘
    │           │            │               │
    │──POST /api/v1/data/process──>│            │               │
    │           │            │               │
    │           │            │──Publish to data_queue──>│
    │           │            │               │               │
    │           │            │               │──No consumer available
    │           │            │               │               │
    │           │            │<──Timeout/Error─────────────│
    │           │            │               │               │
    │           │            │──Return error───────────────>│
    │           │            │  {error: "No subscriber available"}│
    │           │            │               │               │
    │           │<──Error response───────────│               │
    │           │            │               │               │
    │<──503 Service Unavailable─────────────│               │
    │  {error: "No subscriber available"}    │               │
    │           │            │               │               │
```

### Sequence Diagram - Processing Error

```
┌──────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│Client│    │DataSvc   │    │ RabbitMQ │    │EventProd │
└───┬──┘    └────┬─────┘    └────┬─────┘    └────┬─────┘
    │           │               │               │
    │           │<──Receive message───────────────│
    │           │               │               │
    │           │──Process data                  │
    │           │  (exception occurs)            │
    │           │               │               │
    │           │──Catch exception               │
    │           │──Create error response         │
    │           │  {
    │           │    error: "Receiver exception",
    │           │    queue: data_queue,
    │           │    service_name: data,
    │           │    correlation_id: uuid-1234,
    │           │    exception: "Invalid input"
    │           │  }
    │           │               │               │
    │           │──Publish error response───────>│
    │           │               │               │
    │           │               │──Route to callback──>│
    │           │               │               │
    │           │               │               │<──Receive error
    │           │               │               │
    │<──503 Service Unavailable───────────────────│
    │  {error: "Receiver exception: Invalid input"}│
    │           │               │               │
```

### Error Scenarios

1. **No Service Available**
   - RabbitMQ queue has no consumers
   - EventProducer returns: `{"error": "No subscriber available"}`
   - FastAPI returns: `503 Service Unavailable`

2. **Processing Error**
   - Data Service encounters exception during processing
   - Service catches exception and returns error response
   - Error includes: error message, queue name, service name, correlation ID, exception details
   - FastAPI returns: `503 Service Unavailable` with error details

3. **Timeout**
   - Response not received within timeout period (default: 300 seconds)
   - EventProducer returns: `{"error": "Request timeout"}`
   - FastAPI returns: `503 Service Unavailable`

4. **Invalid Request**
   - Pydantic validation fails (`app.models.schemas.DataRequest`)
   - FastAPI returns: `422 Unprocessable Entity` with validation errors

5. **Task Not Found**
   - Async task ID doesn't exist in Redis
   - FastAPI returns: `404 Not Found`

---

## Use Case 6: Health Check

**Endpoint:** `GET /health`

Simple health check endpoint to verify service availability.

### Sequence Diagram

```
┌──────┐    ┌──────┐    ┌──────┐
│Client│    │Nginx │    │FastAPI│
└───┬──┘    └───┬──┘    └───┬──┘
    │           │           │
    │──GET /health─────────>│
    │           │           │
    │           │           │──Check service status
    │           │           │               │
    │           │           │<──Status: healthy
    │           │           │               │
    │<──200 OK───────────────│
    │  {status: "healthy"}   │
    │           │           │
```

### Step-by-Step Flow

1. **Client Request**
   - Client sends GET request to `/health`

2. **Health Check**
   - FastAPI checks service status
   - Returns simple JSON response

3. **Response**
   - `200 OK` with `{"status": "healthy"}`

---

## Summary

These sequence diagrams cover all major use cases:

1. ✅ **Synchronous Processing** - Direct RPC pattern via RabbitMQ
   - Flow: Client → Nginx → FastAPI → DataService → EventProducer → RabbitMQ → Data Service
   - Uses: `app.api.v1.endpoints.data`, `app.services.data_service`, `app.infrastructure.rabbitmq`

2. ✅ **Asynchronous Processing (Start)** - Celery task creation
   - Flow: Client → FastAPI → DataService → Celery Task → Redis → Worker
   - Uses: `app.tasks.data.process_data_task`, `app.infrastructure.celery`

3. ✅ **Asynchronous Processing (Status)** - Polling for task results
   - Flow: Client → FastAPI → DataService → Celery AsyncResult → Redis
   - Uses: `app.services.data_service.get_task_status()`

4. ✅ **Event Logging** - Observability tracking
   - Flow: EventProducer/EventReceiver → Logger Service
   - Uses: `app.infrastructure.rabbitmq` for logging events

5. ✅ **Error Handling** - Various error scenarios
   - Handles: Service unavailable, processing errors, timeouts, validation errors
   - Uses: Pydantic validation (`app.models.schemas`), error responses

6. ✅ **Health Check** - Service availability check
   - Endpoint: `GET /health`
   - Simple status check

Each diagram shows the complete flow of messages and interactions between components, making it easy to understand the system behavior and debug issues.

## Architecture Components

The diagrams reference the following components from the `backend/app/` structure:

- **Controllers**: `app.api.v1.endpoints.*` - Handle HTTP requests/responses
- **Services**: `app.services.*` - Business logic layer
- **Repositories**: `app.repositories.*` - Data access layer
- **Models**: `app.models.schemas` (Pydantic), `app.models.database` (SQLModel)
- **Infrastructure**: `app.infrastructure.rabbitmq`, `app.infrastructure.celery`
- **Tasks**: `app.tasks.*` - Celery task definitions
- **Core**: `app.core.database`, `app.core.dependencies` - Configuration and helpers
