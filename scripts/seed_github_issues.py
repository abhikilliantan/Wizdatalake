#!/usr/bin/env python3
"""Seed DataLakeSkM GitHub issues via gh api (reliable milestone titles)."""
from __future__ import annotations

import json
import subprocess
import sys

REPO = sys.argv[1] if len(sys.argv) > 1 else "JuliusMutugu/DataLakeSkM"


def run(args: list[str], input_text: str | None = None) -> str:
    r = subprocess.run(
        args,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )
    if r.returncode != 0:
        raise RuntimeError(f"$ {' '.join(args)}\n{r.stderr or r.stdout}")
    return r.stdout.strip()


def ensure_label(name: str, color: str, desc: str) -> None:
    subprocess.run(
        ["gh", "label", "create", name, "--repo", REPO, "--color", color, "--description", desc],
        capture_output=True,
        text=True,
    )


def milestones() -> dict[str, int]:
    raw = run(["gh", "api", f"repos/{REPO}/milestones", "--paginate"])
    return {m["title"]: m["number"] for m in json.loads(raw)}


def ensure_milestones() -> dict[str, int]:
    wanted = {
        "M1 — Week 1 Foundation & Hub": "Hub + catalog synthetic event E2E (D1–D5).",
        "M2 — Event-driven + CRM + Files": "Apps + CRM + files via event-driven path (D6–D10).",
        "M3 — Streaming + DB extracts": "Streaming + DB extracts; CDC Phase 2 decision (D11–D15).",
        "M4 — Hardening & UAT prep": "Ready for formal UAT (D16–D20).",
        "UAT — Sign-off & handover": "Formal UAT, fixes, acceptance, handover (D21–D24).",
    }
    existing = milestones()
    for title, desc in wanted.items():
        if title not in existing:
            run(
                [
                    "gh",
                    "api",
                    f"repos/{REPO}/milestones",
                    "-f",
                    f"title={title}",
                    "-f",
                    f"description={desc}",
                    "-f",
                    "state=open",
                ]
            )
    return milestones()


def create_issue(title: str, body: str, labels: list[str], milestone: int) -> None:
    # skip if open issue with same title exists
    open_titles = run(
        [
            "gh",
            "issue",
            "list",
            "--repo",
            REPO,
            "--state",
            "open",
            "--limit",
            "200",
            "--json",
            "title",
            "--jq",
            ".[].title",
        ]
    ).splitlines()
    if title in open_titles:
        print(f"skip exists: {title}")
        return
    payload = {
        "title": title,
        "body": body,
        "labels": labels,
        "milestone": milestone,
    }
    out = run(
        ["gh", "api", f"repos/{REPO}/issues", "--input", "-"],
        input_text=json.dumps(payload),
    )
    num = json.loads(out)["number"]
    print(f"#{num} {title}")


