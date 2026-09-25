# OpenHands Delivery Team — Workflow

**Purpose:** Run OpenHands as the software development team that implements DataLakeSkM until MVP completion.

| Role | Who | GitHub |
|------|-----|--------|
| **Dev team (agents)** | OpenHands + Cursor ACP | Commit & PR → **Julius** `origin` |
| **Tech lead / you** | Review, merge on Julius, promote when ready | Push reviewed work → **Abhishek** `wizdatalake` |
| **Product / BA / PM** | Issues, acceptance, demos | Comments on Julius issues |

---

## Golden rule (do not break)

```text
OpenHands  →  commits/PRs  →  github.com/JuliusMutugu/DataLakeSkM   (origin)
You        →  review       →  then push/promote  →  github.com/abhikilliantan/Wizdatalake  (wizdatalake)
```

Agents **must never** push to `wizdatalake` / Abhishek’s repo.  
That remote is for **your** promotion after review.

---

## Remotes (already configured)

```bash
git remote -v
# origin      → https://github.com/JuliusMutugu/DataLakeSkM.git
# wizdatalake → https://github.com/abhikilliantan/Wizdatalake.git
```

---

## How the team works day to day

1. **Work is an Issue** on Julius’s repo (`[D#] …` or `[AC-#] …`).
2. **You allocate** the issue to OpenHands (prompt in Agent Canvas).
3. OpenHands implements **only that issue**, commits on a feature branch, opens a **PR into Julius** (`origin`).
4. **You review** the PR on Julius (code + demo evidence).
5. Merge on Julius when happy.
6. When you want Abhishek’s copy updated: **you** promote (cherry-pick / merge / push to `wizdatalake`). Agents do not do this.

### Prompt template for OpenHands

```text
Workspace: /projects/DataLakeSkM
Agent profile: cursor

Work Julius GitHub issue #<N> ([D#] title).
Read AGENTS.md and docs/FOUNDATION_ALIGNMENT.md.
Implement ONLY that issue’s checklist.
Commit on a feature branch. Push and open a PR against origin (JuliusMutugu/DataLakeSkM).
NEVER push to remote "wizdatalake" (Abhishek). Never expand NEO / Phase-2 scope.
```

---

## Start / stop the team (OpenHands)

Ingestion API already uses **:8000**. OpenHands UI uses **:8010**.

```bash
./scripts/start-openhands.sh          # http://localhost:8010/canvas
docker rm -f openhands-datalakeskm    # stop team UI
```

| Setting | Value |
|---------|--------|
| UI | http://localhost:8010/canvas |
| Workspace | `/projects/DataLakeSkM` |
| Agent profile | `cursor` (Cursor ACP) |
| Commit remote | `origin` = Julius |

Keep the data stack up separately:

```bash
docker compose --env-file .env up -d
# ingestion API (demo): PYTHONPATH=. .venv/bin/python -m ingestion.main  → :8000
```

---

## Branch naming (agents)

| Pattern | Example |
|---------|---------|
| Day work | `feature/d12-streaming-consumer` |
| Acceptance | `feature/ac7-catalog-row` |
| Fix | `fix/ingest-auth-header` |

Base from latest `main` (or the active delivery branch you specify in the issue).

---

## Definition of Done (agent PR)

- [ ] Issue checklist complete  
- [ ] Tests added/updated where relevant  
- [ ] No `.env` / secrets committed  
- [ ] PR targets **Julius** `origin`  
- [ ] PR description links `#issue` + how to demo  
- [ ] Did **not** push `wizdatalake`

---

## Your promote-to-Abhishek checklist (human only)

```bash
# After review/merge on Julius:
git fetch origin
git checkout main
git pull origin main

# Option A — push main to Abhishek when ready
git push wizdatalake main

# Option B — push a reviewed feature branch for Abhishek to see
git push wizdatalake feature/your-reviewed-branch
```

Never ask OpenHands to run the promote step.

---

## Scope boundary (team charter)

**In:** foundation — hub, webhooks, streaming, files, DB extract, catalog, ops health.  
**Out until you say otherwise:** NEO runtime, agent RAG, multi-tenant authZ, full CDC prod, warehouses.

Source of truth: `docs/FOUNDATION_ALIGNMENT.md` · day plan: `docs/INTEGRATION_DEVELOPMENT_PLAN.md`.

---

## If OpenHands can’t push to Julius

- Confirm `gh auth status` / git credentials on the host.  
- Confirm `origin` URL is JuliusMutugu/DataLakeSkM.  
- Prefer HTTPS + `gh` or a PAT with `repo` scope for Julius only — **not** Abhishek write access for agents.
