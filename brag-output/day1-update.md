# Day 1 briefing — Sales Manager & Product Manager

**Project:** DataLakeSkM  
**Date:** 2026-09-24  
**Audience:** Sales Manager · Product Manager  
**Attach:** `docs/architecture.html` (open in browser)

---

## What we are building (plain language)

We are building a **company-owned data lake** — one place where data from our apps, CRM (Salesforce / HubSpot), files, and databases lands so analytics, AI, and operations can use it later.

It is **self-hosted and vendor-agnostic**: we are not locking the product into AWS, Azure, or Google Cloud. That matters for cost, data control, and how we sell / position the platform.

---

## How the architecture works (4 layers)

Walk people top-to-bottom on the diagram:

### A — Presentation (what people look at)
Dashboards, API docs, catalog browser, storage console, and BA/PM volume reports.  
**Role:** see health, volumes, and evidence — **not** where source data is written.

### B — Data sources (where business data comes from)
- Custom apps  
- Salesforce & HubSpot (CRM events)  
- Flat files (CSV / JSON)  
- Databases (PostgreSQL, MySQL; more later)

### C — System Integration — **this is what we are delivering in the MVP (NOW)**
One **unified integration hub** that accepts data, cleans/normalizes it, tags it, and routes it.

Two ways data enters (both matter commercially):

| Path | Business meaning | Example |
|------|------------------|---------|
| **① Event-driven** | Something happened → we capture it soon after | Contact updated in Salesforce / HubSpot; app webhook |
| **② Event-streaming** | Continuous / high-volume flow | App event streams; later near-real-time DB change (CDC = Phase 2) |

Also: file upload/drop and scheduled database extracts.

### D — Lake + catalog (where truth lives)
- **Data lake (MinIO):** the actual raw files, organized by source and date so we can find and reuse them  
- **Catalog (PostgreSQL):** the ledger — what came in, from where, when, success/fail  

Presentation (layer A) reads from D. Integration (layer C) writes into D.

---

## Why this design (talking points)

| Stakeholder ask | Answer |
|-----------------|--------|
| **Sales — “What do we sell?”** | A platform that centralizes CRM + app + file + DB data into one governed lake, without forcing a hyperscaler. |
| **Sales — “Why not just Salesforce reports?”** | CRM is one source. The lake holds *all* approved sources in one place for analytics / AI / ops. |
| **Product — “What’s the MVP promise?”** | Ingest from apps, Salesforce, HubSpot, files, and DB extracts into a partitioned lake, with a catalog trail for every successful write. |
| **Product — “What’s *not* in MVP?”** | Full live CDC production, warehouse/BI tools, multi-tenant SSO, heavy HA — documented as Phase 2. |
| **Both — “How do we know it works?”** | Nine acceptance checks (AC-1…AC-9): e.g. Salesforce/HubSpot sample events land in the lake under the right source; catalog has a row for each write. |

---

## Day 1 status (what we did today)

**Progress:** foundation and alignment, not customer-facing features yet.

1. **Architecture agreed in writing** — the diagram above (`docs/architecture.html`)  
2. **20-day MVP plan drafted** — scope, acceptance criteria, week-by-week delivery (`docs/INTEGRATION_DEVELOPMENT_PLAN.md`) — **needs your sign-off**  
3. **Platform foundation started** — storage layout (by source + date), catalog schema, local stack definition (lake + stream bus + catalog DB)

**Ask of you (Sales / Product):**
- Confirm MVP scope and acceptance criteria in the plan  
- Confirm source priority (which CRM / apps / DBs matter first for demos and pipeline stories)

**Next (Day 2):** bring the local platform up and prove a first write into the lake (health check).

---

## One-paragraph email / Slack version

> Day 1 on DataLakeSkM: we locked the architecture for a self-hosted data lake that pulls apps, Salesforce/HubSpot, files, and databases into one place — without cloud lock-in. The MVP focus is the **System Integration** layer (hub + webhooks + streaming + extracts) writing into a tagged lake and a catalog so Sales/Product can later show volumes and UAT evidence. Architecture diagram and 20-day plan are ready for your review and sign-off; tomorrow we smoke-test the foundation stack.
