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
exec python3 -u tools/catalogue_editor_server.py "$@"
