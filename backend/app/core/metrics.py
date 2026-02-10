"""
In-memory metrics for observability (RPC latency, timeouts).
Thread-safe; used by EventProducer and exposed by GET /api/v1/metrics.
Enables tuning backpressure (queue depth, latency, timeouts).
"""
import threading
from collections import deque
from typing import Any, Dict

# Last N RPC latencies in seconds (thread-safe via lock)
_MAX_LATENCIES = 1000
_latencies: deque = deque(maxlen=_MAX_LATENCIES)
_counts: Dict[str, int] = {"timeouts": 0}
_lock = threading.Lock()


def record_rpc_latency(seconds: float) -> None:
    """Record a successful RPC round-trip duration (seconds)."""
    with _lock:
        _latencies.append(seconds)


def record_rpc_timeout() -> None:
    """Record an RPC timeout (no response within timeout)."""
    with _lock:
        _counts["timeouts"] += 1


def get_rpc_stats() -> Dict[str, Any]:
    """
    Return RPC metrics: count, avg, p50, p95 (seconds), timeouts_total.
    Percentiles are approximate (from last N samples).
    """
    with _lock:
        latencies = list(_latencies)
        timeouts = _counts["timeouts"]
    if not latencies:
        return {
            "latency_seconds": {"count": 0, "avg": None, "p50": None, "p95": None},
            "timeouts_total": timeouts,
        }
    n = len(latencies)
    sorted_lat = sorted(latencies)
    avg = sum(latencies) / n
    p50 = sorted_lat[int(0.50 * (n - 1))] if n else None
    p95 = sorted_lat[int(0.95 * (n - 1))] if n else None
    return {
        "latency_seconds": {
            "count": n,
            "avg": round(avg, 4),
            "p50": round(p50, 4),
            "p95": round(p95, 4),
        },
        "timeouts_total": timeouts,
    }
