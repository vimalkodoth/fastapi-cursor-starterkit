"""
Service communication helpers and dependencies.
"""
import json
import os
from typing import Any, Dict, Optional

import requests
from sqlmodel import Session

from app.core.database import engine
from app.infrastructure.rabbitmq import EventProducer
from app.models.database import TaskLog


def _write_task_log_sync(
    correlation_id: str,
    queue_name: str,
    service_name: str,
    status: str,
    description: str,
    task_type: str,
) -> None:
    """Write a single task log row to task_logs (sync, for use from EventProducer)."""
    with Session(engine) as session:
        log = TaskLog(
            task_id=correlation_id,
            correlation_id=correlation_id,
            queue_name=queue_name,
            service_name=service_name,
            task_type=task_type,
            description=description or None,
            status=status,
        )
        session.add(log)
        session.commit()


def call_service_via_rabbitmq(
    queue_name: str, payload: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Call a microservice via RabbitMQ using EventProducer (RPC pattern).
    Raises ValueError with a descriptive message on failure (API layer should map to HTTPException).
    """
    try:
        event_producer = EventProducer(
            username=os.getenv("RABBITMQ_USER", "guest"),
            password=os.getenv("RABBITMQ_PASSWORD", "welcome1"),
            host=os.getenv("RABBITMQ_HOST", "rabbitmq"),
            port=int(os.getenv("RABBITMQ_PORT", "5672")),
            service_name="api_sync",
            on_log_event=_write_task_log_sync,
        )

        response = event_producer.call(queue_name, json.dumps(payload))
        parsed = json.loads(response)
        if isinstance(parsed, dict) and "error" in parsed:
            raise ValueError(parsed["error"])
        return parsed
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"RabbitMQ call failed: {str(e)}") from e


def call_service_via_http(
    service_url: str, payload: Dict[str, Any], timeout: int = 30
) -> Dict[str, Any]:
    """
    Call a microservice via HTTP.
    Raises ValueError on failure (API layer should map to HTTPException).
    """
    try:
        response = requests.post(service_url, json=payload, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise ValueError(f"HTTP call failed: {str(e)}") from e


def call_service(
    service_url: Optional[str] = None,
    queue_name: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    use_rabbitmq: bool = True,
) -> Dict[str, Any]:
    """
    Unified function to call a service either via RabbitMQ or HTTP.
    Raises ValueError if required args are missing or the call fails.
    """
    if payload is None:
        payload = {}

    if use_rabbitmq:
        if not queue_name:
            raise ValueError("queue_name is required for RabbitMQ calls")
        return call_service_via_rabbitmq(queue_name, payload)
    if not service_url:
        raise ValueError("service_url is required for HTTP calls")
    return call_service_via_http(service_url, payload)


def get_service_url(service_name: str) -> str:
    """
    Get service URL from environment variable or construct default.
    """
    env_key = f"{service_name.upper()}_SERVICE_URL"
    default_port = 5000  # Default port for microservices
    return os.getenv(
        env_key, f"http://{service_name}-service:{default_port}/api/v1/{service_name}"
    )


def get_queue_name(service_name: str) -> str:
    """
    Get queue name from environment variable or construct default.
    """
    env_key = f"{service_name.upper()}_QUEUE_NAME"
    return os.getenv(env_key, f"{service_name}_queue")
