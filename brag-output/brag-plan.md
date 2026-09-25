# Day 2 brag / demo plan — live foundation + agent serve

**Angle:** Show a **live** Day-2 system: data lands, is audited, and is **served** to an agent-style client — the NEO enforcement base.

**Audience:** Sales · Product · NEO sponsor (non-technical OK)

**Tone:** polished, high-stakes, evidence-first (no animation theater)

**Primary artifacts**
| File | Use |
|------|-----|
| `brag-output/day2-demo.md` | Room script (what to say + run) |
| `scripts/simulate_day2_demo.sh` | One-command live simulation |
| `brag-output/day2-live-evidence/` | Captured health, serve JSON, full-run transcript |
| `brag-output/share-copy.txt` | Slack / email blurb |
| `docs/DATA_PIPELINE_FLOW.md` | Mermaid extract→load→serve |
| `docs/DAY2_DELIVERY_AND_VALUE.md` | Sponsor value pack |

**Live storyboard (~8–10 min)**

| # | Time | Beat |
|---|------|------|
| 1 | 0–1m | Health green — lake + catalog reachable |
| 2 | 1–3m | `demo_ingest.sh` — SF/HS/SAP/app/file → MinIO folders |
| 3 | 3–6m | `demo_serve.sh` — agent discover + fetch payload + presign |
| 4 | 6–7m | Stream smoke `datalake.ingest` |
| 5 | 7–8m | SQL catalog + pytest 19 passed |
| 6 | 8–10m | Close: NEO base approved?; next paid slice |

**Differentiator vs Day 1:** Day 1 = architecture & plan. Day 2 = **running ingest + agent serve**.

**Pass criteria for the room**
- [ ] Someone saw `status: stored` and an object key  
- [ ] Someone saw a **payload** returned from `/v1/serve/events/{id}`  
- [ ] Someone saw catalog SQL or recent JSON update  
- [ ] Tests reported passed  

**Repos**
- Julius / Abhishek: serving layer on `main` (Wizdatalake PR #3+)  
- Local: `feature/d10-file-ingest` with `/v1/serve/*`
