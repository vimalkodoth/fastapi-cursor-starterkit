"""
RabbitMQ client for data service using kombu.
Lightweight implementation using industry-standard kombu library.
Uses a Dead Letter Exchange (DLX) and Dead Letter Queue (DLQ): failed messages
are nack'd with requeue=False and routed to the DLQ for inspection/retry.
"""
import json
from contextlib import nullcontext
from typing import Callable

from kombu import Connection, Exchange, Producer, Queue
from kombu.mixins import ConsumerMixin

_null_context = nullcontext


def _get_tracer_none(*_a, **_k):
    return None


try:
    from app.observability import emit_log as _otel_emit_log
    from app.observability import extract_trace_context, get_tracer
except ImportError:
    _otel_emit_log = None
    extract_trace_context = None
    get_tracer = _get_tracer_none

# Dead letter: exchange and queue names (suffix to main queue name)
DLX_SUFFIX = "_dlx"
DLQ_SUFFIX = "_dlq"


class EventReceiver(ConsumerMixin):
    """
    RabbitMQ event receiver using kombu for listening to queues and processing messages.
    """

    def __init__(
        self,
        username: str,
        password: str,
        host: str,
        port: int,
        queue_name: str,
        service: Callable,
        service_name: str,
    ):
        """
        Initialize EventReceiver with kombu.

        Args:
            username: RabbitMQ username
            password: RabbitMQ password
            host: RabbitMQ host
            port: RabbitMQ port
            queue_name: Name of the queue to listen to
            service: Service class that processes messages
            service_name: Name of the service
        """
        self.service_worker = service
        self.service_name = service_name
        self.queue_name = queue_name

        # Create connection
        connection_url = f"amqp://{username}:{password}@{host}:{port}//"
        self.connection = Connection(connection_url)

        print(f"Awaiting requests from [x] {queue_name} [x]")

    def get_consumers(self, consumer_cls, channel):
        """Set up consumer for the queue with Dead Letter Exchange and DLQ."""
        dlx_name = self.queue_name + DLX_SUFFIX
        dlq_name = self.queue_name + DLQ_SUFFIX
        dlx = Exchange(dlx_name, type="direct", durable=True)
        dlx.declare(channel=channel)
        dlq = Queue(
            dlq_name,
            exchange=dlx,
            routing_key=dlq_name,
            durable=True,
        )
        dlq.declare(channel=channel)
        main_queue = Queue(
            self.queue_name,
            durable=True,
            queue_arguments={
                "x-dead-letter-exchange": dlx_name,
                "x-dead-letter-routing-key": dlq_name,
            },
        )
        return [
            consumer_cls(
                queues=[main_queue],
                callbacks=[self.on_request],
                prefetch_count=1,
            )
        ]

    def _headers_carrier(self, message):
        """Build a string-keyed dict from message headers for trace context extraction."""
        headers = (
            getattr(message, "headers", None)
            or message.properties.get("application_headers")
            or {}
        )
        if not isinstance(headers, dict):
            return {}
        return {str(k): str(v) for k, v in headers.items() if v is not None}

    def on_request(self, body, message):
        """Handle incoming message."""
        service_instance = self.service_worker()
        correlation_id = message.properties.get("correlation_id", "unknown")

        self._log_event(correlation_id, "start", "-")

        tracer = get_tracer(__name__, "1.0.0") if callable(get_tracer) else None
        carrier = self._headers_carrier(message)
        remote_ctx = (
            extract_trace_context(carrier) if callable(extract_trace_context) else None
        )
        if tracer and remote_ctx is not None:
            span_ctx = tracer.start_as_current_span(
                "message.process", context=remote_ctx
            )
        elif tracer:
            span_ctx = tracer.start_as_current_span("message.process")
        else:
            span_ctx = _null_context()
        try:
            with span_ctx:
                # Process message - convert body to string if needed
                if isinstance(body, dict):
                    body_str = json.dumps(body)
                elif isinstance(body, bytes):
                    body_str = body.decode("utf-8")
                else:
                    body_str = str(body)

                if _otel_emit_log is not None:
                    try:
                        _otel_emit_log(
                            "data-service processing start",
                            attributes={
                                "layer": "dataservice",
                                "correlation_id": correlation_id,
                                "queue_name": self.queue_name,
                            },
                        )
                    except Exception:
                        pass

                response, task_type = service_instance.call(body_str)

                if _otel_emit_log is not None:
                    try:
                        _otel_emit_log(
                            "data-service processing end",
                            attributes={
                                "layer": "dataservice",
                                "correlation_id": correlation_id,
                                "task_type": task_type,
                            },
                        )
                    except Exception:
                        pass

                # Send response
                producer = Producer(message.channel)
                producer.publish(
                    response,
                    exchange="",
                    routing_key=message.properties.get("reply_to"),
                    correlation_id=correlation_id,
                    serializer="json",
                    retry=True,
                )

                message.ack()
                self._log_event(correlation_id, "end", "-")
                print(f"Processed request: {task_type}")

        except Exception as e:
            response = {
                "error": "Receiver exception",
                "queue": self.queue_name,
                "service_name": self.service_name,
                "correlation_id": correlation_id,
                "exception": str(e),
            }
            producer = Producer(message.channel)
            producer.publish(
                response,
                exchange="",
                routing_key=message.properties.get("reply_to"),
                correlation_id=correlation_id,
                serializer="json",
                retry=True,
            )
            self._log_event(correlation_id, "end", f"Receiver exception: {str(e)}")
            print(f"Receiver exception: {str(e)}")
            # Reject so message is dead-lettered to DLQ for inspection/retry
            message.reject(requeue=False)

    def _log_event(self, correlation_id: str, status: str, description: str):
        """Emit OTel log when enabled (receiver lifecycle: start/end). Includes trace_id from current span."""
        if _otel_emit_log is not None:
            try:
                _otel_emit_log(
                    body=f"receiver {status}",
                    attributes={
                        "layer": "receiver",
                        "correlation_id": correlation_id,
                        "queue_name": self.queue_name,
                        "service_name": self.service_name,
                        "status": status,
                        "description": description,
                    },
                )
            except Exception:
                pass
