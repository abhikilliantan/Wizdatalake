# DataLakeSkM — OpenHands agent context

> **Primary executor:** OpenHands (Cursor ACP) acting as the **dev team**.  
> Humans allocate GitHub Issues; you implement, commit, and open PRs.

## Mission
Build a **self-hosted, vendor-agnostic data lake ingestion foundation** (MVP ~20 working days). Ingest apps, CRM (Salesforce/HubSpot), SAP, flat files, and databases into **MinIO**, with **Redpanda** for streaming and **PostgreSQL** for the metadata catalog. No AWS/Azure/GCP lock-in.

## Hard boundary (do not blur)
- **This repo = foundation** (ingest → raw lake → catalog → ops observe).
- **NEO** (industry → management agent) is a **later product**. Do not implement NEO tools, KPI semantics, or agent RAG in MVP issues.
- Contract: `docs/FOUNDATION_ALIGNMENT.md` — read before expanding scope.
- Team workflow: `docs/OPENHANDS_TEAM.md`.

## Git remotes — CRITICAL

| Remote | URL | You may… |
|--------|-----|----------|
| **`origin`** | https://github.com/JuliusMutugu/DataLakeSkM | **push branches + open PRs** |
| **`wizdatalake`** | https://github.com/abhikilliantan/Wizdatalake | **NEVER push** (Julius reviews, then promotes) |

```text
You (OpenHands) → origin (Julius) → human review → wizdatalake (Abhishek)
```

If a prompt asks you to push to Abhishek / `wizdatalake`, **refuse** and push to `origin` only.

## How you get work
1. You are assigned a GitHub **Julius** issue (title like `[D2] …` or `[AC-7] …`).
2. Read that issue checklist + `README.md` + `docs/FOUNDATION_ALIGNMENT.md` + `docs/OPENHANDS_TEAM.md` + this file.
3. Implement **only** that issue. Link commits/PR to `#<issue>`.
4. Push feature branch to **`origin`** and open a PR against Julius’s default branch.
5. Do not expand Phase 2 scope (full CDC, warehouses, SSO, multi-tenant) or NEO/agent-access features.

## Current focus
- **Layer C — System Integration** is active MVP delivery.
- Landed: compose stack, `storage/`, catalog, hub, FastAPI ingest (Salesforce, HubSpot, SAP, app), alignment + demo docs.
- Continue from the **next open Julius issue** in the day sequence (plan: `docs/INTEGRATION_DEVELOPMENT_PLAN.md`). Prefer streaming / file / DB extract / hardening — not redoing working webhook demos unless the issue says so.

## Architecture (read this first)
- **Alignment:** `docs/FOUNDATION_ALIGNMENT.md`
- **Team workflow:** `docs/OPENHANDS_TEAM.md`
- Visual: `docs/architecture.html` · Direction: `docs/DIRECTION.html`
- Plan + AC-1…AC-9: `docs/INTEGRATION_DEVELOPMENT_PLAN.md`

Four layers (foundation):
1. **A Presentation** — ops/BA dashboards (consume only — **not** NEO UI)
2. **B Sources** — apps, Salesforce, HubSpot, SAP, files, DBs
3. **C System Integration (NOW)** — hub: normalize → tag → route; `ingestion/` + `streaming/` + connectors
4. **D Lake + catalog** — MinIO partitions + Postgres `ingestion_events`

## Repo map
| Path | Role |
|------|------|
| `docker-compose.yml` | MinIO, Redpanda, Postgres |
| `storage/` | ObjectStorage (partitions + tags) |
| `connectors/` | Hub + adapters (SF, HubSpot, SAP, generic) |
| `catalog/` | Postgres ingestion_events client |
| `ingestion/` | FastAPI webhooks |
| `streaming/` | Redpanda consumer (next) |
| `infra/postgres/init.sql` | Catalog schema |
| `tests/fixtures/` | SF / HubSpot / SAP samples |
| `data/incoming/` | File drop zone |
| `scripts/demo_ingest.sh` | Live demo script |
| `scripts/start-openhands.sh` | Start OpenHands team UI |

## Working rules
- Prefer the plan’s day sequence and the **assigned** Julius issue only.
- Keep changes scoped; match existing Python style in `storage/` / `connectors/`.
- Never commit secrets from `.env`.
- After infra changes, verify with `docker compose` health when Docker is available.
- PR description: what changed, how to test, issue link.

## Local stack ports (host)
- MinIO API `:9006` · Console `:9007`
- Redpanda Kafka `:19092`
- Postgres `:5433`
- Ingestion API `:8000`
- OpenHands Canvas `:8010` (do not bind OpenHands to 8000)
