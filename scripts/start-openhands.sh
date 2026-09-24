#!/usr/bin/env bash
# Start OpenHands Agent Canvas wired to Cursor ACP (agent acp)
set -euo pipefail

PROJECTS_PATH="${PROJECTS_PATH:-$HOME/projects}"
OPENHANDS_HOME="${OPENHANDS_HOME:-$HOME/.openhands}"
IMAGE="${OPENHANDS_IMAGE:-ghcr.io/openhands/agent-canvas:1.23.0}"
NAME="${OPENHANDS_NAME:-openhands-datalakeskm}"
PORT="${PORT:-8000}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AGENT_BIN="${CURSOR_AGENT_BIN:-$HOME/.local/bin/agent}"

mkdir -p "$OPENHANDS_HOME"/{agent-canvas,storage,workspaces,automation,cursor-auth,config} "$PROJECTS_PATH"
chmod -R a+rwX "$OPENHANDS_HOME" 2>/dev/null || true
# Prefer a real bind-mount of the repo (symlinks under /projects break inside Docker)

if [[ ! -x "$AGENT_BIN" ]]; then
  echo "Cursor agent CLI not found at $AGENT_BIN"
  echo "Install Cursor CLI / run: curl https://cursor.com/install -fsS | bash"
  exit 1
fi

# Copy Cursor login so container uid 10001 can read it (host file is mode 600)
mkdir -p "$OPENHANDS_HOME/config/cursor"
if [[ -f "$HOME/.config/cursor/auth.json" ]]; then
  cp -f "$HOME/.config/cursor/auth.json" "$OPENHANDS_HOME/config/cursor/auth.json"
  chmod 644 "$OPENHANDS_HOME/config/cursor/auth.json"
fi
chmod -R a+rwX "$OPENHANDS_HOME/config"

if docker ps -a --format '{{.Names}}' | grep -qx "$NAME"; then
  echo "Stopping existing container $NAME…"
  docker rm -f "$NAME" >/dev/null
fi

echo "Projects: $REPO_ROOT → /projects/DataLakeSkM"
echo "Agent:    Cursor ACP via $AGENT_BIN"
echo "UI:       http://localhost:${PORT}/canvas"
echo ""

# Container runs as uid 10001 — ensure it can edit the project
if command -v setfacl >/dev/null; then
  setfacl -R -m u:10001:rwx -m d:u:10001:rwx "$REPO_ROOT" 2>/dev/null || true
fi
find "$REPO_ROOT" \( -path "$REPO_ROOT/.venv" -o -path "$REPO_ROOT/.pytest_cache" \) -prune -o -type d -exec chmod a+rwx {} + 2>/dev/null || true
find "$REPO_ROOT" \( -path "$REPO_ROOT/.venv" -o -path "$REPO_ROOT/.pytest_cache" \) -prune -o -type f -exec chmod a+rw {} + 2>/dev/null || true

docker run -d --name "$NAME" --privileged \
  -p "${PORT}:8000" \
  -e AGENT_CANVAS_DISABLE_TELEMETRY=1 \
  -e HOME=/home/openhands \
  -e PATH="/home/juliunz/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
  -v "${OPENHANDS_HOME}:/home/openhands/.openhands" \
  -v "${OPENHANDS_HOME}/config:/home/openhands/.config" \
  -v "${REPO_ROOT}:/projects/DataLakeSkM" \
  -v "${HOME}/.local/bin:/home/juliunz/.local/bin:ro" \
  -v "${HOME}/.local/share/cursor-agent:/home/juliunz/.local/share/cursor-agent:ro" \
  "$IMAGE"

echo "Started. Configuring agent profile → Cursor ACP…"
for _ in $(seq 1 45); do
  if curl -sf -o /dev/null "http://127.0.0.1:${PORT}/canvas"; then break; fi
  sleep 2
done

API_KEY=""
for _ in $(seq 1 30); do
  API_KEY="$(docker exec -u 0 "$NAME" cat /home/openhands/.openhands/agent-canvas/api-key.txt 2>/dev/null || true)"
  [[ -n "${API_KEY:-}" ]] && break
  sleep 2
done

if [[ -z "${API_KEY:-}" ]]; then
  echo "API key not ready. In UI: Settings → Agent → ACP → Custom → /home/juliunz/.local/bin/agent acp"
  exit 0
fi

auth=(-H "Content-Type: application/json" -H "X-Session-API-Key: ${API_KEY}")
curl -sf "${auth[@]}" -X PATCH "http://127.0.0.1:${PORT}/api/settings" \
  -d '{"agent_settings_diff":{"agent_kind":"acp","acp_server":"custom","acp_command":["/home/juliunz/.local/bin/agent","acp"]}}' >/dev/null

curl -sf "${auth[@]}" -X POST "http://127.0.0.1:${PORT}/api/agent-profiles/cursor" \
  -d '{"agent_kind":"acp","acp_server":"custom","acp_command":"/home/juliunz/.local/bin/agent acp"}' >/dev/null || true

PID="$(curl -sf -H "X-Session-API-Key: ${API_KEY}" "http://127.0.0.1:${PORT}/api/agent-profiles" \
  | python3 -c 'import sys,json; d=json.load(sys.stdin); print(next((p["id"] for p in d["profiles"] if p["name"]=="cursor"),""))')"
if [[ -n "$PID" ]]; then
  curl -sf -X POST -H "X-Session-API-Key: ${API_KEY}" \
    "http://127.0.0.1:${PORT}/api/agent-profiles/${PID}/activate" >/dev/null || true
  curl -sf "${auth[@]}" -X PATCH "http://127.0.0.1:${PORT}/api/settings" \
    -d "{\"active_agent_profile_id\":\"${PID}\"}" >/dev/null || true
fi

echo "Cursor login inside sandbox:"
docker exec -u openhands -e HOME=/home/openhands -e PATH="/home/juliunz/.local/bin:$PATH" "$NAME" \
  /home/juliunz/.local/bin/agent status 2>&1 | head -10 || true

echo ""
echo "Open http://localhost:${PORT}/canvas"
echo "Workspace: /projects/DataLakeSkM"
echo "Agent profile: cursor (ACP → your Cursor subscription)"
echo "Stop: docker rm -f $NAME"
