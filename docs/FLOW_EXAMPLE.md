# Data Processing Flows – Synchronous vs Asynchronous

This document walks through **one example** for both the **synchronous** and **asynchronous** data processing flows using the same sample payload.

**Example request body (used for both flows):**

```json
{
  "payload": "hello world",
  "description": "uppercase"
}
```

**Base URL (via Nginx):** `http://localhost:8080` → API at `http://api:8000`  
**API prefix:** `/api/v1`

---

## 1. Synchronous flow

**Endpoint:** `POST /api/v1/data/process`

The client sends the request and **waits** until the result is ready. The response is returned in the same HTTP response.

### Step-by-step (example)

| Step | Component | What happens |
|------|-----------|--------------|
| 1 | **Client** | Sends `POST /api/v1/data/process` with body `{"payload": "hello world", "description": "uppercase"}`. |
| 2 | **Nginx** | Proxies to FastAPI at `http://api:8000/api/v1/data/process`. |
| 3 | **FastAPI (Controller)** | `app.api.v1.endpoints.data.process_data()` receives the request, validates it with `DataRequest`, and calls `DataService.process_data_sync()`. |
| 4 | **DataService** | Builds payload `{payload, description, task_type: "data"}`, calls `call_service(queue_name="data_queue", ..., use_rabbitmq=True)`. |
| 5 | **EventProducer (API)** | Creates a temporary callback queue, publishes to RabbitMQ `data_queue` with `reply_to` and `correlation_id`, and **blocks** listening on the callback queue. Optionally logs to Logger service. |
| 6 | **RabbitMQ** | Routes the message to `data_queue`. |
| 7 | **Data Service (microservice)** | EventReceiver consumes from `data_queue`, calls `DataService.call(body)` (e.g. uppercase "hello world" → "HELLO WORLD"), publishes the result back to the callback queue with the same `correlation_id`. |
| 8 | **EventProducer (API)** | Receives the response on the callback queue, matches by `correlation_id`, returns the parsed JSON to `call_service()`. |
| 9 | **DataService** | Gets response (e.g. `{"result": "HELLO WORLD"}`). If `"error"` in response, raises `ValueError`. Otherwise calls `data_repo.create_record(...)` and persists a row in **PostgreSQL** (task_id "-", status "Success", outcome). Producer "start" and "end" events are also written to **task_logs** via `EventProducer`'s `on_log_event` callback. |
| 10 | **Controller** | Returns `200 OK` with body e.g. `{"task_id": "-", "task_status": "Success", "outcome": {"result": "HELLO WORLD"}}`. |
| 11 | **Client** | Receives the final result in the same HTTP response. |

### Summary

- **Same HTTP request/response:** client waits until processing is done.
- **Path:** Client → Nginx → FastAPI → EventProducer → RabbitMQ → Data Service → back through RabbitMQ to API → **PostgreSQL (record created)** → response to client.
- **Use when:** You need the result immediately in the same call.

---

## 2. Asynchronous flow

**Endpoints:**

- **Start task:** `POST /api/v1/data/process-async`
- **Get status/result:** `GET /api/v1/data/process-async/{task_id}`

The client gets a **task ID** immediately and can **poll** for status and result later.

### 2.1 Start async task

| Step | Component | What happens |
|------|-----------|--------------|
| 1 | **Client** | Sends `POST /api/v1/data/process-async` with body `{"payload": "hello world", "description": "uppercase"}`. |
| 2 | **Nginx** | Proxies to FastAPI. |
| 3 | **FastAPI (Controller)** | `process_data_async()` validates with `DataRequest`, calls `DataService.process_data_async()`. |
| 4 | **DataService** | Calls `process_data_task.delay(json.dumps({payload, description}))`. Celery enqueues the task in **Redis** and returns an `AsyncResult` with a task ID (e.g. `abc-123-def`). |
| 5 | **Controller** | Returns **202 Accepted** immediately with e.g. `{"task_id": "abc-123-def", "task_status": "Processing", "outcome": null}`. |
| 6 | **Client** | Receives 202 and the `task_id`; no outcome yet. |

**No database write at this step.** The actual processing runs in the background.

### 2.2 Background processing (Celery worker)

