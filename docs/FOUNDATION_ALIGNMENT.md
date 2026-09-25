# Foundation Alignment — DataLakeSkM ↔ NEO

**Document type:** Alignment contract (BA · PM · Engineering · NEO product)  
**Version:** 1.0  
**Status:** Proposed for sign-off  
**Last updated:** 2026-09-25  
**Related:** [INTEGRATION_DEVELOPMENT_PLAN.md](./INTEGRATION_DEVELOPMENT_PLAN.md) · [architecture.html](./architecture.html)

---

## 1. One-sentence truth

> **DataLakeSkM Foundation = how industrial and business data gets into a governed raw lake.**  
> **NEO = how management agents later discover, query, and act on that data.**  
> They are **sequential layers**, not the same product.

If someone says “the lake is the agent,” that is **out of alignment**.

---

## 2. Problem we are solving (and not solving)

### In scope for this foundation

| Problem | Foundation answer |
|---------|-------------------|
| Data is trapped in apps, CRM, files, and DBs | Ingest into one self-hosted lake (MinIO) |
| No single audit trail of what landed | PostgreSQL catalog (`ingestion_events`) |
| Cloud vendor lock-in | MinIO + Redpanda + Postgres (open stack) |
| Objects are unfindable later | Hive partitions + tags (`source`, `event_type`, …) |
| Mixed sync styles | Event-driven webhooks **and** streaming **and** batch extract |

### Explicitly **out** of foundation scope (NEO / later layers)

| Problem | Who owns it later |
|---------|-------------------|
| Agent “connects” and reasons over data | **NEO + Agent Data Access Layer** |
| Industry KPIs, plant/P&L semantics | **Semantic / metrics layer** |
| Natural-language or tool-calling retrieval | **NEO tools / MCP / RAG / query APIs** |
| Who may see which tenant / site / customer | **AuthZ / governance for agents** |
| Executive dashboards as product UX | **NEO presentation / management UI** |
| Full CDC production (WAL / binlog) | **Phase 2 of the lake** (optional feed into same lake) |

---

## 3. Layer contract (no ambiguity)

```text
┌─────────────────────────────────────────────────────────────┐
│  NEO  —  Industrial → Management Agent                      │
│  Plans · asks · decides · acts  (FUTURE PRODUCT)            │
└───────────────────────────▲─────────────────────────────────┘
                            │  tools / APIs / governed queries
┌───────────────────────────┴─────────────────────────────────┐
│  Agent Data Access Layer  (PLANNED — after foundation)      │
│  Catalog API · semantic models · query/RAG · authZ          │
└───────────────────────────▲─────────────────────────────────┘
                            │  reads curated + catalogued data
┌───────────────────────────┴─────────────────────────────────┐
│  Curated / semantic lake  (PLANNED — silver/gold)           │
│  Contracts · KPIs · industry entities                       │
└───────────────────────────▲─────────────────────────────────┘
                            │  transforms from raw
╔═══════════════════════════╩═════════════════════════════════╗
║  ★ FOUNDATION BOUNDARY (THIS REPO / MVP)                    ║
║  Sources → System Integration → Raw MinIO + Catalog Postgres║
║  Presentation here = ops / BA observe only (not NEO product)║
╚═════════════════════════════════════════════════════════════╝
```

**Rule:** Nothing above the foundation boundary is required for MVP sign-off.  
**Rule:** Nothing inside the foundation pretends to be NEO.

---

## 4. What “done foundation” means

The foundation is **aligned and complete for its job** when:

1. Approved sources can land in MinIO under  
   `raw/source=<source>/year=/month=/day=/…`
2. Every successful write is **tagged** and has a **catalog row**.
3. Failed writes are **visible** (no silent drop).
4. Ops / BA can **observe** intake (console, catalog, UAT evidence).
5. The lake is **self-hosted** and portable (no AWS/Azure/GCP dependency).

