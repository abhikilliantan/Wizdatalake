#!/usr/bin/env bash
# Continuously dispatch OpenHands iterations for LOCAL development.
# Default: no GitHub push/PR. Advances when .openhands/iterations/IN.done exists
# or when a conversation finishes after writing that marker.
set -euo pipefail

PORT="${PORT:-8010}"
NAME="${OPENHANDS_NAME:-openhands-datalakeskm}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STATE_DIR="${OPENHANDS_HOME:-$HOME/.openhands}/automation"
STATE_FILE="${STATE_DIR}/iteration-watchdog.state"
POLL_SECS="${POLL_SECS:-90}"
MAX_ITERS="${MAX_ITERS:-8}"
LOCAL_DEV="${LOCAL_DEV:-1}"
PROFILE_ID="${OPENHANDS_CURSOR_PROFILE_ID:-}"

mkdir -p "$STATE_DIR" "$REPO_ROOT/.openhands/iterations"

api_key() {
  docker exec -u 0 "$NAME" cat /home/openhands/.openhands/agent-canvas/api-key.txt 2>/dev/null
}

refresh_auth() {
  if [[ -f "$HOME/.config/cursor/auth.json" ]]; then
    mkdir -p "${OPENHANDS_HOME:-$HOME/.openhands}/config/cursor"
    cp -f "$HOME/.config/cursor/auth.json" "${OPENHANDS_HOME:-$HOME/.openhands}/config/cursor/auth.json"
    chmod 644 "${OPENHANDS_HOME:-$HOME/.openhands}/config/cursor/auth.json"
  fi
}

resolve_profile() {
  local k="$1"
  if [[ -n "$PROFILE_ID" ]]; then
    echo "$PROFILE_ID"
    return
  fi
  curl -sf -H "X-Session-API-Key: $k" "http://127.0.0.1:${PORT}/api/agent-profiles" \
    | python3 -c 'import sys,json; d=json.load(sys.stdin); print(next(p["id"] for p in d["profiles"] if p["name"]=="cursor"))'
}

prompt_for() {
  LOCAL_DEV="$LOCAL_DEV" "$REPO_ROOT/scripts/dispatch-openhands-iteration.sh" "$1" 2>/dev/null \
    | sed -n '/-------- COPY INTO CANVAS --------/,/-------- END --------/{//!p}'
}

latest_status() {
  local k="$1" cid="${2:-}"
  if [[ -n "$cid" ]]; then
    curl -sf -H "X-Session-API-Key: $k" "http://127.0.0.1:${PORT}/api/conversations/${cid}" \
      | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("execution_status",""))' 2>/dev/null || echo missing
  else
    echo none
  fi
}

iter_done_local() {
  local iter="$1"
  [[ -f "$REPO_ROOT/.openhands/iterations/I${iter}.done" ]]
}

start_conversation() {
  local k="$1" iter="$2" pid="$3"
  local prompt body
  prompt="$(prompt_for "$iter")"
  body=$(
    ITER="$iter" PID="$pid" python3 - "$prompt" <<'PY'
import json, os, sys
prompt = sys.argv[1]
iter_n = int(os.environ["ITER"])
pid = os.environ["PID"]
text = (
    prompt
    + f"\n\nIMPORTANT: Do not push to GitHub or open PRs. Local development only."
    + f"\nWhen done, write .openhands/iterations/I{iter_n}.done then stop."
)
obj = {
  "workspace": {"working_dir": "/projects/DataLakeSkM", "kind": "LocalWorkspace"},
  "agent_profile_id": pid,
  "max_iterations": 500,
  "stuck_detection": True,
  "confirmation_policy": {"kind": "NeverConfirm"},
  "initial_message": {
    "role": "user",
    "run": True,
    "content": [{"type": "text", "text": text}],
  },
}
print(json.dumps(obj))
PY
  )
  curl -sf -H "Content-Type: application/json" -H "X-Session-API-Key: $k" \
    -X POST "http://127.0.0.1:${PORT}/api/conversations" -d "$body"
}

