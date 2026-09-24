# DataLakeSkM — Integration & Development Plan

**Document type:** Project Plan (BA + PM approval)  
**Version:** 1.0  
**Status:** Draft — pending BA / PM sign-off  
**Last updated:** 2026-09-24  
**Owner:** Engineering  
**Reviewers:** Business Analyst · Project Manager

---

## 1. Executive summary

We are building a **self-hosted, vendor-agnostic Data Lake ingestion platform** that ingests data from applications, CRM systems (Salesforce, HubSpot), flat files, and databases into MinIO (S3-compatible), with Redpanda for streaming and PostgreSQL for the metadata catalog.

This plan covers **integration design, development, testing, and business acceptance** over a **20 working-day (4-week) MVP cycle**, followed by a short hardening / UAT window.

| Item | Value |
|------|--------|
| Working model | Day-by-day sequence (Mon–Fri) |
| MVP target | End of Week 4 |
| UAT / sign-off | Days 21–23 |
| Go-live readiness | Day 24 (checklist + handover) |

---

## 2. Business objectives

| ID | Objective | Business value |
|----|-----------|----------------|
| BO-1 | Centralize raw data from all approved sources into one lake | Single source of truth for analytics / AI |
| BO-2 | Support real-time and near-real-time ingestion | Faster CRM and operational visibility |
| BO-3 | Remain cloud-vendor agnostic (no AWS/Azure/GCP lock-in) | Cost control and data sovereignty |
| BO-4 | Tag and partition all objects for discoverability | Auditability and downstream processing |
| BO-5 | Trace every ingestion event in a catalog | Compliance and operational support |

---

## 3. Scope

### 3.1 In scope (MVP)

| Area | Included |
|------|----------|
| Infrastructure | Docker Compose: MinIO, Redpanda, PostgreSQL |
| Storage | Partitioned writes + metadata tags to MinIO |
| Integration hub | Source registry, normalize, tag, route |
| Event-driven path | FastAPI webhooks (apps + CRM) |
| Event-streaming path | Redpanda producer/consumer → MinIO |
| CRM connectors | Salesforce + HubSpot webhook adapters (MVP payloads) |
| File ingestion | CSV / JSON drop or upload API |
| Database sources | PostgreSQL + MySQL **batch extract** (scheduled); CDC design spike |
| Catalog | `ingestion_events`, connector registry, stream checkpoints |
| Observability | Structured logs, health endpoints, basic metrics hooks |
| Docs / UAT | Architecture, runbooks, BA acceptance pack |

### 3.2 Out of scope (MVP) — deferred to Phase 2

- Full CDC (Debezium / WAL / binlog) production rollout  
- Snowflake / ClickHouse / BI warehouse consumers  
- Schema registry governance UI  
- Multi-tenant RBAC / SSO  
- Production HA / multi-node Redpanda cluster  
- Real Salesforce / HubSpot production OAuth apps (sandbox first)

Phase 2 items are **documented as backlog**, not blocked for MVP sign-off.

---

## 4. Success criteria (BA acceptance)

The BA considers MVP **accepted** when all of the following are demonstrated:

| ID | Criterion | Evidence |
|----|-----------|----------|
| AC-1 | A Salesforce-like webhook payload is ingested and stored under `raw/source=salesforce/...` | Demo + object key + tags |
| AC-2 | A HubSpot-like webhook payload is ingested and stored under `raw/source=hubspot/...` | Demo + object key + tags |
| AC-3 | A custom app event can be posted to the webhook API and appears in MinIO | curl / Postman script |
| AC-4 | A flat file (CSV or JSON) lands in the lake with correct partition path | Demo file |
| AC-5 | A sample database table extract (Postgres or MySQL) lands in the lake | Job run log + object |
| AC-6 | A stream of ≥1,000 messages through Redpanda is batch-flushed to MinIO | Load script + count |
| AC-7 | Every successful write has a catalog row in PostgreSQL | SQL query screenshot |
| AC-8 | Failed ingestions are logged and do not silently drop data | Error demo |
| AC-9 | Architecture and runbook are reviewed and understood by BA/PM | Sign-off below |

