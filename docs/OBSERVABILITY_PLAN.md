# Observability Implementation Plan

**Status:** Plan approved. Implementation in phases.

**Decisions (confirmed):**
- **Scope:** Backend API + Celery worker + Data service; Logger service **deprecated** and replaced by OTel.
- **Traces, metrics, logs:** **SigNoz** (single backend); no ELK, no separate Jaeger or Prometheus.
- **Metrics API:** Keep existing `GET /api/v1/metrics` JSON for human-readable output; metrics also sent via OTLP to SigNoz.
- **Instrumentation:** OpenTelemetry only (single SDK for traces, metrics, logs).
- **Collector:** Standalone OTLP Collector; receives from all apps and fans out to **SigNoz** (OTLP).
- **Logger service:** Deprecate; remove HTTP logger calls and logger container once OTel is in place.

---

## 1. Target architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  APPLICATIONS                                                                   │
│  ┌─────────────┐  ┌─────────────────┐  ┌─────────────────┐                     │
│  │ Backend API │  │ Celery worker    │  │ Data service     │                     │
│  │ (FastAPI)   │  │ (Celery)         │  │ (RabbitMQ cons.) │                     │
│  └──────┬──────┘  └────────┬─────────┘  └────────┬─────────┘                     │
│         │                  │                      │                                │
│         │ OTLP             │ OTLP                 │ OTLP                           │
│         │ (gRPC/HTTP)      │ (gRPC/HTTP)          │ (gRPC/HTTP)                     │
│         │ traces, metrics, logs                                                     │
└─────────┼──────────────────┼──────────────────────┼────────────────────────────────┘
          │                  │                      │
          ▼                  ▼                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  OPEN TELEMETRY COLLECTOR (single entry point)                                   │
│  Receivers: otlp (gRPC 4317, HTTP 4318)                                         │
│  Processors: batch, memory_limiter                                               │
│  Exporters: otlp → SigNoz (traces, metrics, logs)                               │
└──────────────────────────────────────┬──────────────────────────────────────────┘
                                        │
                                        ▼
                               ┌──────────────────┐
                               │     SigNoz        │
                               │  (traces, metrics,│
                               │   logs — one UI)  │
                               │   :3301 UI        │
                               │   :4317 OTLP      │
                               └──────────────────┘
