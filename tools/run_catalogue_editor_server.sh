#!/usr/bin/env bash
# Launch the local catalogue editor server with the project venv activated.
#
# The /api/repair-stl endpoint runs a boolean-union / preserve-shells
# solidify pass after admesh that depends on trimesh + manifold3d + shapely
# installed only inside .venv. Running the server with the system Python
# silently falls back to admesh-only repair and leaves the M chip pending
# (see operations log: "Boolean-union deps unavailable").
#
# Always start the server with this script so the venv is guaranteed.
#
#   bash tools/run_catalogue_editor_server.sh
#
# Stop with Ctrl-C. Pass --host / --port to override defaults.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [[ ! -x ".venv/bin/python3" ]]; then
    echo "[run_catalogue_editor_server] ERROR: .venv missing at $REPO_ROOT/.venv" >&2
    echo "[run_catalogue_editor_server] create it once with:" >&2
    echo "  python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt" >&2
    exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate

PORT=8765
EXPECT_PORT_VALUE=0
for ARG in "$@"; do
    if [[ "$EXPECT_PORT_VALUE" == "1" ]]; then
        PORT="$ARG"
        EXPECT_PORT_VALUE=0
        continue
    fi

    case "$ARG" in
        --port)
            EXPECT_PORT_VALUE=1
            ;;
        --port=*)
            PORT="${ARG#--port=}"
            ;;
    esac
done

if command -v lsof >/dev/null 2>&1 && lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "[run_catalogue_editor_server] ERROR: port $PORT is already in use." >&2
    echo "[run_catalogue_editor_server] Existing listener:" >&2
    lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >&2 || true
    echo "[run_catalogue_editor_server] Stop the old editor server, then rerun this script." >&2
    echo "[run_catalogue_editor_server] Or start a second copy with: bash tools/run_catalogue_editor_server.sh --port 8766" >&2
    exit 1
fi

exec python3 -u tools/catalogue_editor_server.py "$@"