---

## 5. Roles & RACI (MVP)

| Activity | Eng | BA | PM | Ops / DevOps |
|----------|-----|----|----|--------------|
| Requirements & acceptance criteria | C | **A/R** | C | I |
| Day-by-day plan & timeline | C | C | **A/R** | I |
| Architecture | **R** | C | I | C |
| Development | **A/R** | I | I | C |
| Integration demos | **R** | **A** | C | I |
| UAT execution | C | **A/R** | C | I |
| Go / no-go | C | C | **A** | C |

**R** = Responsible · **A** = Accountable · **C** = Consulted · **I** = Informed

---

## 6. Assumptions & constraints

1. Local Docker environment is available for all engineers.  
2. Salesforce / HubSpot MVP uses **fixture payloads** first; live sandbox credentials arrive by Day 10.  
3. Source database credentials (read-only) available by Day 12.  
4. Working days are consecutive Mon–Fri unless PM adjusts for holidays.  
5. One primary engineer + BA/PM review slots; parallelization noted where helpful.  
6. “Done” for a day means code merged/ready to demo + checklist item ticked.

---

## 7. High-level phases

```
Week 1  Foundation & hub skeleton
Week 2  Event-driven + CRM + files
Week 3  Streaming + database extracts
Week 4  Hardening, UAT prep, BA/PM demos
Days 21–24  UAT, fixes, sign-off, handover
```

---

## 8. Day-by-day sequence

### Week 1 — Foundation & Integration Hub

| Day | Focus | Engineering deliverables | BA / PM involvement | Exit criteria |
|-----|--------|--------------------------|---------------------|---------------|
| **D1** | Kickoff & backlog freeze | Confirm scope vs §3; create ticket board from this plan; env bootstrap (`docker compose up`) | **BA:** confirm AC-1…AC-9 · **PM:** lock dates | Signed scope checklist |
| **D2** | Platform health | Verify MinIO / Redpanda / Postgres; smoke-test `ObjectStorage.put_json`; document ports in runbook draft | PM: risk log started | All 3 services healthy |
| **D3** | Integration hub design | Source model (`source_type`, `source_id`, tags); routing rules (webhook vs stream vs batch); package skeleton `connectors/` | **BA workshop (1h):** source priority ranking | Design note approved by BA |
| **D4** | Hub implementation (core) | `SourceRegistry`, `normalize()`, `route()`, shared envelope schema | — | Unit tests for envelope |
| **D5** | Catalog wiring | Write/read `ingestion_events` from storage path; connector registry table | PM: Week 1 checkpoint | Catalog row created on write |

**Week 1 milestone (M1):** Hub + catalog can store a synthetic event end-to-end.

---

### Week 2 — Event-driven path, CRM, files

| Day | Focus | Engineering deliverables | BA / PM involvement | Exit criteria |
|-----|--------|--------------------------|---------------------|---------------|
| **D6** | FastAPI service skeleton | `ingestion/` app, health, config, logging, Docker service optional | — | `/health` returns 200 |
| **D7** | Generic webhook endpoint | `POST /v1/ingest/{source}` → hub → MinIO → catalog | BA: sample payload review | AC-3 path works |
| **D8** | Salesforce adapter | Map fixture → envelope; tags `source=salesforce` | **BA:** field mapping review | AC-1 demo-ready |
| **D9** | HubSpot adapter | Map fixture → envelope; tags `source=hubspot` | **BA:** field mapping review | AC-2 demo-ready |
| **D10** | Flat file ingestion | Upload API or watched folder; CSV/JSON → lake | **PM:** mid-project status | AC-4 demo-ready |

**Week 2 milestone (M2):** Apps + CRM + files ingest via event-driven path (BA demo).

**BA demo #1 (end of D10 / start of D11):** Live walkthrough of AC-1, AC-2, AC-3, AC-4.

---

### Week 3 — Streaming & database sources