```

**Removed:** Logger service (HTTP); no ELK, no separate Jaeger or Prometheus. SigNoz is the single observability backend.

---

## 2. Components and ports

| Component | Image / Build | Ports | Purpose |
|-----------|----------------|-------|---------|
| **OTel Collector** | `otel/opentelemetry-collector-contrib` | 4317 (gRPC), 4318 (HTTP) | Receive OTLP from apps; export OTLP to SigNoz |
| **SigNoz** | [SigNoz docker](https://signoz.io/docs/install/docker) | 3301 (UI), 4317 (OTLP gRPC), 4318 (OTLP HTTP) | Traces, metrics, logs; ClickHouse; one dashboard |

**Note:** SigNoz accepts OTLP on 4317/4318. Collector sends traces, metrics, and logs to SigNoz. Run SigNoz via their docker-compose (same network) or add to this project's compose.

---

## 3. Deprecation of Logger service

### 3.1 What is removed

- **docker-compose:** Remove `logger` service and its build/network/depends_on references.
- **Environment variables:** Remove `LOGGER_PRODUCER_URL` and `LOGGER_RECEIVER_URL` from `api`, `api-celery`, and `data-service`.
- **Code:**
  - **backend:** `backend/app/infrastructure/rabbitmq.py` — remove `logger_url` from `EventProducer` and `EventReceiver`; remove `_log_event()` HTTP call (keep `on_log_event` callback for DB only if desired, or move to OTel logs).
  - **backend:** `backend/app/core/dependencies.py` — stop passing `logger_url` to `EventProducer`; keep or drop `on_log_event=_write_task_log_sync` (decision: keep DB write for sync path or replace with OTel log).
  - **backend:** `backend/app/tasks/data.py` — stop passing `logger_url` to `EventProducer`.
  - **dataservice:** `services/dataservice/rabbitmq_client.py` — remove `logger_url` and `_log_event()` HTTP call; `services/dataservice/main.py` — remove `LOGGER_RECEIVER_URL`.
- **Docs:** ARCHITECTURE.md and any runbooks — remove or rewrite "Logger service" section to "Observability (OTel + Collector + SigNoz)".

### 3.2 What replaces it

- **Traces:** OTel spans in API, Celery, and Data service; correlation_id becomes trace_id/span attribute; SigNoz shows full request flow.
- **Metrics:** OTel metrics (and existing RPC/queue stats) sent via OTLP to SigNoz; keep `GET /api/v1/metrics` JSON unchanged for human use.
- **Logs:** OTel log records (e.g. producer/receiver events) emitted from the same services and exported via Collector to SigNoz; query in SigNoz UI.
- **Optional:** Keep writing `task_logs` in PostgreSQL from sync path via `on_log_event` for backward compatibility, or remove and rely on SigNoz.

---

## 4. Implementation phases

### Phase 1 — Infrastructure (no app code changes)

**Goal:** Run OTel Collector and SigNoz so Collector can fan out to SigNoz.

| Step | Action |
|------|--------|
| 1.1 | Add `otel-collector` service to `docker-compose.yml`; mount Collector config (see Section 6) that exports OTLP to SigNoz. |
| 1.2 | Add SigNoz: either (A) use [SigNoz official docker-compose](https://github.com/SigNoz/signoz/tree/main/deploy) in a separate `deploy/` or directory and join the same Docker network, or (B) add SigNoz core services (query-service, frontend, ClickHouse, otel-collector) to this project's compose. For (A), ensure our Collector exports to the hostname of SigNoz's OTLP receiver (e.g. `signoz-otel-collector:4317`). |
| 1.3 | Create `observability/otel-collector-config.yaml`: otlp receiver (4317, 4318) → batch → otlp exporter to SigNoz (`signoz:4317` or the correct SigNoz OTLP host). |
| 1.4 | Wire network so api, api-celery, data-service can reach `otel-collector:4317` and `4318`; Collector can reach SigNoz OTLP (4317). |

**Deliverable:** `docker compose up` (and SigNoz stack if separate) brings up Collector + SigNoz; no app instrumentation yet.

---

### Phase 2 — Backend API: OpenTelemetry + keep current metrics format

**Goal:** API sends traces, metrics, and logs via OTLP to Collector; keep `GET /api/v1/metrics` JSON; metrics also in SigNoz.

| Step | Action |
|------|--------|
| 2.1 | Add deps: `opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-exporter-otlp-proto-grpc` (or http), `opentelemetry-instrumentation-fastapi`, `opentelemetry-instrumentation-sqlalchemy` (optional), `Export all telemetry to Collector (OTLP); Collector exports to SigNoz. |
| 2.2 | Add `backend/app/observability.py` (or `core/otel.py`): init OTel SDK — TracerProvider, MeterProvider, LoggerProvider; OTLP exporters (gRPC) to `OTEL_EXPORTER_OTLP_ENDPOINT`; register FastAPI auto-instrumentation; set resource (service.name=fastapi-api). |
| 2.3 | In `main.py`: call observability init before `app = FastAPI()` (or in lifespan). |
| 2.4 | In `EventProducer.call()` (and sync path): create a span (e.g. `rabbitmq.rpc`) and set correlation_id as attribute; emit a log record for start/end instead of HTTP to logger. Remove `logger_url` and HTTP `_log_event`; keep or remove `on_log_event` (DB). |
| 2.5 | Send all telemetry via OTLP to Collector; keep `GET /api/v1/metrics` unchanged (human-readable JSON). Metrics appear in SigNoz via Collector. |
| 2.6 | Env: `OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317`, `OTEL_SERVICE_NAME=fastapi-api`, `OTEL_TRACES_EXPORTER=otlp`, `OTEL_METRICS_EXPORTER=otlp`, `OTEL_LOGS_EXPORTER=otlp`. |

