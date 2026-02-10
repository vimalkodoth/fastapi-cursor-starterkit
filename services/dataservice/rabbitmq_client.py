"""
RabbitMQ client for data service using kombu.
Lightweight implementation using industry-standard kombu library.
Uses a Dead Letter Exchange (DLX) and Dead Letter Queue (DLQ): failed messages
are nack'd with requeue=False and routed to the DLQ for inspection/retry.
"""
from kombu import Connection, Exchange, Queue, Producer, Consumer
from kombu.mixins import ConsumerMixin
import requests
import json
from typing import Optional, Callable

# Dead letter: exchange and queue names (suffix to main queue name)
DLX_SUFFIX = "_dlx"
DLQ_SUFFIX = "_dlq"


class EventReceiver(ConsumerMixin):
    """
    RabbitMQ event receiver using kombu for listening to queues and processing messages.
    """
    
    def __init__(self, username: str, password: str, host: str, port: int,
                 queue_name: str, service: Callable, service_name: str,
                 logger_url: Optional[str] = None):
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
        connection_url = f'amqp://{username}:{password}@{host}:{port}//'
        self.connection = Connection(connection_url)
        
        print(f"Awaiting requests from [x] {queue_name} [x]")
    
    def get_consumers(self, Consumer, channel):
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
        return [Consumer(
            queues=[main_queue],
            callbacks=[self.on_request],
            prefetch_count=1,
        )]
    
    def on_request(self, body, message):
        """Handle incoming message."""
        service_instance = self.service_worker()
        correlation_id = message.properties.get('correlation_id', 'unknown')
        
        self._log_event(correlation_id, 'start', '-')
        
        try:
            # Process message - convert body to string if needed
            if isinstance(body, dict):
                body_str = json.dumps(body)
            elif isinstance(body, bytes):
                body_str = body.decode('utf-8')
            else:
                body_str = str(body)
            
            response, task_type = service_instance.call(body_str)
            
            # Send response
            producer = Producer(message.channel)
            producer.publish(
                response,
                exchange='',
                routing_key=message.properties.get('reply_to'),
                correlation_id=correlation_id,
                serializer='json',
                retry=True
            )
            
            message.ack()
            self._log_event(correlation_id, 'end', '-')
            print(f'Processed request: {task_type}')
            
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
                "description": description
            }
            try:
                requests.post(self.logger_url, json=params, timeout=1)
            except requests.exceptions.RequestException:
                pass  # Logger service unavailable, continue silently
