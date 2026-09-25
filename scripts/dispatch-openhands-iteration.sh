#!/usr/bin/env bash
# Print OpenHands iteration prompt. LOCAL_DEV=1 (default): no GitHub push/PR.
set -euo pipefail

ITER="${1:-1}"
LOCAL_DEV="${LOCAL_DEV:-1}"
REPO="JuliusMutugu/DataLakeSkM"

declare -A ISSUES TITLES
ISSUES[1]=14; TITLES[1]="[D10] Flat file ingestion"
ISSUES[2]=16; TITLES[2]="[D11] Redpanda topics + producer helper"
ISSUES[3]=17; TITLES[3]="[D12] Streaming consumer batch flush"
ISSUES[4]=18; TITLES[4]="[D13] Stream load test ≥1000 messages"
ISSUES[5]=19; TITLES[5]="[D14] DB batch extract — PostgreSQL"
ISSUES[6]=21; TITLES[6]="[D15] DB batch extract — MySQL + CDC spike"
ISSUES[7]=23; TITLES[7]="[D16] Error handling & retries (start Week-4)"
ISSUES[8]=27; TITLES[8]="[D20] UAT pack & dry run"

if [[ -z "${ISSUES[$ITER]:-}" ]]; then
  echo "Usage: LOCAL_DEV=1 $0 <1-8>"
  exit 1
fi

N="${ISSUES[$ITER]}"
TITLE="${TITLES[$ITER]}"
DONE_MARKER=".openhands/iterations/I${ITER}.done"

if [[ "$LOCAL_DEV" == "1" ]]; then
  GIT_RULES=$(cat <<EOF
LOCAL DEV MODE (no GitHub required):
  - Implement ONLY this issue checklist in the workspace
  - Prefer local commits on the feature branch if useful; DO NOT push; DO NOT open PRs
  - Do NOT run gh auth / gh pr / git push — that blocks development
  - Verify with local tests / curl / docker compose when relevant
  - When the checklist is satisfied locally, write marker file:
      ${DONE_MARKER}
    containing one line: DONE and a short summary, then stop.
EOF
)
else
  GIT_RULES=$(cat <<EOF
Git rules:
  - Push ONLY to origin (https://github.com/JuliusMutugu/DataLakeSkM.git)
  - Open a PR linked to #${N}
  - NEVER push remote wizdatalake (Abhishek)
  - Never commit .env
EOF
)
fi

PROMPT=$(cat <<EOF
You are the DataLakeSkM OpenHands developer (not the orchestrator).

Read: AGENTS.md, docs/OPENHANDS_TEAM.md (if present), docs/ITERATION_SCHEDULE.md (if present)

Iteration: I${ITER} — Julius issue #${N} — ${TITLE}
Implement ONLY that issue checklist.
${GIT_RULES}
Never commit .env.
Workspace: /projects/DataLakeSkM
Agent profile: cursor
When done: summarize what you built and how to demo locally.
EOF
)

echo "======== OPENHANDS ITERATION I${ITER} (LOCAL_DEV=${LOCAL_DEV}) ========"
echo "Issue: https://github.com/${REPO}/issues/${N}"
echo "Canvas: http://localhost:8010/canvas"
echo
echo "-------- COPY INTO CANVAS --------"
echo "$PROMPT"
echo "-------- END --------"
