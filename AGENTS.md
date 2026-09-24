# DataLakeSkM — OpenHands agent context

## Mission
Build a **self-hosted, vendor-agnostic data lake ingestion platform** (MVP ~20 working days). Ingest apps, CRM (Salesforce/HubSpot), flat files, and databases into **MinIO**, with **Redpanda** for streaming and **PostgreSQL** for the metadata catalog. No AWS/Azure/GCP lock-in.

## Current focus
- **Layer C — System Integration** is the active MVP delivery scope.
- Day 1 foundation exists: `docker-compose.yml`, `storage/` ObjectStorage client, catalog SQL, architecture + plan docs.
- Next: bring stack up, smoke-test MinIO writes, then integration hub / connectors.

## Architecture (read this first)
- Visual: `docs/architecture.html`
- Plan + AC-1…AC-9: `docs/INTEGRATION_DEVELOPMENT_PLAN.md`

Four layers:
1. **A Presentation** — dashboards/reports (consume only)
2. **B Sources** — apps, Salesforce, HubSpot, files, DBs
3. **C System Integration (NOW)** — hub: normalize → tag → route; event-driven (`ingestion/`) + streaming (`streaming/`) + file/DB connectors
4. **D Lake + catalog** — MinIO partitions + Postgres `ingestion_events`

## Repo map
| Path | Role |
|------|------|
| `docker-compose.yml` | MinIO, Redpanda, Postgres |
| `storage/` | ObjectStorage client (Hive partitions + tags) |
| `infra/postgres/init.sql` | Catalog schema |
| `ingestion/` | FastAPI webhooks (skeleton) |
| `streaming/` | Redpanda consumer (skeleton) |
| `tests/fixtures/` | Salesforce / HubSpot sample payloads |
| `data/incoming/` | File drop zone |

## Working rules
- Prefer implementing against the plan’s day sequence; do not expand Phase 2 (full CDC, warehouses, SSO) into MVP.
- Keep changes scoped; match existing Python style in `storage/`.
- Never commit secrets from `.env`.
- After infra changes, verify with `docker compose` health when Docker is available in the sandbox.
- Stakeholder language for Sales/PM: see `brag-output/day1-update.md`.

## Local stack ports (host)
- MinIO API `:9006` · Console `:9007`
- Redpanda Kafka `:19092`
- Postgres `:5433`