load_state() {
  if [[ -f "$STATE_FILE" ]]; then
    # shellcheck disable=SC1090
    source "$STATE_FILE"
  fi
  CURRENT_ITER="${CURRENT_ITER:-1}"
  CONVERSATION_ID="${CONVERSATION_ID:-}"
  DISPATCH_COUNT="${DISPATCH_COUNT:-0}"
}

save_state() {
  cat >"$STATE_FILE" <<EOF
CURRENT_ITER=${CURRENT_ITER}
CONVERSATION_ID=${CONVERSATION_ID}
DISPATCH_COUNT=${DISPATCH_COUNT}
UPDATED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)
MODE=local_dev
EOF
}

cmd="${1:-run}"

case "$cmd" in
  once|run|daemon)
    refresh_auth
    if ! docker ps --format '{{.Names}}' | grep -qx "$NAME"; then
      echo "OpenHands not running. Start: $REPO_ROOT/scripts/start-openhands.sh"
      exit 1
    fi
    KEY="$(api_key)"
    [[ -n "$KEY" ]] || { echo "No API key"; exit 1; }
    PID="$(resolve_profile "$KEY")"
    load_state

    LOOPS=9999
    [[ "$cmd" == "once" ]] && LOOPS=1

    echo "Watchdog LOCAL_DEV=${LOCAL_DEV}: I${CURRENT_ITER}…I${MAX_ITERS}"
    echo "Canvas: http://localhost:${PORT}/canvas"

    for ((loop=0; loop<LOOPS; loop++)); do
      if (( CURRENT_ITER > MAX_ITERS )); then
        echo "All iterations through I${MAX_ITERS} done locally."
        exit 0
      fi

      if iter_done_local "$CURRENT_ITER"; then
        echo "I${CURRENT_ITER}: local done marker found — advancing"
        CURRENT_ITER=$((CURRENT_ITER + 1))
        CONVERSATION_ID=""
        DISPATCH_COUNT=0
        save_state
        continue
      fi

      STATUS="$(latest_status "$KEY" "$CONVERSATION_ID")"
      echo "$(date -u +%H:%M:%SZ) I${CURRENT_ITER} cid=${CONVERSATION_ID:-none} status=${STATUS} dispatches=${DISPATCH_COUNT}"

      # If finished and marker missing, do not infinite-loop the same prompt forever
      if [[ "$STATUS" == "finished" || "$STATUS" == "idle" ]]; then
        if iter_done_local "$CURRENT_ITER"; then
          continue
        fi
        if (( DISPATCH_COUNT >= 2 )); then
          echo "I${CURRENT_ITER}: finished twice without marker — leaving for manual/Canvas; sleeping"
          sleep "$POLL_SECS"
          continue
        fi
      fi

      if [[ -z "$CONVERSATION_ID" || "$STATUS" == "error" || "$STATUS" == "missing" || "$STATUS" == "none" || "$STATUS" == "finished" || "$STATUS" == "idle" ]]; then
        if [[ "$STATUS" == "error" ]]; then
          refresh_auth
        fi
        echo "Starting OpenHands conversation for I${CURRENT_ITER} (local, no GitHub)"
        RESP="$(start_conversation "$KEY" "$CURRENT_ITER" "$PID")"
        CONVERSATION_ID="$(echo "$RESP" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("id",""))')"
        DISPATCH_COUNT=$((DISPATCH_COUNT + 1))
        echo "Started $CONVERSATION_ID"
        save_state
      fi

      [[ "$cmd" == "once" ]] && exit 0
      sleep "$POLL_SECS"
    done
    ;;
  status)
    load_state
    echo "CURRENT_ITER=$CURRENT_ITER CONVERSATION_ID=$CONVERSATION_ID MODE=local_dev"
    for i in $(seq 1 "$MAX_ITERS"); do
      if iter_done_local "$i"; then echo "I$i DONE"; else echo "I$i pending"; fi
    done
    ;;
  *)
    echo "Usage: LOCAL_DEV=1 $0 [run|once|daemon|status]"
    exit 1
    ;;
esac
