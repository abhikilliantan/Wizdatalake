#!/usr/bin/env bash
# Live demo: ingest → discover → serve payload to an "agent"
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
set -a
# shellcheck disable=SC1091
source .env
set +a

BASE="${DEMO_BASE_URL:-http://localhost:${INGESTION_PORT:-8000}}"
SECRET="${AGENT_ACCESS_SECRET:-${WEBHOOK_SHARED_SECRET:-dev-webhook-secret-change-me}}"
AGENT=(-H "X-Agent-Key: ${SECRET}")
INGEST=(-H "Content-Type: application/json" -H "X-Webhook-Secret: ${WEBHOOK_SHARED_SECRET:-$SECRET}")

echo "=== Serve-layer demo (agent access) ==="
echo "API: $BASE"
echo

echo "1) Health"
curl -sS "$BASE/health" | python3 -m json.tool
echo

echo "2) Ensure a fresh app event exists"
curl -sS "${INGEST[@]}" \
  -d '{"event_type":"order.created","object_id":"agent-demo-001","payload":{"sku":"NEO-WIDGET","qty":5,"plant":"Nairobi-01"},"tags":{"agent_demo":"true"}}' \
  "$BASE/v1/ingest/app" | python3 -m json.tool
echo

echo "3) Agent discovers events (filter source=app)"
LIST=$(curl -sS "${AGENT[@]}" "$BASE/v1/serve/events?source=app&limit=5")
echo "$LIST" | python3 -m json.tool
EVENT_ID=$(echo "$LIST" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d["events"][0]["id"])')
KEY=$(echo "$LIST" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d["events"][0]["object_key"])')
echo "Using catalog_id=$EVENT_ID"
echo

echo "4) Agent fetches payload from MinIO via catalog id"
curl -sS "${AGENT[@]}" "$BASE/v1/serve/events/${EVENT_ID}" | python3 -m json.tool
echo

echo "5) Presigned URL for external application download"
curl -sS "${AGENT[@]}" --get --data-urlencode "key=${KEY}" \
  "$BASE/v1/serve/objects/presign" | python3 -m json.tool
echo

echo "=== Serve demo complete ==="
echo "OpenAPI: $BASE/docs  (tag: serve)"
