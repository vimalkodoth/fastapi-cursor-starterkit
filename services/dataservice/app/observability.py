"""
OpenTelemetry setup for data-service: traces and logs exported via OTLP to the collector (SigNoz).
Init once at process startup; when OTEL_EXPORTER_OTLP_ENDPOINT is not set, all signals are no-op.
"""
import os
from typing import Any, Dict, Optional

_otel_logger = None


def _normalize_endpoint(endpoint: str) -> str:
    """Strip http(s) scheme for gRPC."""
    if endpoint.startswith("http://"):
        return endpoint[7:]
    if endpoint.startswith("https://"):
        return endpoint[8:]
    return endpoint


def init_observability() -> None:
    """
    Initialize OpenTelemetry: resource, tracer provider, logger provider, OTLP exporters (gRPC).
    Call once from main before starting the receiver.
    If OTEL_EXPORTER_OTLP_ENDPOINT is not set, does nothing (no-op).
    """
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    if not endpoint:
        return

    grpc_endpoint = _normalize_endpoint(endpoint)
    service_name = os.getenv("OTEL_SERVICE_NAME", "data-service")

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


def get_tracer(name: str = __name__, version: str = "1.0.0"):
    """Return the OTel tracer if tracing is enabled, else None."""
    try:
        from opentelemetry import trace

        return trace.get_tracer(name, version)
    except Exception:
        return None


def extract_trace_context(carrier: Dict[str, str]):
    """
    Extract trace context from a carrier (e.g. incoming RabbitMQ message headers).
    Returns a Context to use as parent when starting a span, or None if none/invalid.
    """
    try:
        from opentelemetry import propagate

        return propagate.extract(carrier)
    except Exception:
        return None


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
    Emit a log record to OTLP when logs are enabled.
    When include_trace_context is True, adds trace_id and span_id from the current span.
    No-op if OTEL_EXPORTER_OTLP_ENDPOINT was not set or logs SDK unavailable.
    """
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
