#!/usr/bin/env bash
# Seed GitHub labels, milestones, and issues for DataLakeSkM (planning foundation).
set -euo pipefail
REPO="${1:-JuliusMutugu/DataLakeSkM}"

echo "Seeding $REPO …"

# --- Labels ---
create_label() {
  local name="$1" color="$2" desc="$3"
  gh label create "$name" --repo "$REPO" --color "$color" --description "$desc" 2>/dev/null \
    || gh label edit "$name" --repo "$REPO" --color "$color" --description "$desc" 2>/dev/null \
    || true
}

create_label "epic" "6F42C1" "Cross-cutting epic"
create_label "foundation" "0E8A16" "Week 1 foundation & planning"
create_label "week-1" "0E8A16" "Week 1 — Foundation & hub"
create_label "week-2" "1D76DB" "Week 2 — Event-driven + CRM + files"
create_label "week-3" "FBCA04" "Week 3 — Streaming + DB"
create_label "week-4" "D93F0B" "Week 4 — Hardening + UAT prep"
create_label "uat" "B60205" "UAT / sign-off"
create_label "acceptance" "5319E7" "BA acceptance criterion"
create_label "phase-2" "C5DEF5" "Deferred to Phase 2"
create_label "ba-pm" "E99695" "Needs BA / PM action"
create_label "day" "BFDADC" "Day-scoped engineering task"

# --- Milestones ---
ensure_milestone() {
  local title="$1" desc="$2"
  if gh api "repos/$REPO/milestones" --jq '.[].title' 2>/dev/null | grep -Fxq "$title"; then
    echo "Milestone exists: $title"
  else
    gh api "repos/$REPO/milestones" -f title="$title" -f description="$desc" -f state=open >/dev/null
    echo "Created milestone: $title"
  fi
}

ensure_milestone "M1 — Week 1 Foundation & Hub" "Hub + catalog can store a synthetic event end-to-end (D1–D5)."
ensure_milestone "M2 — Event-driven + CRM + Files" "Apps + CRM + files ingest via event-driven path (D6–D10)."
ensure_milestone "M3 — Streaming + DB extracts" "Streaming path + DB extracts; CDC Phase 2 decision (D11–D15)."
ensure_milestone "M4 — Hardening & UAT prep" "System ready for formal UAT (D16–D20)."
ensure_milestone "UAT — Sign-off & handover" "Formal UAT, fixes, acceptance, handover (D21–D24)."

ms_number() {
  gh api "repos/$REPO/milestones" --jq ".[] | select(.title==\"$1\") | .number"
}

M1=$(ms_number "M1 — Week 1 Foundation & Hub")
M2=$(ms_number "M2 — Event-driven + CRM + Files")
M3=$(ms_number "M3 — Streaming + DB extracts")
M4=$(ms_number "M4 — Hardening & UAT prep")
MU=$(ms_number "UAT — Sign-off & handover")

issue() {
  local title="$1" body="$2" labels="$3" milestone="$4"
  gh issue create --repo "$REPO" --title "$title" --body "$body" --label "$labels" --milestone "$milestone"
}

echo "Creating foundation / planning issues…"

issue "[Epic] Week 1 — Foundation & Integration Hub" "$(cat <<'EOF'
## Goal
Foundation + hub skeleton so a synthetic event can land in MinIO with a catalog row (**M1**).

## Children
- D1 Kickoff & backlog freeze
- D2 Platform health
- D3 Integration hub design
- D4 Hub implementation (core)
- D5 Catalog wiring

## Exit
Hub + catalog store a synthetic event end-to-end.

## Refs
- `docs/INTEGRATION_DEVELOPMENT_PLAN.md` §8 Week 1
- `docs/architecture.html` Layer C (NOW)
EOF
)" "epic,foundation,week-1" "$M1"

issue "[Planning] BA/PM sign-off — scope + AC-1…AC-9" "$(cat <<'EOF'
## Why
D1 exit requires signed scope. Plan is still **Draft**.

## Ask
- [ ] BA confirms AC-1…AC-9 in plan §4
- [ ] PM locks dates / working model
- [ ] Confirm MVP in/out (§3) — Phase 2 stays deferred

## Artifact
`docs/INTEGRATION_DEVELOPMENT_PLAN.md`

## Blocks
Formal “D1 complete” and Week 1 BA workshop prioritization.
EOF
)" "foundation,ba-pm,week-1" "$M1"

