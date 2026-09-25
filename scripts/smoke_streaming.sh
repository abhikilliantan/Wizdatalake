#!/usr/bin/env bash
# D11 demo — ensure topic + produce/consume smoke against local Redpanda.
# Prerequisites: docker compose up -d redpanda redpanda-init
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

set -a
# shellcheck disable=SC1091
[[ -f .env ]] && source .env
set +a

export KAFKA_BOOTSTRAP_SERVERS="${KAFKA_BOOTSTRAP_SERVERS:-localhost:19092}"
export KAFKA_TOPIC_INGEST="${KAFKA_TOPIC_INGEST:-datalake.ingest}"

echo "=== D11 Redpanda smoke ==="
echo "Bootstrap: ${KAFKA_BOOTSTRAP_SERVERS}"
echo "Topic:     ${KAFKA_TOPIC_INGEST}"
echo

if command -v docker >/dev/null 2>&1; then
  DOCKER=(docker)
  docker info >/dev/null 2>&1 || DOCKER=(sudo docker)
  echo "1) Topic list (rpk in redpanda container)"
  "${DOCKER[@]}" exec datalake-redpanda rpk topic list -X brokers=localhost:9092 || true
  echo
fi

echo "2) Python produce/consume smoke"
PYTHONPATH=. "${ROOT}/.venv/bin/python" -m streaming.smoke
echo
echo "=== D11 smoke complete ==="
