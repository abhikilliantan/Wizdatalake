# DataLakeSkM

Self-hosted, **vendor-agnostic data lake ingestion platform**.

Apps, CRM (Salesforce / HubSpot), flat files, and databases land in **one governed lake** (MinIO) with a **catalog ledger** (PostgreSQL) and an optional **streaming bus** (Redpanda). No AWS / Azure / GCP lock-in.

> **Foundation alignment (read first):**  
> This repo is the **ingest / raw lake foundation**. It is **not** NEO.  
> NEO (industry → management agent) will consume this lake later through a **separate Agent Data Access Layer**.  
> Full contract: **[docs/FOUNDATION_ALIGNMENT.md](docs/FOUNDATION_ALIGNMENT.md)** — BA/PM sign-off.

| | |
|---|---|
| **Repo** | https://github.com/abhikilliantan/Wizdatalake |
| **Alignment** | [Foundation ↔ NEO](docs/FOUNDATION_ALIGNMENT.md) |
| **Plan status** | Draft — pending BA / PM sign-off |
| **MVP horizon** | ~20 working days + UAT (D21–D24) |

---

## 0. What this foundation is (no doubts)

| This foundation **IS** | This foundation is **NOT** |
|------------------------|----------------------------|
| How data **gets in** (webhooks, streams, files, DB extract) | How agents **reason** or manage industry KPIs |
| Raw MinIO lake + Postgres catalog | NEO’s product UI or tool runtime |
| Ops / BA **observation** presentation | Management executive experience |
| Prerequisite for NEO | “NEO is connected to company data” |

```text
NEO (future)  →  Agent Access Layer (future)  →  Curated/semantic (future)
                              ▲
                    ★ FOUNDATION (this repo / MVP)
         Sources → Integration → Raw MinIO + Catalog
```

---

## 1. Why this exists (business objectives)

| ID | Objective | Business value |
|----|-----------|----------------|
| BO-1 | Centralize raw data from all approved sources | Single source of truth for analytics / AI |
| BO-2 | Real-time and near-real-time ingestion | Faster CRM and operational visibility |
| BO-3 | Cloud-vendor agnostic | Cost control and data sovereignty |
| BO-4 | Tag and partition every object | Discoverability, audit, downstream processing |
| BO-5 | Trace every ingestion in a catalog | Compliance and ops support |

---

## 2. Architecture (design factors)

Open the interactive diagram: **[docs/architecture.html](docs/architecture.html)**.

### Four layers

| Layer | Name | Role |
|-------|------|------|
| **A** | Presentation | Ops dashboard, API docs, catalog explorer, MinIO console, BA/PM volume reports — **consume / observe only** |
| **B** | Data sources | Custom apps, Salesforce, HubSpot, flat files, PostgreSQL, MySQL (+ other RDBMS later) |
| **C** | System Integration **(MVP NOW)** | Unified hub: register → normalize → authenticate → tag → route |
| **D** | Lake + catalog | MinIO raw lake (Hive partitions + object tags) · PostgreSQL `ingestion_events` / connectors / checkpoints |

### Integration paths (Layer C)

| Path | Package | When to use |
|------|---------|-------------|
| **① Event-driven** | `ingestion/` (FastAPI) | Discrete events — CRM webhooks, app webhooks |
| **② Event-streaming** | `streaming/` (Redpanda) | Continuous / high volume; future CDC producers |
| **File connector** | drop zone / upload | CSV · JSON batches |
| **DB extract** | batch connectors | Scheduled Postgres / MySQL extracts (CDC = Phase 2) |

### Storage contract (Layer D)

- **Bucket layout (Hive-style):**  
  `raw/source=<source>/year=YYYY/month=MM/day=DD/…`
- **Object tags / metadata:** `source`, `event_type`, `object_id`, …
- **Catalog:** every successful write should get an `ingestion_events` row (**AC-7**)

Example key:

```text
raw/source=salesforce/year=2026/month=09/day=24/<uuid>.json
```

### Design principles

1. **Vendor-agnostic** — S3 API via MinIO; Kafka API via Redpanda; portable Postgres catalog.
2. **Hub-first** — one envelope + routing contract; adapters plug into the hub, not into storage directly.
3. **Raw lake + ledger** — keep raw payloads; catalog is the audit trail for presentation / UAT evidence.
4. **MVP vs Phase 2** — ship webhook + stream + batch extracts first; full CDC and warehouses later.