issue "[Planning] Source priority ranking (BA workshop)" "$(cat <<'EOF'
## Why
D3 needs BA ranking of which sources matter first for demos / pipeline stories.

## Candidates
Custom apps · Salesforce · HubSpot · Flat files · PostgreSQL · MySQL

## Output
Ordered priority list + notes attached to this issue (or linked doc).

## When
Schedule with D3 hub design workshop (1h).
EOF
)" "foundation,ba-pm,week-1" "$M1"

issue "[D1] Kickoff & backlog freeze" "$(cat <<'EOF'
## Focus
Kickoff, scope freeze, ticket board, env bootstrap.

## Checklist
- [x] Scope written (`docs/INTEGRATION_DEVELOPMENT_PLAN.md` §3)
- [x] Architecture artifact (`docs/architecture.html`)
- [x] GitHub issues + milestones seeded (this board)
- [ ] `docker compose up` healthy (carry to D2 if needed)
- [ ] BA/PM sign-off (see planning issue)

## Exit criteria
Signed scope checklist.

## Notes
Storage client + partitioning tests landed ahead of D2.
EOF
)" "day,foundation,week-1" "$M1"

issue "[D2] Platform health — MinIO / Redpanda / Postgres" "$(cat <<'EOF'
## Focus
Verify stack health; smoke-test `ObjectStorage.put_json`; draft runbook ports.

## Checklist
- [ ] `docker compose up -d`
- [ ] MinIO healthy (`:9006` / console `:9007`)
- [ ] Redpanda healthy (`:19092`)
- [ ] Postgres healthy (`:5433`) + init schema present
- [ ] Smoke: `ObjectStorage.put_json` → partitioned key under `raw/…`
- [ ] Runbook draft: ports section
- [ ] PM: start risk log

## Exit
All 3 services healthy + successful smoke write.
EOF
)" "day,foundation,week-1" "$M1"

issue "[D3] Integration hub design + connectors/ skeleton" "$(cat <<'EOF'
## Focus
Source model, routing rules, `connectors/` package skeleton.

## Checklist
- [ ] Define `source_type`, `source_id`, tags model
- [ ] Routing: webhook vs stream vs batch
- [ ] Design note for BA approval
- [ ] Package skeleton `connectors/`
- [ ] BA workshop: source priority (linked planning issue)

## Exit
Design note approved by BA.
EOF
)" "day,foundation,week-1" "$M1"

issue "[D4] Hub implementation — SourceRegistry / normalize / route" "$(cat <<'EOF'
## Focus
Core hub: `SourceRegistry`, `normalize()`, `route()`, shared envelope schema.

## Checklist
- [ ] Envelope schema (shared event contract)
- [ ] `SourceRegistry`
- [ ] `normalize()` + `route()`
- [ ] Unit tests for envelope

## Exit
Unit tests for envelope green.
EOF
)" "day,foundation,week-1" "$M1"

issue "[D5] Catalog wiring — ingestion_events on write" "$(cat <<'EOF'
## Focus
Write/read `ingestion_events` from storage path; connector registry table.

## Checklist
- [ ] Catalog write on successful ObjectStorage put
- [ ] Connector registry table usage
- [ ] Demo: synthetic event → MinIO + catalog row
- [ ] PM Week 1 checkpoint

## Exit
Catalog row created on write → **M1 complete**.
EOF
)" "day,foundation,week-1" "$M1"

echo "Creating Week 2–4 + UAT day issues…"

issue "[Epic] Week 2 — Event-driven + CRM + Files" "FastAPI webhooks, Salesforce/HubSpot adapters, file ingest. Milestone M2. See plan §8." "epic,week-2" "$M2"
issue "[D6] FastAPI ingestion service skeleton" "\`ingestion/\` app, health, config, logging. Exit: \`/health\` → 200." "day,week-2" "$M2"
issue "[D7] Generic webhook POST /v1/ingest/{source}" "Webhook → hub → MinIO → catalog. Exit: AC-3 path works. BA: sample payload review." "day,week-2" "$M2"
issue "[D8] Salesforce adapter" "Map fixture → envelope; tags \`source=salesforce\`. Exit: AC-1 demo-ready. BA field mapping review." "day,week-2" "$M2"
issue "[D9] HubSpot adapter" "Map fixture → envelope; tags \`source=hubspot\`. Exit: AC-2 demo-ready. BA field mapping review." "day,week-2" "$M2"
issue "[D10] Flat file ingestion" "Upload API or drop folder; CSV/JSON → lake. Exit: AC-4 demo-ready. PM mid-project status." "day,week-2" "$M2"