def main() -> None:
    for name, color, desc in [
        ("epic", "6F42C1", "Cross-cutting epic"),
        ("foundation", "0E8A16", "Week 1 foundation & planning"),
        ("week-1", "0E8A16", "Week 1 — Foundation & hub"),
        ("week-2", "1D76DB", "Week 2 — Event-driven + CRM + files"),
        ("week-3", "FBCA04", "Week 3 — Streaming + DB"),
        ("week-4", "D93F0B", "Week 4 — Hardening + UAT prep"),
        ("uat", "B60205", "UAT / sign-off"),
        ("acceptance", "5319E7", "BA acceptance criterion"),
        ("phase-2", "C5DEF5", "Deferred to Phase 2"),
        ("ba-pm", "E99695", "Needs BA / PM action"),
        ("day", "BFDADC", "Day-scoped engineering task"),
    ]:
        ensure_label(name, color, desc)

    ms = ensure_milestones()
    m1, m2, m3, m4, mu = (
        ms["M1 — Week 1 Foundation & Hub"],
        ms["M2 — Event-driven + CRM + Files"],
        ms["M3 — Streaming + DB extracts"],
        ms["M4 — Hardening & UAT prep"],
        ms["UAT — Sign-off & handover"],
    )

    issues = [
        (
            "[Epic] Week 1 — Foundation & Integration Hub",
            """## Goal
Foundation + hub skeleton so a synthetic event can land in MinIO with a catalog row (**M1**).

## Children
D1–D5 (kickoff → catalog wiring)

## Exit
Hub + catalog store a synthetic event end-to-end.

## Refs
- `docs/INTEGRATION_DEVELOPMENT_PLAN.md` §8 Week 1
- `docs/architecture.html` Layer C (NOW)
""",
            ["epic", "foundation", "week-1"],
            m1,
        ),
        (
            "[Planning] BA/PM sign-off — scope + AC-1…AC-9",
            """## Why
D1 exit requires signed scope. Plan is still **Draft**.

## Ask
- [ ] BA confirms AC-1…AC-9 in plan §4
- [ ] PM locks dates / working model
- [ ] Confirm MVP in/out (§3) — Phase 2 stays deferred

## Artifact
`docs/INTEGRATION_DEVELOPMENT_PLAN.md`
""",
            ["foundation", "ba-pm", "week-1"],
            m1,
        ),
        (
            "[Planning] Source priority ranking (BA workshop)",
            """## Why
D3 needs BA ranking of which sources matter first for demos / pipeline.

## Candidates
Custom apps · Salesforce · HubSpot · Flat files · PostgreSQL · MySQL

## Output
Ordered priority list on this issue.

## When
With D3 hub design workshop (1h).
""",
            ["foundation", "ba-pm", "week-1"],
            m1,
        ),
        (
            "[D1] Kickoff & backlog freeze",
            """## Focus
Kickoff, scope freeze, ticket board, env bootstrap.

## Checklist
- [x] Scope written (`docs/INTEGRATION_DEVELOPMENT_PLAN.md` §3)
- [x] Architecture artifact (`docs/architecture.html`)
- [x] GitHub issues + milestones seeded
- [ ] `docker compose up` healthy (see D2)
- [ ] BA/PM sign-off (planning issue)

## Exit
Signed scope checklist.

## Notes
Storage client + partitioning tests landed ahead of schedule.
""",
            ["day", "foundation", "week-1"],
            m1,
        ),
        (
            "[D2] Platform health — MinIO / Redpanda / Postgres",
            """## Focus
Verify stack health; smoke-test `ObjectStorage.put_json`; draft runbook ports.

## Checklist
- [ ] `docker compose up -d`
- [ ] MinIO healthy (`:9006` / console `:9007`)
- [ ] Redpanda healthy (`:19092`)
- [ ] Postgres healthy (`:5433`) + init schema
- [ ] Smoke: `ObjectStorage.put_json` → `raw/…`
- [ ] Runbook draft: ports
- [ ] PM: start risk log

## Exit
All 3 services healthy + successful smoke write.
""",
            ["day", "foundation", "week-1"],
            m1,
        ),
        (
            "[D3] Integration hub design + connectors/ skeleton",
            """## Focus
Source model, routing rules, `connectors/` package skeleton.

## Checklist
- [ ] `source_type`, `source_id`, tags model
- [ ] Routing: webhook vs stream vs batch
- [ ] Design note for BA approval
- [ ] Package skeleton `connectors/`
- [ ] BA workshop: source priority

## Exit
Design note approved by BA.
""",
            ["day", "foundation", "week-1"],
            m1,
        ),
        (
            "[D4] Hub implementation — SourceRegistry / normalize / route",
            """## Focus
`SourceRegistry`, `normalize()`, `route()`, shared envelope schema.

## Checklist
- [ ] Envelope schema
- [ ] `SourceRegistry`
- [ ] `normalize()` + `route()`
- [ ] Unit tests for envelope

## Exit
Envelope unit tests green.
""",
            ["day", "foundation", "week-1"],
            m1,
        ),
        (
            "[D5] Catalog wiring — ingestion_events on write",
            """## Focus
Write/read `ingestion_events` from storage path; connector registry.

## Checklist
- [ ] Catalog write on successful ObjectStorage put
- [ ] Connector registry usage
- [ ] Demo: synthetic event → MinIO + catalog row
- [ ] PM Week 1 checkpoint

## Exit
Catalog row on write → **M1 complete**.
""",
            ["day", "foundation", "week-1"],
            m1,
        ),
        (
            "[Epic] Week 2 — Event-driven + CRM + Files",
            "FastAPI webhooks, Salesforce/HubSpot adapters, file ingest. Milestone **M2**. Plan §8.",
            ["epic", "week-2"],
            m2,
        ),
        (
            "[D6] FastAPI ingestion service skeleton",
            "`ingestion/` app, health, config, logging. Exit: `/health` → 200.",
            ["day", "week-2"],
            m2,
        ),
        (
            "[D7] Generic webhook POST /v1/ingest/{source}",
            "Webhook → hub → MinIO → catalog. Exit: **AC-3**. BA: sample payload review.",
            ["day", "week-2"],
            m2,
        ),
        (
            "[D8] Salesforce adapter",
            "Map fixture → envelope; `source=salesforce`. Exit: **AC-1** demo-ready.",
            ["day", "week-2"],
            m2,
        ),
        (
            "[D9] HubSpot adapter",
            "Map fixture → envelope; `source=hubspot`. Exit: **AC-2** demo-ready.",
            ["day", "week-2"],
            m2,
        ),
        (
            "[D10] Flat file ingestion",
            "Upload API or drop folder; CSV/JSON → lake. Exit: **AC-4**. PM mid-project status.",
            ["day", "week-2"],
            m2,
        ),
        (
            "[Epic] Week 3 — Streaming + DB extracts",
            "Redpanda consumer, load test, PG/MySQL extracts, CDC spike → Phase 2. **M3**.",
            ["epic", "week-3"],
            m3,
        ),
        (
            "[D11] Redpanda topics + producer helper",
            "Create `datalake.ingest`; produce/consume smoke.",
            ["day", "week-3"],
            m3,
        ),
        (
            "[D12] Streaming consumer batch flush",
            "Batch flush to MinIO + catalog + checkpoints. Exit: **AC-6** at small scale.",
            ["day", "week-3"],
            m3,
        ),
        (
            "[D13] Stream load test ≥1000 messages",
            "Script + object count & partitions. Exit: **AC-6** evidence.",
            ["day", "week-3"],
            m3,
        ),
        (
            "[D14] DB batch extract — PostgreSQL",
            "Read-only connector; table → lake. Exit: **AC-5** (Postgres).",
            ["day", "week-3"],
            m3,
        ),
        (
            "[D15] DB batch extract — MySQL + CDC spike",
            "MySQL parity + CDC design spike → Phase 2. BA/PM approve Phase 2 CDC scope.",
            ["day", "week-3"],
            m3,
        ),
        (
            "[Epic] Week 4 — Hardening & UAT prep",
            "Errors, security, observability, regression, UAT pack. **M4**.",
            ["epic", "week-4"],
            m4,
        ),
        (
            "[D16] Error handling & retries",
            "Failed status in catalog; retry policy. Exit: **AC-8** evidence.",
            ["day", "week-4"],
            m4,
        ),
        (
            "[D17] Security baseline",
            "Secrets, webhook shared-secret, private bucket. PM security checklist.",
            ["day", "week-4"],
            m4,
        ),
        (
            "[D18] Observability",
            "Correlation IDs; metrics/log notes. Trace one event source→lake→catalog.",
            ["day", "week-4"],
            m4,
        ),
        (
            "[D19] End-to-end regression suite",
            "Fixture-based tests for all MVP sources. CI/local green.",
            ["day", "week-4"],
            m4,
        ),
        (
            "[D20] UAT pack & dry run",
            "Scenarios mapped to AC-1…AC-9; dry run with BA.",
            ["day", "week-4", "ba-pm"],
            m4,
        ),
        (
            "[D21] Formal UAT — execute AC-1…AC-9",
            "BA lead; Eng support. Log defects.",
            ["day", "uat"],
            mu,
        ),
        (
            "[D22] Defect fix window (P0/P1)",
            "Fixes + retest only.",
            ["day", "uat"],
            mu,
        ),
        (
            "[D23] Final demo & BA acceptance",
            "Full walkthrough; BA acceptance decision.",
            ["day", "uat", "ba-pm"],
            mu,
        ),
        (
            "[D24] Handover & PM go/no-go",
            "Runbooks, env vars, known issues, Phase 2 backlog.",
            ["day", "uat", "ba-pm"],
            mu,
        ),
        (
            "[AC-1] Salesforce webhook → lake path",
            "Salesforce-like payload under `raw/source=salesforce/…` with tags.",
            ["acceptance"],
            m2,
        ),
        (
            "[AC-2] HubSpot webhook → lake path",
            "HubSpot-like payload under `raw/source=hubspot/…` with tags.",
            ["acceptance"],
            m2,
        ),
        (
            "[AC-3] Custom app webhook → lake",
            "POST webhook API → MinIO. Evidence: curl/Postman.",
            ["acceptance"],
            m2,
        ),
        (
            "[AC-4] Flat file → lake partitions",
            "CSV/JSON with correct partition path.",
            ["acceptance"],
            m2,
        ),
        (
            "[AC-5] Database extract → lake",
            "Sample PG or MySQL table extract in lake.",
            ["acceptance"],
            m3,
        ),
        (
            "[AC-6] ≥1000 stream messages flushed",
            "Redpanda → batch flush MinIO; count verified.",
            ["acceptance"],
            m3,
        ),
        (
            "[AC-7] Catalog row per successful write",
            "Every successful write has `ingestion_events` row.",
            ["acceptance"],
            m1,
        ),
        (
            "[AC-8] Failed ingestions logged",
            "Failures do not silently drop data.",
            ["acceptance"],
            m4,
        ),
        (
            "[AC-9] Architecture + runbook BA/PM review",
            "Architecture and runbook reviewed/understood.",
            ["acceptance", "ba-pm"],
            mu,
        ),
        (
            "[Phase 2] Full CDC production (deferred)",
            "Debezium / WAL / binlog production — out of MVP. Decision memo due D15.",
            ["phase-2"],
            m3,
        ),
    ]

    for title, body, labels, milestone in issues:
        create_issue(title, body, labels, milestone)

    print("done")


if __name__ == "__main__":
    main()
