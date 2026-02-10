"""
Queue depth from RabbitMQ Management API for observability.
Used by GET /api/v1/metrics to expose queue depth (backpressure signal).
"""
import os
from typing import Any, Dict, List, Optional

import requests

# Default vhost "/" is URL-encoded as %2F
_VHOST = "%2F"
_REQUEST_TIMEOUT = 5


def _management_url() -> str:
    """Base URL for RabbitMQ Management API (e.g. http://guest:welcome1@rabbitmq:15672)."""
    base = os.getenv(
        "RABBITMQ_MANAGEMENT_URL",
        (
            f"http://{os.getenv('RABBITMQ_USER', 'guest')}:"
            f"{os.getenv('RABBITMQ_PASSWORD', 'welcome1')}@"
            f"{os.getenv('RABBITMQ_HOST', 'rabbitmq')}:"
            f"{os.getenv('RABBITMQ_MANAGEMENT_PORT', '15672')}"
        ),
    )
    return base.rstrip("/")


def get_queue_depths(
    queue_names: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Fetch queue depths from RabbitMQ Management API.
    Returns dict keyed by queue name with messages, messages_ready, messages_unacknowledged.
    On error returns {"error": "..."} and no queue keys.
    """
    if queue_names is None:
        queue_names = ["data_queue", "data_queue_dlq"]
    base = _management_url()
    result: Dict[str, Any] = {}
    for name in queue_names:
        url = f"{base}/api/queues/{_VHOST}/{name}"
        try:
            resp = requests.get(url, timeout=_REQUEST_TIMEOUT)
            if resp.status_code != 200:
                result[name] = {"error": f"HTTP {resp.status_code}"}
                continue
            data = resp.json()
            result[name] = {
                "messages": data.get("messages", 0),
                "messages_ready": data.get("messages_ready", 0),
                "messages_unacknowledged": data.get("messages_unacknowledged", 0),
            }
        except requests.RequestException as e:
            result[name] = {"error": str(e)}
        except (KeyError, TypeError) as e:
            result[name] = {"error": f"Invalid response: {e}"}
    return result
