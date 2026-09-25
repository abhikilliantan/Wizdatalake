# 2 PM Demo Runbook — Event-driven ingestion

**Branch:** `feature/d10-file-ingest` (or merged delivery branch)  
**What you are showing:** Foundation path ① — webhook + flat files → adapt → MinIO → catalog  
**What you are NOT claiming:** NEO agent connectivity (see `docs/FOUNDATION_ALIGNMENT.md`)

---

## Before the meeting (2 minutes)

```bash
cd /path/to/DataLakeSkM
git checkout feature/d10-file-ingest
docker compose --env-file .env up -d
set -a && source .env && set +a
PYTHONPATH=. .venv/bin/python -m ingestion.main
# leave this terminal running
```

In a second terminal:

```bash
./scripts/demo_ingest.sh
```

Open in browser:
- API docs: http://localhost:8000/docs  
- MinIO: http://localhost:9007 (user/pass: `minioadmin` / `minioadmin`)  
- Health: http://localhost:8000/health  

---

## Talk track (5–7 minutes)

1. **Alignment (30s)** — This demo is the *foundation*: data lands and is audited. NEO comes later on top.
2. **Health** — Show `/health` → `minio_ok`, `catalog_ok`, registered sources.
3. **Salesforce** — POST fixture via `/docs` or demo script → show `object_key` partition path.
4. **HubSpot** — Same flow, different source tag.
5. **SAP** — BusinessPartner CloudEvent → `raw/source=sap/…` (ERP industrial story).
6. **Flat file (AC-4)** — Upload `tests/fixtures/sample_stock.csv` via `/v1/files/upload` (or drop into `data/incoming/` and `POST /v1/files/process-incoming`) → `raw/source=file/year=…/month=…/day=…`.
7. **Agent serve (MVP access layer)** — `./scripts/demo_serve.sh` or OpenAPI tag **serve**:
   - `GET /v1/serve/events?source=app` (header `X-Agent-Key`)
   - `GET /v1/serve/events/{id}` → payload from MinIO
   - `GET /v1/serve/objects/presign?key=…` → time-limited download URL
8. **Catalog** — `/v1/catalog/recent` or SQL: every write has a row.
9. **MinIO console** — Browse `datalake-raw` → `raw/source=…/year=…/month=…/day=…`.

---

## Header for manual curl

```http
X-Webhook-Secret: dev-webhook-secret-change-me
Content-Type: application/json
```

File upload (multipart):

```bash
curl -sS -H "X-Webhook-Secret: $WEBHOOK_SHARED_SECRET" \
  -F "file=@tests/fixtures/sample_stock.csv" \
  -F "source=file" \
  http://localhost:8000/v1/files/upload
```

Drop-folder alternative:

```bash
cp tests/fixtures/sample_stock.csv data/incoming/
curl -sS -X POST -H "X-Webhook-Secret: $WEBHOOK_SHARED_SECRET" \
  http://localhost:8000/v1/files/process-incoming
# or: PYTHONPATH=. .venv/bin/python -m connectors.process_incoming
```

---

## Success criteria covered live

| AC | Evidence in this demo |
|----|------------------------|
| AC-1 | Salesforce → `raw/source=salesforce/…` |
| AC-2 | HubSpot → `raw/source=hubspot/…` |
| AC-3 | Custom app → MinIO |
| AC-4 | CSV/JSON file → `raw/source=file/year=…/month=…/day=…` |
| — | SAP BusinessPartner → `raw/source=sap/…` (demo extension) |
| AC-7 | `catalog_id` + SQL rows |
| AC-9 | Architecture + alignment docs available |

---

## If something fails

| Symptom | Fix |
|---------|-----|
| MinIO unhealthy | `docker compose --env-file .env up -d minio` |
| Catalog ping false | Check Postgres on `:5433` |
| 401 Unauthorized | Send `X-Webhook-Secret` matching `.env` |
| Port 8000 busy | `INGESTION_PORT=8005` in `.env` and restart |
