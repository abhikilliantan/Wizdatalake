#!/usr/bin/env bash
# Simulated live Day-2 demo for the room — runs real systems with spoken beats.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
VENV="${VENV:-$HOME/.venvs/datalakeskm}"
PY="${VENV}/bin/python"
[[ -x "$PY" ]] || PY=python3

set -a
# shellcheck disable=SC1091
source .env
set +a

beat() { echo; echo "======== $1 ========"; echo "$2"; echo; sleep "${3:-1}"; }

beat "DAY 2 DEMO" "DataLakeSkM — extract → MinIO → catalog → agent serve (NEO base)" 1

beat "1 · HEALTH" "Object store + audit ledger must be green." 0
curl -sS "http://localhost:${INGESTION_PORT:-8000}/health" | "$PY" -m json.tool

beat "2 · MULTI-SOURCE INGEST" "Salesforce, HubSpot, SAP, app, files → lake (watch stored + object_key)." 0
./scripts/demo_ingest.sh

beat "3 · AGENT SERVE" "External agent discovers events and fetches MinIO payload + presign URL." 0
./scripts/demo_serve.sh

beat "4 · STREAM SMOKE" "Redpanda topic datalake.ingest produce/consume." 0
PYTHONPATH=. "$PY" -m streaming.smoke

beat "5 · CATALOG LEDGER" "SQL proof of what landed." 0
docker exec datalake-postgres psql -U datalake -d datalake -c \
  "SELECT id, source, event_type, status, created_at FROM ingestion_events ORDER BY id DESC LIMIT 8;"

beat "6 · AUTOMATED TESTS" "Failing to test assures failure — we run pytest." 0
PYTHONPATH=. "$PY" -m pytest tests/ -q --tb=line

beat "CLOSE" "Day 2 shown live: ingest + serve. NEO enforcement base is runnable. Evidence: brag-output/day2-live-evidence/" 1
