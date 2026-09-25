#!/usr/bin/env bash
# Create datalake.ingest on local Redpanda (idempotent).
# Used by docker compose redpanda-init and can be run from the host via rpk in-container.
set -euo pipefail

TOPIC="${KAFKA_TOPIC_INGEST:-datalake.ingest}"
PARTITIONS="${KAFKA_TOPIC_PARTITIONS:-1}"
RF="${KAFKA_TOPIC_REPLICATION_FACTOR:-1}"
BROKERS="${REDPANDA_BROKERS:-redpanda:9092}"

echo "Waiting for Redpanda at ${BROKERS}..."
until rpk cluster health -X brokers="${BROKERS}" 2>/dev/null | grep -E 'Healthy:.+true' >/dev/null; do
  sleep 2
done

echo "Ensuring topic: ${TOPIC} (partitions=${PARTITIONS}, rf=${RF})"
if rpk topic list -X brokers="${BROKERS}" | awk 'NR>1 {print $1}' | grep -qx "${TOPIC}"; then
  echo "Topic already exists: ${TOPIC}"
else
  rpk topic create "${TOPIC}" \
    -X brokers="${BROKERS}" \
    -p "${PARTITIONS}" \
    -r "${RF}"
  echo "Created topic: ${TOPIC}"
fi

rpk topic describe "${TOPIC}" -X brokers="${BROKERS}"