| Step | Component | What happens |
|------|-----------|--------------|
| 7 | **Celery worker** | Picks the task from Redis and runs `app.tasks.data.process_data_task(payload_json)`. |
| 8 | **process_data_task** | Parses payload, creates `EventProducer`, calls `event_producer.call("data_queue", payload)`: same RabbitMQ RPC pattern as sync (publish to `data_queue`, wait on callback queue). |
| 9 | **RabbitMQ → Data Service** | Same as sync: Data Service consumes, processes (e.g. uppercase), publishes response to callback queue. |
| 10 | **Celery task** | Receives response, then **persists a row to PostgreSQL** via `DataRepository.create_record` (task_id = Celery task ID, task_status "Success", outcome). Returns result; Celery also stores the **result in Redis** under the task ID. |
| 11 | **Client** | Can poll `GET /api/v1/data/process-async/abc-123-def` to get status and outcome. The same task can be found in the DB (e.g. via `GET /api/v1/database/records` or by task_id). |

### 2.3 Poll for result

| Step | Component | What happens |
|------|-----------|--------------|
| 12 | **Client** | Sends `GET /api/v1/data/process-async/abc-123-def`. |
| 13 | **FastAPI** | `get_data_task_status(task_id)` uses `DataService.get_task_status(task_id)` → `AsyncResult(task_id)`. |
| 14 | **DataService** | If `not task.ready()` → returns `{"task_id": "...", "task_status": "Processing", "outcome": null}` → API returns **202**. If `task.failed()` → raises; if ready, `task.get()` from Redis and returns `{"task_id": "...", "task_status": "Success", "outcome": {...}}`. |
| 15 | **Client** | Receives either 202 (still processing) or 200 with full outcome. |

### Summary

- **Two phases:** (1) Start task → 202 + `task_id`. (2) Poll `GET .../process-async/{task_id}` until 200 with outcome.
- **Path (start):** Client → Nginx → FastAPI → Celery (enqueue in Redis) → 202 to client.  
- **Path (background):** Celery worker → EventProducer → RabbitMQ → Data Service → response back to worker → **PostgreSQL** (record created with Celery task_id, status, outcome) and result stored in **Redis**.  
- **Path (poll):** Client → FastAPI → `AsyncResult(task_id)` → Redis → 202 or 200 to client.
- **DB integration:** Async path **does** create a row in PostgreSQL when the task completes (`app.tasks.data.process_data_task` calls `DataRepository.create_record` with the Celery task ID). On failure, a record with `task_status="Failed"` is also persisted.
- **Use when:** You want to avoid blocking the client and can poll or use webhooks later.

---

## Idempotency

Clients may send an optional **`Idempotency-Key`** header (e.g. a UUID) on `POST /api/v1/data/process` and `POST /api/v1/data/process-async`. The API stores the response in Redis under that key (1h TTL). A duplicate request with the same key returns the stored response without re-running processing.

---

## Quick comparison

| Aspect | Synchronous | Asynchronous |
|--------|-------------|-------------|
| **Endpoint** | `POST /api/v1/data/process` | `POST /api/v1/data/process-async` then `GET /api/v1/data/process-async/{task_id}` |
| **Response** | 200 with result in same response | 202 with `task_id`; result via polling |
| **Processing** | Same process (API) → RabbitMQ → Data Service | Celery worker → RabbitMQ → Data Service |
| **Result storage** | PostgreSQL (via `DataRepository.create_record`) | Redis (Celery backend) + PostgreSQL (record created by Celery task on completion/failure) |
| **Blocking** | Client blocks until done | Client returns immediately; worker runs in background |

---

## Example cURL commands

**Synchronous (wait for result):**

```bash
curl -X POST http://localhost:8080/api/v1/data/process \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: optional-uuid" \
  -d '{"payload": "hello world", "description": "uppercase"}'
# → 200 OK, body: {"task_id":"-","task_status":"Success","outcome":{...}}
```

**Asynchronous (start then poll):**

```bash
# Start task
curl -X POST http://localhost:8080/api/v1/data/process-async \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: optional-uuid" \
  -d '{"payload": "hello world", "description": "uppercase"}'
# → 202 Accepted, body: {"task_id":"abc-123-...","task_status":"Processing","outcome":null}

# Get result (use task_id from above)
curl http://localhost:8080/api/v1/data/process-async/abc-123-def
# → 202 if still processing, or 200 with outcome when done
```
