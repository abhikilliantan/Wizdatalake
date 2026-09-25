#!/usr/bin/env bash
# Demo script for BA/PM — webhook → MinIO → catalog
# Usage: ./scripts/demo_ingest.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

set -a
# shellcheck disable=SC1091
source .env
set +a

BASE_URL="${DEMO_BASE_URL:-http://localhost:${INGESTION_PORT:-8000}}"
SECRET="${WEBHOOK_SHARED_SECRET:-dev-webhook-secret-change-me}"
HDR=(-H "Content-Type: application/json" -H "X-Webhook-Secret: ${SECRET}")

echo "=== DataLakeSkM demo ==="
echo "API: $BASE_URL"
echo

echo "1) Health"
curl -sS "$BASE_URL/health" | python3 -m json.tool
echo

echo "2) Salesforce fixture → /v1/ingest/salesforce"
curl -sS "${HDR[@]}" \
  -d @"$ROOT/tests/fixtures/salesforce_contact_updated.json" \
  "$BASE_URL/v1/ingest/salesforce" | python3 -m json.tool
echo

echo "3) HubSpot fixture → /v1/ingest/hubspot"
curl -sS "${HDR[@]}" \
  -d @"$ROOT/tests/fixtures/hubspot_contact_property_change.json" \
  "$BASE_URL/v1/ingest/hubspot" | python3 -m json.tool
echo

echo "4) SAP BusinessPartner fixture → /v1/ingest/sap"
curl -sS "${HDR[@]}" \
  -d @"$ROOT/tests/fixtures/sap_business_partner_changed.json" \
  "$BASE_URL/v1/ingest/sap" | python3 -m json.tool
echo

echo "5) Custom app event → /v1/ingest/app"
curl -sS "${HDR[@]}" \
  -d '{"event_type":"order.created","object_id":"demo-ord-001","payload":{"sku":"WIDGET","qty":3,"plant":"Nairobi-01"},"tags":{"demo":"true"}}' \
  "$BASE_URL/v1/ingest/app" | python3 -m json.tool
echo

echo "6) Recent catalog rows"
curl -sS "$BASE_URL/v1/catalog/recent?limit=8" | python3 -m json.tool
echo

echo "=== Demo complete ==="
echo "MinIO console: ${MINIO_CONSOLE_URL:-http://localhost:9007}  (minioadmin / minioadmin)"
echo "OpenAPI docs:  $BASE_URL/docs"