The foundation is **not** done when NEO can answer “what is plant utilization this week?”  
That is a **later layer** success criterion.

---

## 5. How this foundation unblocks NEO

NEO needs trustworthy inputs. The foundation provides:

| NEO need | Foundation delivers | Still missing for NEO |
|----------|---------------------|------------------------|
| Durable history | Raw objects in MinIO | Query API over those objects |
| Provenance | Tags + `ingestion_events` | Agent-readable catalog API |
| Multi-source truth | Hub + connectors | Semantic join / industry ontology |
| Low lock-in | Open stack | NEO deployment / tool host |
| Fresh enough data | Webhooks + streams + extracts | SLA policies NEO can trust |

**Alignment statement for PM/BA:**  
Building the lake first avoids NEO sitting on fragile CSV drops and one-off CRM exports.  
Building NEO on top of an unfinished lake creates false confidence.

---

## 6. Shared vocabulary (use these words only)

| Term | Meaning here |
|------|----------------|
| **Foundation / DataLakeSkM** | Ingest + raw store + catalog + ops presentation |
| **System Integration** | Hub, webhooks, streaming, file/DB connectors (MVP build) |
| **Raw lake** | Untouched / lightly normalized payloads in MinIO |
| **Catalog** | Platform Postgres ledger of what was ingested |
| **Presentation (MVP)** | Ops / BA / PM observation — **not** NEO’s management UI |
| **Agent Data Access Layer** | Future APIs/tools NEO calls |
| **NEO** | Industry-to-management agent product (consumer of the lake) |
| **Semantic / gold layer** | Future curated models & KPIs for management decisions |

---

## 7. Decision log (locked unless change-controlled)

| ID | Decision | Rationale |
|----|----------|-----------|
| D-01 | Foundation does **not** include NEO runtime | Clear ownership; avoid scope collapse |
| D-02 | MVP presentation ≠ NEO UI | Ops observability only |
| D-03 | Raw-first; silver/gold after MVP | Stable intake before semantics |
| D-04 | Agent access is a **separate workstream** after M4/UAT | Depends on catalog + raw reliability |
| D-05 | CDC full rollout is Phase 2 | Batch extract is enough for foundation demos |
| D-06 | All agent reads go through access layer, not direct MinIO creds | Security & audit for industry data |

---

## 8. Success criteria split

### Foundation (BA acceptance — existing AC-1…AC-9)

Evidence of **ingestion correctness** (webhooks, files, DB extract, stream flush, catalog, failures).

### NEO readiness (future — not MVP)

| ID | Criterion (later) |
|----|-------------------|
| NR-1 | NEO can list available datasets via catalog API |
| NR-2 | NEO can retrieve a scoped answer for one industry KPI |
| NR-3 | Access denied when agent lacks tenant/site permission |
| NR-4 | Answer cites lake object keys / catalog ids (auditability) |

NR-* are **out of scope** for current MVP sign-off.

---

## 9. What we will / will not say externally

| Say | Do not say |
|-----|------------|
| “We built a self-hosted ingestion lake for industrial & CRM data.” | “NEO is connected to all company data.” |
| “Agents will consume this lake through a governed access layer.” | “The data lake is the agent.” |
| “MVP proves data lands, is tagged, and is auditable.” | “MVP delivers management intelligence.” |

---

## 10. Sign-off

By signing, parties confirm they share the same foundation boundary and NEO sequencing.

| Role | Name | Date | Decision |
|------|------|------|----------|
| Business Analyst | ________ | ________ | ☐ Approve · ☐ Changes · ☐ Reject |
| Project Manager | ________ | ________ | ☐ Approve · ☐ Changes · ☐ Reject |
| Engineering | ________ | ________ | ☐ Acknowledge |
| NEO product owner (if assigned) | ________ | ________ | ☐ Acknowledge |

**Change control:** Moving any NEO / Agent Access item into MVP requires a written change request and re-approval by BA + PM.

---

*End of Foundation Alignment v1.0*