issue "[Epic] Week 3 — Streaming + DB extracts" "Redpanda consumer, load test, PG/MySQL extracts, CDC spike → Phase 2. Milestone M3." "epic,week-3" "$M3"
issue "[D11] Redpanda topics + producer helper" "Create \`datalake.ingest\`; produce/consume smoke." "day,week-3" "$M3"
issue "[D12] Streaming consumer batch flush" "Batch flush to MinIO + catalog + checkpoints. Exit: AC-6 path at small scale." "day,week-3" "$M3"
issue "[D13] Stream load test ≥1000 messages" "Script + object count & partitions. Exit: AC-6 evidence. PM capacity note." "day,week-3" "$M3"
issue "[D14] DB batch extract — PostgreSQL" "Read-only connector; table → lake. Exit: AC-5 (Postgres). BA: tables/columns." "day,week-3" "$M3"
issue "[D15] DB batch extract — MySQL + CDC spike" "MySQL parity + CDC design spike → Phase 2 backlog. BA/PM approve Phase 2 CDC scope." "day,week-3" "$M3"

issue "[Epic] Week 4 — Hardening & UAT prep" "Errors, security, observability, regression, UAT pack. Milestone M4." "epic,week-4" "$M4"
issue "[D16] Error handling & retries" "Failed status in catalog; retry policy. Exit: AC-8 evidence." "day,week-4" "$M4"
issue "[D17] Security baseline" "Secrets, webhook shared-secret, private bucket. PM security checklist." "day,week-4" "$M4"
issue "[D18] Observability" "Correlation IDs; metrics/log notes. Trace one event source→lake→catalog." "day,week-4" "$M4"
issue "[D19] End-to-end regression suite" "Fixture-based tests for all MVP sources. CI/local green." "day,week-4" "$M4"
issue "[D20] UAT pack & dry run" "Scenarios mapped to AC-1…AC-9; dry run with BA." "day,week-4,ba-pm" "$M4"

issue "[D21] Formal UAT — execute AC-1…AC-9" "BA lead; Eng support. Log defects." "day,uat" "$MU"
issue "[D22] Defect fix window (P0/P1)" "Fixes + retest only." "day,uat" "$MU"
issue "[D23] Final demo & BA acceptance" "Full walkthrough; BA acceptance decision." "day,uat,ba-pm" "$MU"
issue "[D24] Handover & PM go/no-go" "Runbooks, env vars, known issues, Phase 2 backlog." "day,uat,ba-pm" "$MU"

echo "Creating acceptance criteria issues…"

issue "[AC-1] Salesforce webhook → lake path" "Ingest Salesforce-like payload under \`raw/source=salesforce/…\` with tags. Evidence: demo + object key." "acceptance" "$M2"
issue "[AC-2] HubSpot webhook → lake path" "Ingest HubSpot-like payload under \`raw/source=hubspot/…\` with tags." "acceptance" "$M2"
issue "[AC-3] Custom app webhook → lake" "POST webhook API → appears in MinIO. Evidence: curl/Postman." "acceptance" "$M2"
issue "[AC-4] Flat file → lake partitions" "CSV/JSON lands with correct partition path." "acceptance" "$M2"
issue "[AC-5] Database extract → lake" "Sample PG or MySQL table extract in lake." "acceptance" "$M3"
issue "[AC-6] ≥1000 stream messages flushed" "Redpanda → batch flush MinIO; count verified." "acceptance" "$M3"
issue "[AC-7] Catalog row per successful write" "Every successful write has \`ingestion_events\` row." "acceptance" "$M1"
issue "[AC-8] Failed ingestions logged" "Failures do not silently drop data." "acceptance" "$M4"
issue "[AC-9] Architecture + runbook BA/PM review" "Architecture and runbook reviewed/understood." "acceptance,ba-pm" "$MU"

issue "[Phase 2] Full CDC production (deferred)" "Debezium / WAL / binlog production rollout — explicitly out of MVP. Decision memo due D15." "phase-2" "$M3"

echo "Done seeding $REPO"
gh issue list --repo "$REPO" --limit 50
