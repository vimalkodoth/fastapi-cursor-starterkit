"""
Celery worker configuration.
OpenTelemetry is initialized per worker process via worker_process_init (traces, metrics, logs → OTLP).
Trace context is propagated from API to worker so one request = one trace (API → worker → data-service).

Propagation: The API sends W3C trace context in the task payload (_trace_context). This handler runs
before the Celery instrumentor's task_prerun. We copy traceparent/tracestate onto task.request so
the instrumentor's getter (getattr(request, key)) finds them and creates the task span as a child
of the API span. This works regardless of broker (Redis/RabbitMQ) and Celery message header support.
"""
import json
import os

from celery import Celery
from celery.signals import task_prerun, worker_process_init

# W3C Trace Context keys the instrumentor's getter looks for on task.request
_TRACEPARENT = "traceparent"
_TRACESTATE = "tracestate"


app = Celery(
    "celery_api",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
    include=["app.tasks.data"],
)


@worker_process_init.connect(weak=False)
def _init_otel_worker(**_kwargs):
    """Initialize OpenTelemetry and Celery instrumentation in each worker process."""
    try:
        from app.observability import init_observability

        init_observability()
    except (ImportError, AttributeError):
        pass
    try:
        from opentelemetry.instrumentation.celery import CeleryInstrumentor

        CeleryInstrumentor().instrument()
    except ImportError:
        pass


@task_prerun.connect(weak=False)
def _propagate_trace_context_to_request(sender, task_id, args, kwargs, **extra):
    """
    Copy trace context from task payload onto task.request so the Celery instrumentor's
    task_prerun (which runs after this) sees it via extract(request) and creates the task
    span as a child of the API span. One request = one end-to-end trace.
    """
    request = extra.get("request")
    if request is None:
        task = extra.get("task")
        request = getattr(task, "request", None) if task else None
    if request is None:
        return
    raw = (args[0] if args else None) or kwargs.get("payload")
    if not raw:
        return
    try:
        payload = json.loads(raw) if isinstance(raw, str) else raw
    except (TypeError, ValueError):
        return
    carrier = payload.get("_trace_context")
    if not carrier or not isinstance(carrier, dict):
        return
    traceparent = carrier.get(_TRACEPARENT) or carrier.get("traceparent")
    tracestate = carrier.get(_TRACESTATE) or carrier.get("tracestate")
    if traceparent:
        setattr(
            request,
            _TRACEPARENT,
            traceparent if isinstance(traceparent, str) else str(traceparent),
        )
    if tracestate:
        setattr(
            request,
            _TRACESTATE,
            tracestate if isinstance(tracestate, str) else str(tracestate),
        )
