#!/usr/bin/env bash
# Trigger backend FastAPI endpoints so metrics, traces, and logs show up in SigNoz.
#
# Plan – what gets emitted:
#   Backend (FastAPI):  traces (every HTTP), metrics (RPC stats via /metrics + OTel),
#                       logs (emit_log from RabbitMQ producer on RPC).
#   Data-service:       traces (message.process span), logs (emit_log on consume).
#   Celery worker:      traces (task spans), metrics (if enabled), logs (task logs + emit_log on RPC).
#
# Endpoints used:
#   GET  /, /health           → backend only (simple traces).
#   GET  /api/v1/metrics     → backend trace + RPC/queue metrics.
#   POST /api/v1/data/process → backend → RabbitMQ RPC → data-service (traces + logs from both).
#   POST /api/v1/data/process-async → backend enqueues Celery → worker → RabbitMQ → data-service.
#   GET  /api/v1/data/process-async/{id} → backend trace; poll after async to complete flow.
#   GET  /api/v1/database/records, /api/v1/database/logs → backend traces.
#
# Usage: ./scripts/trigger-observability.sh [BASE_URL]
# Default BASE_URL: http://localhost:8081 (Nginx gateway)

set -e
BASE_URL="${1:-http://localhost:8081}"
API="${BASE_URL}/api/v1"

echo "=== Triggering endpoints for observability (traces, metrics, logs) ==="
echo "Base URL: $BASE_URL"
echo ""

# 1. Simple backend traces
echo "1. GET /"
curl -s -o /dev/null -w "   HTTP %{http_code}\n" "$BASE_URL/"

echo "2. GET /health"
curl -s -o /dev/null -w "   HTTP %{http_code}\n" "$BASE_URL/health"

# 3. Metrics endpoint (backend trace + RPC/queue metrics)
echo "3. GET /api/v1/metrics"
curl -s -o /dev/null -w "   HTTP %{http_code}\n" "$API/metrics"

# 4. Sync data processing: backend → RabbitMQ RPC → data-service (traces + logs from backend + data-service)
echo "4. POST /api/v1/data/process (sync – backend + data-service)"
SYNC_RESP=$(curl -s -w "\n%{http_code}" -X POST "$API/data/process" \
  -H "Content-Type: application/json" \
  -d '{"payload": "observability-test", "description": "trigger traces and logs"}')
SYNC_HTTP=$(echo "$SYNC_RESP" | tail -n1)
echo "   HTTP $SYNC_HTTP"
if [ "$SYNC_HTTP" != "200" ]; then
  echo "   (Sync may fail if data-service is not consuming; continuing anyway)"
fi

# 5. Async data processing: backend → Celery → RabbitMQ → data-service
echo "5. POST /api/v1/data/process-async (async – backend + Celery + data-service)"
ASYNC_RESP=$(curl -s -X POST "$API/data/process-async" \
  -H "Content-Type: application/json" \
  -d '{"payload": "async-observability", "description": "celery and data-service"}')
TASK_ID=$(echo "$ASYNC_RESP" | python3 -c "import sys, json; print(json.load(sys.stdin).get('task_id', '') or '')" 2>/dev/null || echo "")
echo "   task_id: ${TASK_ID:-<none>}"

# 6. Poll async task status (backend traces)
if [ -n "$TASK_ID" ]; then
  echo "6. GET /api/v1/data/process-async/$TASK_ID (poll until done)"
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    STATUS_RESP=$(curl -s "$API/data/process-async/$TASK_ID")
    STATUS=$(echo "$STATUS_RESP" | python3 -c "import sys, json; print(json.load(sys.stdin).get('task_status', ''))" 2>/dev/null || echo "")
    echo "   task_status: $STATUS"
    [ "$STATUS" = "Success" ] || [ "$STATUS" = "Failed" ] && break
    sleep 1
  done
else
  echo "6. (skipping poll – no task_id)"
fi

# 7. Database endpoints (backend traces)
echo "7. GET /api/v1/database/records"
curl -s -o /dev/null -w "   HTTP %{http_code}\n" "$API/database/records?limit=5"

echo "8. GET /api/v1/database/logs"
curl -s -o /dev/null -w "   HTTP %{http_code}\n" "$API/database/logs?limit=5"

# 9. Extra traffic for clearer metrics/traces
echo "9. Extra GET /health (a few more spans)"
for _ in 1 2 3; do curl -s -o /dev/null "$BASE_URL/health"; done
echo "   done"

echo ""
echo "=== Done. Check SigNoz (e.g. http://localhost:3301) for traces, metrics, and logs. ==="
