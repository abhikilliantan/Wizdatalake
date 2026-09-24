# DataLakeSkM

Self-hosted, vendor-agnostic **data lake ingestion platform** — apps, CRM (Salesforce / HubSpot), files, and databases → **MinIO**, with **Redpanda** streaming and **PostgreSQL** catalog. No AWS / Azure / GCP lock-in.

## Docs
- [Architecture](docs/architecture.html) — open in a browser
- [Integration & Development Plan](docs/INTEGRATION_DEVELOPMENT_PLAN.md) — 20-day MVP + AC-1…AC-9
- [AGENTS.md](AGENTS.md) — context for coding agents (OpenHands / Cursor)

## Stack
| Layer | Tech |
|-------|------|
| Lake | MinIO (S3) |
| Stream | Redpanda (Kafka API) |
| Catalog | PostgreSQL |
| Storage client | `storage/` (Hive partitions + object tags) |
| Ingestion (MVP) | FastAPI webhooks · hub · streaming consumer |

## Quick start
```bash
cp .env.example .env
docker compose up -d
python -m pytest tests/ -q
```

Ports (host): MinIO `:9006` / console `:9007` · Redpanda `:19092` · Postgres `:5433`

## Tracking
Work is tracked as GitHub Issues by day (**D1–D24**), milestones **M1–M4**, and acceptance criteria **AC-1…AC-9**.  
OpenHands + Cursor ACP: `./scripts/start-openhands.sh` → http://localhost:8000/canvas

## Status
Day 1 foundation landed (compose, `ObjectStorage`, catalog schema, architecture, plan). Next: **D2 platform health**.
