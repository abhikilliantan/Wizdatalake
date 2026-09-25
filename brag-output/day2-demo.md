# Day 2 — Live demo script (for the room)

**Project:** DataLakeSkM · Foundation under NEO  
**Audience:** Sponsor / Sales / Product (non-technical OK)  
**Mode:** **Live systems only** — run commands while they watch  
**Evidence capture:** `brag-output/day2-live-evidence/` (this session)  
**Date:** 2026-09-25  

**Open before you start (4 tabs):**
1. http://localhost:8000/docs  
2. http://localhost:8000/v1/catalog/recent?limit=12  
3. http://localhost:9007 → bucket `datalake-raw` (`minioadmin` / `minioadmin`)  
4. This script + `docs/DATA_PIPELINE_FLOW.md`

**One-liner for NEO:**  
> “Today you watch data land, get audited, and get **served** to an agent-style client. That is the enforcement base for NEO — not a chatbot skin.”

---

## Pre-flight (30 seconds)

```bash
cd /home/juliunz/Skillmind/DataLakeSkM
docker compose --env-file .env up -d
# API should already be on :8000 — if not:
# PYTHONPATH=. /home/juliunz/.venvs/datalakeskm/bin/python -m ingestion.main
curl -s http://localhost:8000/health | python3 -m json.tool
```

**Say:** “Green means object store and audit ledger are reachable.”

**Pass this session:** `status: ok`, `minio_ok: true`, `catalog_ok: true`

---

## Scene 1 — Multi-source extract → load (2 min)

**Say:** “CRM, ERP, app, and files enter one hub and land in the lake.”

```bash
./scripts/demo_ingest.sh
```

**Point at:**
- Response JSON: `"status":"stored"` + `object_key` + `catalog_id`
- MinIO folders: `raw/source=salesforce|hubspot|sap|app|file/…`
- Catalog tab refreshing with new ids

**This session’s catalog ids (example):** 41 Salesforce · 42 HubSpot · 43 SAP · 44/46 app · 45 file

---

## Scene 2 — Agent serving layer (2 min) — **Day 2 differentiator**

**Say:** “Ingest alone is not enough. NEO and apps must **read** governed data. Watch an agent client discover and fetch from MinIO.”

```bash
./scripts/demo_serve.sh
```

**Point at:**
1. `GET /v1/serve/events?source=app` — discovery  
2. `GET /v1/serve/events/{id}` — **payload body** from MinIO  
3. Presigned URL — time-limited download for an external app  

**Header:** `X-Agent-Key: <same as webhook secret in .env>`

**OpenAPI:** http://localhost:8000/docs → tag **serve**

---

## Scene 3 — Stream path started (45 sec)

**Say:** “Week-3 streaming is on the bus — topic live; consumer flush is next.”

```bash
PYTHONPATH=. /home/juliunz/.venvs/datalakeskm/bin/python -m streaming.smoke
```

**Point at:** topic `datalake.ingest`, produce + consume OK.

---

## Scene 4 — Proof ledger (30 sec)

```bash
docker exec -it datalake-postgres psql -U datalake -d datalake -c \
"SELECT id, source, event_type, status, created_at FROM ingestion_events ORDER BY id DESC LIMIT 8;"
```

**Say:** “Every successful land has a row. That is how you enforce ‘what did the agent see?’ later.”

---

## Scene 5 — Tests (20 sec) — stake language

```bash
PYTHONPATH=. /home/juliunz/.venvs/datalakeskm/bin/python -m pytest tests/ -q
```

**Say:** “Untested work is a failed day. We just proved **19 passed**.”

---

## Close (30 sec)

| They ask | You answer |
|----------|------------|
| Is NEO done? | No — foundation + **serve** MVP so NEO can be grounded. Agent UX/KPIs next. |
| What do we own? | Julius PR + Abhishek `main` (serving layer merged). |
| What’s next paid slice? | AuthZ/tenancy on serve, stream flush ≥1000, DB extracts. |

**Close line:**  
> “You watched extract → lake → audit → **agent fetch**. That is Day 2. Approve this as the NEO enforcement base and we sequence the next layer.”

---

## Simulated live run checklist (tick in the room)

- [ ] Health ok  
- [ ] `demo_ingest.sh` stored rows  
- [ ] MinIO objects visible  
- [ ] `demo_serve.sh` returns payload  
- [ ] Presign URL issued  
- [ ] Stream smoke ok  
- [ ] SQL catalog latest rows  
- [ ] pytest 19 passed  

Full transcript of a completed simulation: `brag-output/day2-live-evidence/full-run.txt`
