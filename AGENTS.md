# DataLakeSkM — OpenHands agent context

> **Primary executor:** OpenHands (Cursor ACP). Humans allocate GitHub Issues; you implement them and open PRs.

## Mission
Build a **self-hosted, vendor-agnostic data lake ingestion foundation** (MVP ~20 working days). Ingest apps, CRM (Salesforce/HubSpot), flat files, and databases into **MinIO**, with **Redpanda** for streaming and **PostgreSQL** for the metadata catalog. No AWS/Azure/GCP lock-in.

## Hard boundary (do not blur)
- **This repo = foundation** (ingest → raw lake → catalog → ops observe).
- **NEO** (industry → management agent) is a **later product**. Do not implement NEO tools, KPI semantics, or agent RAG in MVP issues.
- Contract: `docs/FOUNDATION_ALIGNMENT.md` — read before expanding scope.

## How you get work
1. You are assigned a GitHub issue (title like `[D2] …` or `[AC-7] …`).
2. Read that issue checklist + `README.md` + `docs/FOUNDATION_ALIGNMENT.md` + this file.
3. Implement **only** that issue. Link commits/PR to `#<issue>`.
4. Do not expand Phase 2 scope (full CDC, warehouses, SSO, multi-tenant) or NEO/agent-access features.

## Current focus
- **Layer C — System Integration** is the active MVP delivery scope.
- Day 1 foundation exists: `docker-compose.yml`, `storage/` ObjectStorage client, catalog SQL, architecture + plan docs, GitHub board.
- Next human allocation: **D2 platform health** (`docker compose up` + `ObjectStorage.put_json` smoke) — issue #5.

## Architecture (read this first)
- **Alignment (foundation vs NEO):** `docs/FOUNDATION_ALIGNMENT.md`
- Visual: `docs/architecture.html`
- Plan + AC-1…AC-9: `docs/INTEGRATION_DEVELOPMENT_PLAN.md`
- Human overview: `README.md`

Four layers (foundation):
1. **A Presentation** — ops/BA dashboards (consume only — **not** NEO UI)
2. **B Sources** — apps, Salesforce, HubSpot, files, DBs
3. **C System Integration (NOW)** — hub: normalize → tag → route; event-driven (`ingestion/`) + streaming (`streaming/`) + file/DB connectors
4. **D Lake + catalog** — MinIO partitions + Postgres `ingestion_events`

Above the foundation (do not build in MVP): Agent Data Access Layer → NEO.

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

## GitHub
- Repo: https://github.com/abhikilliantan/Wizdatalake
- Work in small PRs tied to day issues (`[D2]`, `[D3]`, …). Reference issue numbers in commits.
- Do not expand Phase 2 (full CDC, warehouses, SSO) or NEO into MVP.

## Working rules
- Prefer implementing against the plan’s day sequence and the **assigned** GitHub issue only.
- Keep changes scoped; match existing Python style in `storage/`.
- Never commit secrets from `.env`.
- After infra changes, verify with `docker compose` health when Docker is available in the sandbox.
- Stakeholder language for Sales/PM: see `brag-output/day1-update.md`.

## Local stack ports (host)
- MinIO API `:9006` · Console `:9007`
- Redpanda Kafka `:19092`
- Postgres `:5433`