**Deliverable:** API emits OTLP; SigNoz shows traces, metrics, and logs.

---

### Phase 3 — Remove Logger usage from Backend and Data service

**Goal:** No dependency on logger service; telemetry only via OTel.

| Step | Action |
|------|--------|
| 3.1 | `backend/app/infrastructure/rabbitmq.py`: Remove `logger_url` parameter and all `_log_event()` HTTP logic from `EventProducer` and `EventReceiver`. Optionally keep `on_log_event` and call it from a span event or OTel log so DB still gets task_logs, or remove and rely on OTel logs only. |
| 3.2 | `backend/app/core/dependencies.py`: Stop passing `logger_url` to `EventProducer`; keep `on_log_event=_write_task_log_sync` if TaskLog DB is kept. |
| 3.3 | `backend/app/tasks/data.py`: Remove `logger_url` from `EventProducer` constructor. |
| 3.4 | `services/dataservice/rabbitmq_client.py`: Remove `logger_url` and `_log_event()`; add OTel in Phase 5. |
| 3.5 | `services/dataservice/main.py`: Remove `LOGGER_RECEIVER_URL` env. |
| 3.6 | `docker-compose.yml`: Remove `logger` service; remove `LOGGER_*` env from api, api-celery, data-service; remove `depends_on: logger` and `condition: service_started` for logger. |

**Deliverable:** Compose and code no longer reference the logger service.

---

### Phase 4 — Celery worker: OpenTelemetry

**Goal:** Celery tasks and RabbitMQ RPC produce traces/metrics/logs via OTLP.

| Step | Action |
|------|--------|
| 4.1 | Add same OTel deps as backend; in worker process init OTel (TracerProvider, MeterProvider, LoggerProvider → OTLP to Collector). |
| 4.2 | Use `opentelemetry-instrumentation-celery` if available, or manually create a span per task and for the RPC call in `process_data_task`; set correlation_id/trace_id. |
| 4.3 | Ensure trace context is propagated (e.g. trace_id in message or headers) so API → Celery → Data service is one trace if possible. |
| 4.4 | Env: `OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317`, `OTEL_SERVICE_NAME=fastapi-celery-worker`. |

**Deliverable:** SigNoz shows Celery task spans and RPC; metrics and logs in SigNoz.

---

### Phase 5 — Data service: OpenTelemetry

**Goal:** Data service emits traces and logs for receive/process/send.

| Step | Action |
|------|--------|
| 5.1 | Add OTel SDK to `services/dataservice`; init in `main.py` before starting RabbitMQ consumer. |
| 5.2 | In consumer: create span for each message (e.g. `rabbitmq.consume`); set correlation_id from message as trace/span attribute; emit log records for start/end/error. |
| 5.3 | Env: `OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317`, `OTEL_SERVICE_NAME=data-service`. |

**Deliverable:** End-to-end trace (API → RabbitMQ → Data service → back) and logs in SigNoz.

---

### Phase 6 — Collector config and SigNoz

**Goal:** Collector receives OTLP and exports all signals to SigNoz.

| Step | Action |
|------|--------|
| 6.1 | Finalize `observability/otel-collector-config.yaml`: otlp receiver (grpc 4317, http 4318); batch processor; otlp exporter to SigNoz (endpoint = SigNoz OTLP host, e.g. `signoz-otel-collector:4317` or `signoz:4317` depending on SigNoz deploy). Single pipeline per signal (traces, metrics, logs) or one otlp exporter for all. |
| 6.2 | Ensure SigNoz is running and reachable from Collector; verify traces, metrics, and logs appear in SigNoz UI (port 3301 or 8080 per SigNoz docs). |

