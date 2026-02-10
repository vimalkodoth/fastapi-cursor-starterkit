"""
RabbitMQ client using kombu - industry-standard library used by large-scale apps.

kombu is used by:
- Celery (which we're already using)
- Django
- Many large-scale Python applications

Benefits:
- Industry-standard, battle-tested
- Better connection management
- Supports multiple backends (RabbitMQ, Redis, SQS, etc.)
- Less boilerplate than direct RabbitMQ clients
- Not tied to any specific project
"""
import json
import time
import uuid
from typing import Callable, Optional

import requests
from kombu import Connection, Consumer, Exchange, Producer, Queue
from kombu.mixins import ConsumerMixin

from app.core.metrics import record_rpc_latency, record_rpc_timeout

# Dead letter: exchange and queue name suffixes (main queue + suffix)
_DLX_SUFFIX = "_dlx"
_DLQ_SUFFIX = "_dlq"


class EventProducer:
    """
    RabbitMQ event producer using kombu for RPC-style communication.
    Sends messages to queues and waits for responses.
    """

    def __init__(
        self,
        username: str,
        password: str,
        host: str,
        port: int,
        service_name: str,
        logger_url: Optional[str] = None,
        on_log_event: Optional[
            Callable[
                [str, str, str, str, str, str],
                None,
            ]
        ] = None,
    ):
        """
        Initialize EventProducer with kombu.

        Args:
            username: RabbitMQ username
            password: RabbitMQ password
            host: RabbitMQ host
            port: RabbitMQ port
            service_name: Name of the service using this producer
            logger_url: Optional logger service URL for observability
            on_log_event: Optional callback (correlation_id, queue_name, service_name,
                status, description, task_type) to e.g. persist to task_logs
        """
        self.service_name = service_name
        self.logger_url = logger_url
        self.on_log_event = on_log_event

        # Create connection URL
        connection_url = f"amqp://{username}:{password}@{host}:{port}//"
        self.connection = Connection(connection_url)

    def call(self, queue_name: str, payload: str, timeout: int = 300) -> str:
        """
        Send message to queue and wait for response (RPC pattern).

        Args:
            queue_name: Name of the queue to send message to
            payload: Message payload as JSON string
            timeout: Maximum time to wait for response (seconds)

        Returns:
            Response as JSON string
        """
        response = None
        corr_id = str(uuid.uuid4())
        task_type = "data"
        try:
            payload_dict = json.loads(payload) if isinstance(payload, str) else payload
            task_type = payload_dict.get("task_type", "data")
        except (json.JSONDecodeError, TypeError, AttributeError):
            pass

        # Use a dedicated channel for this RPC call
        channel = self.connection.channel()

        try:
            # Named callback queue (avoid amq.* reserved prefix; use client name)
            callback_queue_name = f"reply_{corr_id}"
            callback_queue = Queue(
                callback_queue_name,
                exclusive=True,
                auto_delete=True,
            )
            callback_queue.declare(channel=channel)

            # Set up consumer for response
            def on_response(body, message):
                nonlocal response
                if message.properties.get("correlation_id") == corr_id:
                    response = body
                    message.ack()

            consumer = Consumer(
                channel,
                queues=[callback_queue],
                callbacks=[on_response],
                auto_declare=True,
            )
            consumer.consume()

            # Ensure target queue exists (declare passive to check; skip on error and try publish)
            try:
                target_queue = Queue(queue_name, durable=True)
                target_queue.declare(channel=channel, passive=True)
            except Exception:
                pass  # Queue may not exist yet; publish will timeout if no consumer

            self._log_event(corr_id, queue_name, "start", "-", task_type)

            # Publish message
            producer = Producer(channel)
            producer.publish(
                payload,
                exchange="",
                routing_key=queue_name,
                reply_to=callback_queue_name,
                correlation_id=corr_id,
                serializer="json",
                retry=True,
            )

            # Wait for response
            start_time = time.time()
            while response is None:
                if time.time() - start_time > timeout:
                    record_rpc_timeout()
                    self._log_event(corr_id, queue_name, "end", "Timeout", task_type)
                    consumer.cancel()
                    channel.close()
                    return json.dumps({"error": "Request timeout"})
                try:
                    self.connection.drain_events(timeout=1)
                except Exception:
                    pass  # Timeout is expected, continue waiting

            consumer.cancel()
            self._log_event(corr_id, queue_name, "end", "-", task_type)
            record_rpc_latency(time.time() - start_time)
            channel.close()

            # Convert response to JSON string if needed
            if isinstance(response, dict):
                return json.dumps(response)
            elif isinstance(response, str):
                return response
            else:
                return (
                    json.dumps(response)
                    if response
                    else json.dumps({"error": "Empty response"})
                )
        except Exception as e:
            try:
                channel.close()
            except Exception:
                pass
            self._log_event(
                corr_id, queue_name, "end", f"Exception: {str(e)}", task_type
            )
            return json.dumps({"error": f"RabbitMQ call failed: {str(e)}"})

    def _log_event(
        self,
        correlation_id: str,
        queue_name: str,
        status: str,
        description: str,
        task_type: str = "data",
    ):
        """Log event to logger service and optional DB callback."""
        if self.logger_url:
            params = {
                "correlation_id": correlation_id,
                "queue_name": queue_name,
                "service_name": self.service_name,
                "task_type": status,
                "description": description,
            }
            try:
                requests.post(self.logger_url, json=params, timeout=1)
            except requests.exceptions.RequestException:
                pass  # Logger service unavailable, continue silently
        if self.on_log_event:
            try:
                self.on_log_event(
                    correlation_id,
                    queue_name,
                    self.service_name,
                    status,
                    description,
                    task_type,
                )
            except Exception:
                pass  # Don't fail RPC on log write failure

    def close(self):
        """Close connection."""
        if self.connection:
            self.connection.close()