| Day | Focus | Engineering deliverables | BA / PM involvement | Exit criteria |
|-----|--------|--------------------------|---------------------|---------------|
| **D11** | Redpanda topics | Create `datalake.ingest`; producer helper; ACL/auth deferred | — | Topic exists; produce/consume smoke |
| **D12** | Streaming consumer | Batch flush (size/time) to MinIO + catalog + checkpoints | — | AC-6 path works at small scale |
| **D13** | Load test (stream) | Script: ≥1,000 messages; verify object count & partitions | PM: capacity note | AC-6 evidence captured |
| **D14** | DB batch extract (Postgres) | Read-only connector; table → JSON/Parquet-like JSON lines → lake | **BA:** which tables/columns | AC-5 (Postgres) |
| **D15** | DB batch extract (MySQL) + CDC spike | MySQL extract parity; **design spike** for CDC (Debezium/Redpanda Connect) → Phase 2 backlog | **BA/PM:** approve Phase 2 CDC scope | MySQL extract + CDC decision memo |

**Week 3 milestone (M3):** Streaming path + DB extracts operational; CDC deferred with BA/PM approval.

---

### Week 4 — Hardening, ops, UAT prep

| Day | Focus | Engineering deliverables | BA / PM involvement | Exit criteria |
|-----|--------|--------------------------|---------------------|---------------|
| **D16** | Error handling & retries | Dead-letter / failed status in catalog; retry policy documented | BA: failure UX expectations | AC-8 evidence |
| **D17** | Security baseline | Env secrets, webhook shared-secret header, MinIO private bucket check | PM: security checklist | Checklist complete |
| **D18** | Observability | Structured logs correlation IDs; basic `/metrics` or log dashboards notes | — | Trace one event source→lake→catalog |
| **D19** | End-to-end regression | Automate fixture-based tests for all MVP sources | — | CI/local test suite green |
| **D20** | UAT pack & dry run | Scripted UAT scenarios mapped to AC-1…AC-9; dry run with BA | **BA:** dry-run attendance | UAT pack v1 ready |

**Week 4 milestone (M4):** System ready for formal UAT.

---

### Days 21–24 — UAT, sign-off, handover

| Day | Focus | Activities | Owners |
|-----|--------|------------|--------|
| **D21** | Formal UAT | Execute AC-1…AC-9; log defects | BA (lead), Eng (support) |
| **D22** | Defect fix window | P0/P1 fixes only; retest | Eng + BA |
| **D23** | Final demo & acceptance | Full walkthrough; BA acceptance decision | BA, PM, Eng |
| **D24** | Handover | Runbooks, env vars, known issues, Phase 2 backlog; PM go/no-go record | PM (lead) |

---

## 9. Deliverables checklist

| # | Deliverable | Due | Audience |
|---|-------------|-----|----------|
| 1 | Architecture artifact (`docs/architecture.html`) | Done | All |
| 2 | This plan (approved) | D1 | BA, PM |
| 3 | Integration hub design note | D3 | BA, Eng |
| 4 | Running webhook API | D7 | Eng, BA |
| 5 | CRM adapters + fixtures | D9 | BA |
| 6 | File ingestion path | D10 | BA |
| 7 | Streaming consumer + load evidence | D13 | PM, Eng |
| 8 | DB extract jobs (PG + MySQL) | D15 | BA |
| 9 | CDC Phase 2 decision memo | D15 | BA, PM |
| 10 | UAT pack + runbook | D20 | BA, Ops |
| 11 | Acceptance record (signed) | D23 | BA, PM |

---

## 10. Risks & mitigations

| ID | Risk | Impact | Likelihood | Mitigation | Owner |
|----|------|--------|------------|------------|-------|
| R1 | Live CRM credentials delayed | Medium | Medium | Use fixtures through D10; swap sandbox later | PM |
| R2 | DB access delayed | High | Medium | Use Docker sample DBs for AC-5 | Eng |
| R3 | CDC complexity blows timeline | High | High | Batch extract in MVP; CDC spike only (D15) | PM + Eng |
| R4 | Scope creep (new sources) | High | Medium | Freeze list on D1; park in Phase 2 backlog | BA + PM |
| R5 | Partition/tag inconsistency | Medium | Low | Shared envelope enforced by hub | Eng |
| R6 | Silent data loss | High | Low | Catalog status + failed demos (D16) | Eng |