**Deliverable:** Traces, metrics, and logs in SigNoz.

---

### Phase 7 — Docs and cleanup

| Step | Action |
|------|--------|
| 7.1 | Update `docs/ARCHITECTURE.md`: replace Logger section with Observability (OTel, Collector, SigNoz); add diagram and env vars. |
| 7.2 | Update root `README.md`: add Observability section (SigNoz UI URL, required env vars). |
| 7.3 | Add `docs/OBSERVABILITY.md` (optional): runbook for adding new services, troubleshooting. |
| 7.4 | Remove or archive `logger/` directory (or leave with DEPRECATED notice). |

---

## 5. File-level change summary

| File / area | Change |
|-------------|--------|
| `docker-compose.yml` | Add otel-collector; add or reference SigNoz (or use SigNoz's own compose on same network); remove logger; remove LOGGER_* and depends_on logger from api, api-celery, data-service. |
| `observability/otel-collector-config.yaml` (new) | OTLP in; batch; export to SigNoz (OTLP). |
| `backend/requirements.txt` | Add opentelemetry-* packages. |
| `backend/app/observability.py` or `core/otel.py` (new) | Init SDK, OTLP exporters, FastAPI instrumentation, resource. |
| `backend/main.py` | Call observability init on startup. |
| `backend/app/infrastructure/rabbitmq.py` | Remove logger_url, _log_event HTTP; add span + OTel log in call(). |
| `backend/app/core/dependencies.py` | Remove logger_url from EventProducer; keep on_log_event if DB TaskLog kept. |
| `backend/app/tasks/data.py` | Remove logger_url; add OTel init and spans in task. |
| `services/dataservice/requirements.txt` | Add opentelemetry-* packages. |
| `services/dataservice/main.py` | Init OTel; remove LOGGER_RECEIVER_URL. |
| `services/dataservice/rabbitmq_client.py` | Remove logger_url and _log_event; add OTel span/log in consumer. |
| `docs/ARCHITECTURE.md` | Replace Logger with Observability section. |
| `README.md` | Observability subsection and env vars. |
| `logger/` | Deprecate (README or remove from compose only). |

---

## 6. OpenTelemetry Collector config (example)

Use **contrib** image: `otel/opentelemetry-collector-contrib`. Export all signals to SigNoz via OTLP.

```yaml
# observability/otel-collector-config.yaml (example)
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 1s
    send_batch_size: 1024
  memory_limiter:
    check_interval: 1s
    limit_mib: 512

exporters:
  otlp/signoz:
    endpoint: signoz-otel-collector:4317   # or the hostname of SigNoz's OTLP receiver
    tls:
      insecure: true

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlp/signoz]
    metrics:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlp/signoz]
    logs:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlp/signoz]
```

**Note:** Replace `signoz-otel-collector` with the actual SigNoz OTLP host (e.g. from [SigNoz docker install](https://signoz.io/docs/install/docker)). If SigNoz runs in the same Docker network, use the service name that exposes port 4317.

---

## 7. Environment variables (applications)

| Variable | API | Celery | Data service | Purpose |
|----------|-----|--------|--------------|---------|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://otel-collector:4317` | same | same | OTLP gRPC (or use HTTP 4318 with proto) |
| `OTEL_SERVICE_NAME` | `fastapi-api` | `fastapi-celery-worker` | `data-service` | Service name in traces/logs/metrics |
| `OTEL_TRACES_EXPORTER` | `otlp` | `otlp` | `otlp` | Enable trace export |
| `OTEL_METRICS_EXPORTER` | `otlp` | `otlp` | `otlp` | Enable metric export |
| `OTEL_LOGS_EXPORTER` | `otlp` | `otlp` | `otlp` | Enable log export |

Remove: `LOGGER_PRODUCER_URL`, `LOGGER_RECEIVER_URL`.

---

## 8. Execution order

1. **Phase 1** — Infrastructure and Collector (no app changes).
2. **Phase 2** — Backend API OTel; keep `/api/v1/metrics` JSON.
3. **Phase 3** — Remove logger from code and compose.
4. **Phase 4** — Celery OTel.
5. **Phase 5** — Data service OTel.
6. **Phase 6** — Tune Collector and SigNoz connectivity.
7. **Phase 7** — Docs and deprecate logger folder.

After Phase 2+3, the old logger is fully deprecated and observability is OTel → Collector → SigNoz.

---

## 9. Next steps (immediate)

1. **Review** this plan and confirm Phase 1: how SigNoz will run (same compose vs [SigNoz official docker](https://signoz.io/docs/install/docker)).
2. **Implement Phase 1:** Add `observability/otel-collector-config.yaml` (OTLP → SigNoz); add `otel-collector` to `docker-compose.yml`; run SigNoz (e.g. clone SigNoz repo, `docker compose up` from `deploy/`, or add SigNoz services to this repo); verify Collector can reach SigNoz OTLP.
3. **Implement Phase 2:** Add OTel to backend API and verify traces, metrics, and logs in SigNoz.
4. **Implement Phase 3:** Remove logger from code and compose in one pass.
5. Proceed with Phases 4–7 in order.

---

## 10. Distributed tracing best practice: end-to-end traces

**Standard / expectation:** A single request should appear as **one trace** with a **waterfall** of all services touched (API → Celery → data-service, or API → data-service for sync). This is the usual approach in OpenTelemetry, Jaeger, Zipkin, and SigNoz: one trace ID, multiple spans (one per service/hop), so you see the full path and timing in one view.

**How it works:** **Context propagation** carries `trace_id` and `parent_span_id` across process boundaries. The [W3C Trace Context](https://www.w3.org/TR/trace-context/) standard (e.g. `traceparent` header) is used so that when Service A calls Service B, B creates a span that is a **child** of A’s span, under the same trace.

**What we do in this stack:**

| Boundary | Mechanism |
|----------|-----------|
| **API → RabbitMQ → data-service** | Producer injects current trace context into message **headers** (W3C); data-service consumer extracts and starts `message.process` span with that context as parent. |
| **API → Celery worker** | API injects trace context into the task payload (`_trace_context`); worker’s `task_prerun` signal extracts and **attaches** that context so the Celery task span is created as a child of the API span. |
| **Celery worker → RabbitMQ → data-service** | Same as first row: worker’s `EventProducer` injects context into headers; data-service extracts and continues the trace. |

**Result:** Sync requests show one trace: **fastapi-api** (e.g. `POST /api/v1/data/process`) → **data-service** (`message.process`). Async requests show one trace: **fastapi-api** (`POST /api/v1/data/process-async`) → **fastapi-celery-worker** (`run/app.tasks.data.process_data_task`) → **data-service** (`message.process`). In SigNoz, open a trace by TraceID to see the full waterfall.

**Why payload + request (async):** The Celery instrumentor creates the task span from `extract(task.request)`. Brokers (e.g. Redis) often do not expose custom message headers as `task.request` attributes, so headers-only propagation fails. Sending context in the payload and copying it onto `task.request` in our `task_prerun` (before the instrumentor runs) ensures the instrumentor sees it and creates a child span—one request, one trace.

**Trace shape: “only forward” vs “sending back”.** The FastAPI/ASGI instrumentation can create three spans per HTTP request: **receive** (reading the request from the client), the main **server** span (handling the request), and **send** (writing the response back to the client). We set `exclude_spans=["receive", "send"]` so we keep **one server span per request** that covers the full round-trip. So in the trace you see only the “forward” path in terms of span count: one span per hop (API → worker → data-service), and the “sending back” of the HTTP response is **implicit** in that server span ending—there is no separate “send” or “sending back” span. If the UI or span attributes still mention “send” or “Producer”/“Consumer”, that can come from other layers (e.g. messaging span kinds) and is expected; the important part is we do not create extra receive/send spans for each HTTP request.