---

## 3. Scope

### In scope (MVP)

| Area | Included |
|------|----------|
| Infrastructure | Docker Compose: MinIO, Redpanda, PostgreSQL |
| Storage | Partitioned writes + tags (`storage/`) |
| Integration hub | Source registry, normalize, tag, route (`connectors/` — D3+) |
| Event-driven | FastAPI webhooks (apps + CRM) |
| Event-streaming | Redpanda producer/consumer → MinIO |
| CRM | Salesforce + HubSpot webhook adapters (fixture payloads first) |
| Files | CSV / JSON drop or upload API |
| Databases | Postgres + MySQL **batch extract**; CDC **design spike** only |
| Catalog | `ingestion_events`, connector registry, stream checkpoints |
| Observability | Structured logs, health, basic metrics hooks |
| Docs / UAT | Architecture, runbooks, BA acceptance pack |

### Out of scope (Phase 2)

- Full CDC production (Debezium / WAL / binlog)
- Snowflake / ClickHouse / BI warehouse consumers
- Schema registry governance UI
- Multi-tenant RBAC / SSO
- Production HA / multi-node Redpanda
- Live CRM production OAuth (sandbox first in MVP)

Tracked as: [Phase 2 CDC](https://github.com/JuliusMutugu/DataLakeSkM/issues/43)

---

## 4. Planning & delivery model

Full plan: **[docs/INTEGRATION_DEVELOPMENT_PLAN.md](docs/INTEGRATION_DEVELOPMENT_PLAN.md)**.

### Timeline

| Window | Focus | Milestone |
|--------|--------|-----------|
| Week 1 (D1–D5) | Foundation & hub skeleton | **M1** — synthetic event → lake + catalog |
| Week 2 (D6–D10) | Event-driven + CRM + files | **M2** — AC-1…AC-4 demo path |
| Week 3 (D11–D15) | Streaming + DB extracts | **M3** — AC-5, AC-6 + CDC decision |
| Week 4 (D16–D20) | Hardening & UAT prep | **M4** — ready for formal UAT |
| D21–D24 | UAT, fixes, sign-off, handover | **UAT** milestone |

### Day map (engineering)

| Day | Focus |
|-----|--------|
| D1 | Kickoff, scope freeze, ticket board, env bootstrap |
| D2 | Platform health — MinIO / Redpanda / Postgres + `put_json` smoke |
| D3 | Hub design + `connectors/` skeleton + BA source priority |
| D4 | Hub core — `SourceRegistry`, `normalize`, `route`, envelope |
| D5 | Catalog wiring on write → **M1** |
| D6 | FastAPI `/health` skeleton |
| D7 | `POST /v1/ingest/{source}` → hub → lake → catalog (**AC-3**) |
| D8 | Salesforce adapter (**AC-1**) |
| D9 | HubSpot adapter (**AC-2**) |
| D10 | Flat file ingest (**AC-4**) |
| D11 | Redpanda topic + producer helper |
| D12 | Streaming consumer batch flush |
| D13 | ≥1,000 message load test (**AC-6**) |
| D14 | Postgres batch extract (**AC-5**) |
| D15 | MySQL extract + CDC spike / Phase 2 decision |
| D16 | Errors & retries (**AC-8**) |
| D17 | Security baseline |
| D18 | Observability / correlation IDs |
| D19 | E2E regression suite |
| D20 | UAT pack + dry run |
| D21–D24 | Formal UAT → fixes → acceptance → handover |

### BA acceptance criteria (MVP done when all pass)

| ID | Criterion |
|----|-----------|
| AC-1 | Salesforce-like webhook → `raw/source=salesforce/…` |
| AC-2 | HubSpot-like webhook → `raw/source=hubspot/…` |
| AC-3 | Custom app webhook → MinIO |
| AC-4 | Flat file → correct partition path |
| AC-5 | DB table extract → lake |
| AC-6 | ≥1,000 stream messages flushed to MinIO |
| AC-7 | Catalog row per successful write |
| AC-8 | Failed ingestions logged (no silent drop) |
| AC-9 | Architecture + runbook reviewed by BA/PM |

Issues: label `acceptance` on the [issue board](https://github.com/JuliusMutugu/DataLakeSkM/issues?q=label%3Aacceptance).

### Roles (RACI summary)

| Activity | Eng | BA | PM |
|----------|-----|----|----|
| Acceptance criteria | C | **A/R** | C |
| Timeline | C | C | **A/R** |
| Architecture | **R** | C | I |
| Development | **A/R** | I | I |
| Integration demos | **R** | **A** | C |
| UAT | C | **A/R** | C |
| Go / no-go | C | C | **A** |

---

## 5. Allocating work to OpenHands

**From now on, implementation tasks are assigned to OpenHands.** Humans plan, review, and sign off; OpenHands executes against GitHub Issues.

### How to allocate a task

1. Open (or create) a GitHub Issue for the day / slice — e.g. `[D2] Platform health…` (#5).
2. In OpenHands Agent Canvas (http://localhost:8000/canvas):
   - Workspace: **`/projects/DataLakeSkM`**
   - Agent profile: **`cursor`** (Cursor ACP — uses your Cursor subscription)
3. Prompt pattern:

```text
Work GitHub issue #<N> ([D#] title).
Read AGENTS.md, docs/architecture.html notes, and docs/INTEGRATION_DEVELOPMENT_PLAN.md for that day.
Implement only that issue’s checklist. Open a PR linked to #<N>. Do not expand Phase 2 scope.
```

4. Review the PR → merge → close the issue with evidence (logs, screenshots, object keys).

### Start / stop OpenHands

```bash
./scripts/start-openhands.sh          # Docker + Cursor ACP + this repo mounted
docker rm -f openhands-datalakeskm    # stop
```

Agent context file: **[AGENTS.md](AGENTS.md)** (mission, layers, ports, rules).

### Tracking board

| Artifact | Link |
|----------|------|
| Issues | https://github.com/JuliusMutugu/DataLakeSkM/issues |
| Milestones | https://github.com/JuliusMutugu/DataLakeSkM/milestones |
| Re-seed labels/issues | `python3 scripts/seed_github_issues.py` |

Labels: `foundation`, `week-1`…`week-4`, `day`, `acceptance`, `ba-pm`, `epic`, `phase-2`, `uat`.

---

## 6. Repository map

| Path | Role |
|------|------|
| `docs/FOUNDATION_ALIGNMENT.md` | **BA/PM/NEO contract** — what foundation is / is not |
| `docs/architecture.html` | Architecture diagram (foundation boundary + NEO future) |
| `docs/INTEGRATION_DEVELOPMENT_PLAN.md` | Full BA/PM plan (scope, AC, day sequence) |
| `docker-compose.yml` | MinIO, Redpanda, Postgres, bucket init |
| `storage/` | `ObjectStorage` client — partitions + tags |
| `infra/postgres/init.sql` | Catalog schema |
| `ingestion/` | FastAPI webhooks (skeleton → D6+) |
| `streaming/` | Redpanda consumer (skeleton → D11+) |
| `tests/fixtures/` | Salesforce / HubSpot sample payloads |
| `data/incoming/` | File drop zone |
| `scripts/start-openhands.sh` | Run OpenHands + Cursor ACP |
| `scripts/seed_github_issues.py` | Seed / refresh issue board |
| `brag-output/` | Day-1 Sales/PM briefing video + copy |
| `AGENTS.md` | Instructions for OpenHands / Cursor agents |

---

## 7. Local quick start

```bash
cp .env.example .env
docker compose up -d
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest tests/ -q
```

| Service | Host port |
|---------|-----------|
| MinIO API | `:9006` |
| MinIO Console | `:9007` |
| Redpanda (Kafka) | `:19092` |
| PostgreSQL | `:5433` |

Never commit `.env`.

---

## 8. Current status

| Item | State |
|------|--------|
| Architecture + 20-day plan | Written (sign-off pending — #2) |
| GitHub board (D1–D24, ACs, milestones) | Seeded |
| Docker compose + `ObjectStorage` + partition tests | Landed (Day 1) |
| Catalog SQL init | Landed |
| OpenHands ↔ Cursor ACP | Configured for this repo |
| **Next engineering issue** | **[#5 D2 — Platform health](https://github.com/JuliusMutugu/DataLakeSkM/issues/5)** |

Allocate **#5** to OpenHands to continue.
