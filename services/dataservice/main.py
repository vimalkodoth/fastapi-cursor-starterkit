import os

from rabbitmq_client import EventReceiver

from app.data_service import DataService
from app.observability import init_observability

# OpenTelemetry: traces and logs to otel-collector (no-op if OTEL_EXPORTER_OTLP_ENDPOINT unset)
init_observability()


def main():
    event_receiver = EventReceiver(
        username=os.getenv("RABBITMQ_USER", "guest"),
        password=os.getenv("RABBITMQ_PASSWORD", "welcome1"),
        host=os.getenv("RABBITMQ_HOST", "rabbitmq"),
        port=int(os.getenv("RABBITMQ_PORT", "5672")),
        queue_name=os.getenv("QUEUE_NAME", "data_queue"),
        service=DataService,
        service_name=os.getenv("SERVICE_NAME", "data"),
    )
    # Start consuming messages (ConsumerMixin.run() starts the consumer loop)
    event_receiver.run()


if __name__ == "__main__":
    main()
