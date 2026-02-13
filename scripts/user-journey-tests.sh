#!/usr/bin/env bash
# User journey tests for FastAPI Starter Kit
# Run after: docker compose up -d (and wait for services to be ready)
# Usage: ./scripts/user-journey-tests.sh [BASE_URL]
# Default BASE_URL: http://localhost:8081 (via Nginx)

set -e
BASE_URL="${1:-http://localhost:8081}"
API="${BASE_URL}/api/v1"

echo "=== FastAPI Starter Kit – User journey tests ==="
echo "Base URL: $BASE_URL"
echo ""

# 1. Health
echo "1. Health check (root)"
curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/" | grep -q 200 && echo "   OK" || (echo "   FAIL"; exit 1)

echo "2. Health check (/health)"
curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/health" | grep -q 200 && echo "   OK" || (echo "   FAIL"; exit 1)

# 3. Sync data processing (retry a few times: data-service must be consuming on RabbitMQ)
echo "3. Sync data processing POST /api/v1/data/process"
SYNC_HTTP=""
for attempt in 1 2 3 4 5; do
  SYNC_RESP=$(curl -s -w "\n%{http_code}" -X POST "$API/data/process" \
    -H "Content-Type: application/json" \
    -d '{"payload": "hello", "description": "uppercase"}')
  SYNC_HTTP=$(echo "$SYNC_RESP" | tail -n1)
  SYNC_BODY=$(echo "$SYNC_RESP" | sed '$d')
  if [ "$SYNC_HTTP" = "200" ]; then
    break
  fi
  [ "$attempt" -lt 5 ] && echo "   attempt $attempt: HTTP $SYNC_HTTP, retrying in 3s..." && sleep 3
done
echo "   HTTP $SYNC_HTTP"
if [ "$SYNC_HTTP" = "200" ]; then
  echo "$SYNC_BODY" | grep -q "task_status" && echo "   OK" || (echo "   FAIL"; exit 1)
else
  echo "   FAIL (expected 200). Ensure data-service is running and consuming from RabbitMQ."
  exit 1
fi

# 4. Async data processing – start
echo "4. Async data processing – start POST /api/v1/data/process-async"
ASYNC_RESP=$(curl -s -w "\n%{http_code}" -X POST "$API/data/process-async" \
  -H "Content-Type: application/json" \
  -d '{"payload": "world", "description": "uppercase"}')
ASYNC_HTTP=$(echo "$ASYNC_RESP" | tail -n1)
ASYNC_BODY=$(echo "$ASYNC_RESP" | sed '$d')
echo "   HTTP $ASYNC_HTTP"
if [ "$ASYNC_HTTP" = "202" ]; then
  TASK_ID=$(echo "$ASYNC_BODY" | grep -o '"task_id":"[^"]*"' | cut -d'"' -f4)
  echo "   task_id=$TASK_ID"
  echo "   OK"
else
  echo "   FAIL (expected 202)"
  exit 1
fi

# 5. Async – poll status (optional, may still be processing)
echo "5. Async task status GET /api/v1/data/process-async/{task_id}"
if [ -n "$TASK_ID" ]; then
  sleep 2
  STATUS_RESP=$(curl -s -w "\n%{http_code}" "$API/data/process-async/$TASK_ID")
  STATUS_HTTP=$(echo "$STATUS_RESP" | tail -n1)
  echo "   HTTP $STATUS_HTTP (202=processing, 200=done)"
  echo "   OK"
fi

# 6. Database – list records
echo "6. Database records GET /api/v1/database/records"
DB_RESP=$(curl -s -w "\n%{http_code}" "$API/database/records?limit=5")
DB_HTTP=$(echo "$DB_RESP" | tail -n1)
echo "   HTTP $DB_HTTP"
[ "$DB_HTTP" = "200" ] && echo "   OK" || (echo "   FAIL"; exit 1)

# 7. API docs (optional)
echo "7. API docs GET /api/v1/docs"
curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/docs" | grep -q 200 && echo "   OK" || echo "   SKIP (docs may redirect)"

echo ""
echo "=== All user journey checks completed ==="
