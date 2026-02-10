"""
Data processing Celery tasks.
"""
import json
import os
from typing import Any, Dict, Optional

from celery import current_task
from celery.utils.log import get_task_logger
from sqlmodel import Session

from app.core.database import engine
from app.infrastructure.celery import app
from app.infrastructure.rabbitmq import EventProducer
from app.models.database import DataProcessingRecord

# Create logger - enable to display messages on task logger
celery_log = get_task_logger(__name__)


def _save_async_record(
    task_id: str,
    payload_str: str,
    description: Optional[str],
    task_status: str,
    outcome: str,
) -> None:
    """
    Persist a data processing record to PostgreSQL (Celery worker uses sync engine).
    """
    with Session(engine) as session:
        record = DataProcessingRecord(
            task_id=task_id,
            payload=payload_str,
            description=description,
            task_type="data",
            task_status=task_status,
            outcome=outcome,
        )
        session.add(record)
        session.commit()


@app.task(name="app.tasks.data.process_data_task")
def process_data_task(payload: str) -> Dict[str, Any]:
    """
    Process data task asynchronously using Celery and RabbitMQ.
    Uses EventProducer to send message to data service via RabbitMQ queue.
    Persists a record to PostgreSQL on success or failure (async path integration).
    """
    payload_json = json.loads(payload)
    task_id = str(current_task.request.id)
    payload_str = str(payload_json.get("payload", payload))
    description = payload_json.get("description")

    # Queue name for data service
    queue_name = os.getenv("DATA_QUEUE_NAME", "data_queue")

    try:
        event_producer = EventProducer(
            username=os.getenv("RABBITMQ_USER", "guest"),
            password=os.getenv("RABBITMQ_PASSWORD", "welcome1"),
            host=os.getenv("RABBITMQ_HOST", "rabbitmq"),
            port=int(os.getenv("RABBITMQ_PORT", "5672")),
            service_name="api_celery_worker",
            logger_url=os.getenv(
                "LOGGER_PRODUCER_URL", "http://logger:5001/api/v1/logger/log_producer"
            ),
        )

        # Send message to RabbitMQ queue and wait for response
        response = event_producer.call(queue_name, json.dumps(payload_json))
        response_json = json.loads(response)

        # Persist to PostgreSQL to show async path integration
        _save_async_record(
            task_id=task_id,
            payload_str=payload_str,
            description=description,
            task_status="Success",
            outcome=json.dumps(
                response_json
                if isinstance(response_json, dict)
                else {"result": response_json}
            ),
        )

        celery_log.info("Data processing task completed")
        return response_json

    except Exception as e:
        celery_log.error("Data processing task failed: %s", str(e))
        error_payload = {"error": f"Data processing failed: {str(e)}"}
        # Persist failure record to DB for integration visibility
        _save_async_record(
            task_id=task_id,
            payload_str=payload_str,
            description=description,
            task_status="Failed",
            outcome=json.dumps(error_payload),
        )
        return error_payload


@app.task(name="app.tasks.data.process_generic_task")
def process_generic_task(queue_name: str, payload: str) -> Dict[str, Any]:
    """
    Generic task processor for calling any service via RabbitMQ.
    """
    payload_json = json.loads(payload)

    try:
        event_producer = EventProducer(
            username=os.getenv("RABBITMQ_USER", "guest"),
            password=os.getenv("RABBITMQ_PASSWORD", "welcome1"),
            host=os.getenv("RABBITMQ_HOST", "rabbitmq"),
            port=int(os.getenv("RABBITMQ_PORT", "5672")),
            service_name="api_celery_worker",
            logger_url=os.getenv(
                "LOGGER_PRODUCER_URL", "http://logger:5001/api/v1/logger/log_producer"
            ),
        )

        response = event_producer.call(queue_name, json.dumps(payload_json))
        result = json.loads(response)
        celery_log.info(f"Task on queue {queue_name} completed")
        return result

    except Exception as e:
        celery_log.error(f"Task on queue {queue_name} failed: {str(e)}")
        return {"error": f"Task failed: {str(e)}"}