class EventReceiver(ConsumerMixin):
    """
    RabbitMQ event receiver using kombu for listening to queues.
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
        logger_url: Optional[str] = None,
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
            logger_url: Optional logger service URL for observability
        """
        self.service_worker = service
        self.service_name = service_name
        self.queue_name = queue_name
        self.logger_url = logger_url

        # Create connection
        connection_url = f"amqp://{username}:{password}@{host}:{port}//"
        self.connection = Connection(connection_url)

        print(f"Awaiting requests from [x] {queue_name} [x]")

    def get_consumers(self, Consumer, channel):
        """Set up consumer for the queue with Dead Letter Exchange and DLQ."""
        dlx_name = self.queue_name + _DLX_SUFFIX
        dlq_name = self.queue_name + _DLQ_SUFFIX
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
            Consumer(queues=[main_queue], callbacks=[self.on_request], prefetch_count=1)
        ]

    def on_request(self, body, message):
        """Handle incoming message."""
        service_instance = self.service_worker()
        correlation_id = message.properties.get("correlation_id", "unknown")

        self._log_event(correlation_id, "start", "-")

        try:
            # Process message - convert body to string if needed
            if isinstance(body, dict):
                body_str = json.dumps(body)
            elif isinstance(body, bytes):
                body_str = body.decode("utf-8")
            else:
                body_str = str(body)

            response, task_type = service_instance.call(body_str)

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

    def _log_event(self, correlation_id: str, task_type: str, description: str):
        """Log event to logger service if available."""
        if self.logger_url:
            params = {
                "correlation_id": correlation_id,
                "queue_name": self.queue_name,
                "service_name": self.service_name,
                "task_type": task_type,
                "description": description,
            }
            try:
                requests.post(self.logger_url, json=params, timeout=1)
            except requests.exceptions.RequestException:
                pass  # Logger service unavailable, continue silently
