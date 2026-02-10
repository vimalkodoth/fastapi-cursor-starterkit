"""
Observability metrics for backpressure and tuning.
Exposes queue depth (RabbitMQ) and RPC latency/timeouts (in-memory).
"""
from fastapi import APIRouter

from app.core.metrics import get_rpc_stats
from app.core.queue_metrics import get_queue_depths

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("", response_model=dict)
def get_metrics() -> dict:
    """
    Observability metrics: queue depth and RPC stats.
    Use for backpressure tuning (queue growing, latency, timeouts).
    """
    queues = get_queue_depths()
    rpc = get_rpc_stats()
    return {"queues": queues, "rpc": rpc}
