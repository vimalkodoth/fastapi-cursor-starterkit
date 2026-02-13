"""
OpenTelemetry setup: traces, metrics, and logs exported via OTLP to the collector (SigNoz).
Init once at app startup; when OTEL_EXPORTER_OTLP_ENDPOINT is not set, all signals are no-op.
"""
import os
from typing import Any, Dict, Optional

# Set in init when logs are enabled; used by emit_log().
_otel_logger = None


def _normalize_endpoint(endpoint: str) -> str:
    """Strip http(s) scheme for gRPC."""
    if endpoint.startswith("http://"):
        return endpoint[7:]
    if endpoint.startswith("https://"):
        return endpoint[8:]
    return endpoint


def init_observability(app=None):
    """
    Initialize OpenTelemetry: resource; tracer, meter, and logger providers;
    OTLP exporters (gRPC); FastAPI auto-instrumentation.
    Call once from main.py before or after creating the FastAPI app.
    If OTEL_EXPORTER_OTLP_ENDPOINT is not set, does nothing (no-op).
    """
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    if not endpoint:
        return

    grpc_endpoint = _normalize_endpoint(endpoint)
    service_name = os.getenv("OTEL_SERVICE_NAME", "fastapi-api")

    try:
        from opentelemetry.sdk.resources import Resource
    except ImportError:
        return

    resource = Resource.create({"service.name": service_name})

    # --- Traces ---
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        pass
    else:
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=grpc_endpoint, insecure=True))
        )
        trace.set_tracer_provider(provider)

    # --- Metrics ---
    try:
        from opentelemetry import metrics
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
            OTLPMetricExporter,
        )
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    except ImportError:
        pass
    else:
        metric_reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(endpoint=grpc_endpoint, insecure=True),
            export_interval_millis=15_000,
            export_timeout_millis=10_000,
        )
        meter_provider = MeterProvider(
            resource=resource,
            metric_readers=[metric_reader],
        )
        metrics.set_meter_provider(meter_provider)
        _register_rpc_metrics(meter_provider)

    # --- Logs ---
    try:
        from opentelemetry import _logs
        from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
        from opentelemetry.sdk._logs import LoggerProvider
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
    except ImportError:
        pass
    else:
        global _otel_logger
        log_provider = LoggerProvider(resource=resource)
        log_provider.add_log_record_processor(
            BatchLogRecordProcessor(
                OTLPLogExporter(endpoint=grpc_endpoint, insecure=True)
            )
        )
        _logs.set_logger_provider(log_provider)
        _otel_logger = _logs.get_logger(__name__, "1.0.0")

    # --- FastAPI instrumentation (traces) ---
    # exclude_spans: ASGI sends the response in two steps (response.start, response.body),
    # so the middleware creates two "http send" spans per request. Excluding receive/send
    # keeps one server span per request plus any custom spans (e.g. message.process).
    if app is not None:
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

            FastAPIInstrumentor.instrument_app(
                app,
                exclude_spans=["receive", "send"],
            )
        except ImportError:
            pass


def _register_rpc_metrics(meter_provider) -> None:
    """Register observable gauges that report get_rpc_stats() to OTel."""
    try:
        from opentelemetry.metrics import Observation
    except ImportError:
        return
    try:
        from app.core.metrics import get_rpc_stats
    except ImportError:
        return

    meter = meter_provider.get_meter("fastapi-api-rpc", "1.0.0")

    def observe_latency_count(_options):
        stats = get_rpc_stats()
        lat = stats.get("latency_seconds") or {}
        yield Observation(lat.get("count") or 0, {})

    def observe_latency_avg(_options):
        stats = get_rpc_stats()
        lat = stats.get("latency_seconds") or {}
        avg = lat.get("avg")
        if avg is not None:
            yield Observation(avg, {})

    def observe_latency_p50(_options):
        stats = get_rpc_stats()
        lat = stats.get("latency_seconds") or {}
        p50 = lat.get("p50")
        if p50 is not None:
            yield Observation(p50, {})

    def observe_latency_p95(_options):
        stats = get_rpc_stats()
        lat = stats.get("latency_seconds") or {}
        p95 = lat.get("p95")
        if p95 is not None:
            yield Observation(p95, {})

    def observe_timeouts(_options):
        stats = get_rpc_stats()
        yield Observation(stats.get("timeouts_total", 0), {})

    meter.create_observable_gauge(
        name="rpc.latency.count",
        callbacks=[observe_latency_count],
        description="Number of RPC latency samples in the window",
        unit="1",
    )
    meter.create_observable_gauge(
        name="rpc.latency.avg_seconds",
        callbacks=[observe_latency_avg],
        description="Average RPC latency in seconds",
        unit="s",
    )
    meter.create_observable_gauge(
        name="rpc.latency.p50_seconds",
        callbacks=[observe_latency_p50],
        description="p50 RPC latency in seconds",
        unit="s",
    )
    meter.create_observable_gauge(
        name="rpc.latency.p95_seconds",
        callbacks=[observe_latency_p95],
        description="p95 RPC latency in seconds",
        unit="s",
    )
    meter.create_observable_gauge(
        name="rpc.timeouts_total",
        callbacks=[observe_timeouts],
        description="Total RPC timeouts",
        unit="1",
    )


def _get_trace_context_attributes() -> Dict[str, str]:
    """Return trace_id and span_id from current span for log-trace correlation in SigNoz."""
    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        if not span.is_recording():
            return {}
        ctx = span.get_span_context()
        return {
            "trace_id": format(ctx.trace_id, "032x"),
            "span_id": format(ctx.span_id, "016x"),
        }
    except Exception:
        return {}


def emit_log(
    body: str,
    attributes: Optional[Dict[str, Any]] = None,
    severity_number: Optional[int] = None,
    include_trace_context: bool = True,
) -> None:
    """
    Emit a log record to OTLP (SigNoz) when logs are enabled.
    When include_trace_context is True, adds trace_id and span_id from the current span
    so logs correlate with traces in SigNoz.
    No-op if OTEL_EXPORTER_OTLP_ENDPOINT was not set or logs SDK unavailable.
    """
    global _otel_logger
    if _otel_logger is None:
        return
    try:
        attrs = dict(attributes) if attributes else {}
        if include_trace_context:
            attrs.update(_get_trace_context_attributes())
        kwargs = {"body": body}
        if attrs:
            kwargs["attributes"] = attrs
        if severity_number is not None:
            kwargs["severity_number"] = severity_number
        _otel_logger.emit(**kwargs)
    except Exception:
        pass


# --- Trace context propagation (W3C Trace Context) for end-to-end distributed traces ---


def inject_trace_context(carrier: Dict[str, str]) -> None:
    """
    Inject current span context into a dict carrier (e.g. RabbitMQ message headers).
    Enables downstream services to continue the same trace (waterfall).
    No-op if OTel not set up.
    """
    try:
        from opentelemetry import propagate

        propagate.inject(carrier)
    except Exception:
        pass


def extract_trace_context(carrier: Dict[str, str]):
    """
    Extract trace context from a carrier (e.g. incoming message headers).
    Returns a Context to use as parent when starting a span, or None if none/invalid.
    """
    try:
        from opentelemetry import propagate

        return propagate.extract(carrier)
    except Exception:
        return None
