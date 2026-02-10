#!/usr/bin/env bash
# Test the async data processing flow (Celery).
# Usage: ./scripts/test-async-flow.sh [API_BASE_URL]
# Example: ./scripts/test-async-flow.sh http://localhost:8000

set -e
API="${1:-http://localhost:8000}"
API_V1="${API}/api/v1"

echo "1. Submit async task (POST /api/v1/data/process-async)"
RESP=$(curl -s -X POST "${API_V1}/data/process-async" \
  -H "Content-Type: application/json" \
  -d '{"payload": "hello async", "description": "uppercase"}')
echo "$RESP" | head -1

TASK_ID=$(echo "$RESP" | python3 -c "import sys, json; print(json.load(sys.stdin).get('task_id', ''))")
if [ -z "$TASK_ID" ]; then
  echo "Failed to get task_id. Response: $RESP"
  exit 1
fi
echo "   task_id: $TASK_ID"
echo ""

echo "2. Poll until done (GET /api/v1/data/process-async/{task_id})"
while true; do
  STATUS_RESP=$(curl -s -w "\n%{http_code}" "${API_V1}/data/process-async/${TASK_ID}")
  HTTP_CODE=$(echo "$STATUS_RESP" | tail -n1)
  BODY=$(echo "$STATUS_RESP" | sed '$d')
  STATUS=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('task_status', ''))" 2>/dev/null || echo "")

  echo "   HTTP $HTTP_CODE | task_status: $STATUS"
  if [ "$STATUS" = "Success" ]; then
    echo ""
    echo "3. Result:"
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
    exit 0
  fi
  if [ "$STATUS" = "Failed" ] || [ "$STATUS" = "failed" ]; then
    echo "   Task failed. Response: $BODY"
    exit 1
  fi
  sleep 1
done