---

## 11. Communication cadence

| Cadence | Forum | Attendees | Purpose |
|---------|-------|-----------|---------|
| Daily | 15-min standup | Eng, PM (optional BA) | Blockers vs day plan |
| End of week | 30-min checkpoint | Eng, BA, PM | Milestone review M1–M4 |
| D10 / D20 / D23 | Demo | Eng, BA, PM | Acceptance evidence |
| Ad hoc | Defect triage | Eng, BA | UAT issues |

---

## 12. Definition of Done (per feature)

A feature is **Done** when:

1. Code is type-hinted, logged, and has error handling.  
2. Unit or integration test covers the happy path.  
3. Objects land in MinIO with correct `source=` partition and tags.  
4. A catalog row exists (or an explicit failed status).  
5. BA acceptance criterion (if any) is demonstrable.  
6. Runbook / README snippet updated if ops steps changed.

---

## 13. Phase 2 backlog (explicitly deferred)

| Item | Why deferred | Target window |
|------|--------------|---------------|
| Production CDC (Debezium / Redpanda Connect) | Complexity / ops | Post-MVP +2–4 weeks |
| Live Salesforce / HubSpot OAuth apps | Credential & compliance lead time | When sandbox approved |
| Additional DBs (SQL Server, Oracle, Mongo) | Priority after PG/MySQL | Phase 2 |
| Schema evolution / Iceberg or Delta layer | Needs raw lake first | Phase 2 |
| HA cluster & backup/restore drills | Ops maturity | Phase 2 |
| Alerting (Pager / Slack) | After baseline metrics | Phase 2 |

---

## 14. Approval & sign-off

By signing, reviewers confirm:

- Scope (§3) and out-of-scope are understood  
- Acceptance criteria (§4) are complete and testable  
- Day-by-day plan (§8) is achievable under stated assumptions  
- Risks (§10) are acknowledged  

| Role | Name | Date | Signature / Initials | Decision |
|------|------|------|----------------------|----------|
| Business Analyst | ________________ | ________ | ________ | ☐ Approve · ☐ Approve with changes · ☐ Reject |
| Project Manager | ________________ | ________ | ________ | ☐ Approve · ☐ Approve with changes · ☐ Reject |
| Engineering Lead | ________________ | ________ | ________ | ☐ Acknowledge |

**Change control:** After approval, scope changes require a written change request logged by the PM and re-ack by the BA.

---

## 15. Appendix A — Suggested ticket epics

1. **EPIC-INFRA** — Compose, health, config  
2. **EPIC-HUB** — Integration hub & envelope  
3. **EPIC-WEBHOOK** — FastAPI event-driven path  
4. **EPIC-CRM** — Salesforce + HubSpot adapters  
5. **EPIC-FILES** — Flat file ingestion  
6. **EPIC-STREAM** — Redpanda consumer & load test  
7. **EPIC-DB** — Postgres/MySQL batch extract + CDC spike  
8. **EPIC-CATALOG** — Metadata & checkpoints  
9. **EPIC-OPS** — Security, logging, runbooks  
10. **EPIC-UAT** — Acceptance pack & demos  

---

## 16. Appendix B — One-page timeline (print for steering)

| Week | Theme | Milestone | BA demo? |
|------|-------|-----------|----------|
| 1 | Foundation + hub | M1 Synthetic E2E | Soft review D3 |
| 2 | Webhooks + CRM + files | M2 Event-driven MVP | **Yes — D10** |
| 3 | Streaming + DB extract | M3 Streams + DB | Soft review D15 |
| 4 | Harden + UAT prep | M4 UAT-ready | Dry run D20 |
| +4d | UAT + sign-off | Accepted MVP | **Yes — D23** |

---

*End of plan — DataLakeSkM Integration & Development Plan v1.0*
