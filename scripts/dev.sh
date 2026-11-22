#!/usr/bin/env bash
# Default startup: the research lab on :3100 is the only user-facing dashboard. The two backends run
# API-only (their / redirects to the lab). The legacy pages stay in the source for rollback:
#   make legacy-demo                      the old QEC-Aegis page on :8765
#   (cd $MIDQWEST_DIR && .venv/bin/python dashboard/serve.py)   the old MidQwest page on :8000
#
#   ./scripts/dev.sh          start whatever is not already listening, then print the URLs
#   ./scripts/dev.sh stop     stop what this script started
#   ./scripts/dev.sh status   which ports answer
set -uo pipefail
cd "$(dirname "$0")/.."
ROOT=$(pwd)
MIDQWEST_DIR=${MIDQWEST_DIR:-$HOME/MidQwest}
PIDS=$ROOT/logs/dev.pids
mkdir -p logs

listening() { lsof -tiTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1; }

start() {  # start NAME PORT DIR COMMAND...
  local name=$1 port=$2 dir=$3; shift 3
  if listening "$port"; then echo "  $name: already listening on :$port"; return; fi
  # Fully detached: no inherited stdin/stdout, so a caller piping our output is not held open.
  (cd "$dir" && nohup "$@" < /dev/null > "$ROOT/logs/dev-$name.log" 2>&1 & echo "$name $!" >> "$PIDS") > /dev/null 2>&1
  for _ in $(seq 1 60); do listening "$port" && break; sleep 1; done
  listening "$port" && echo "  $name: started on :$port (log logs/dev-$name.log)" || echo "  $name: FAILED to start, see logs/dev-$name.log"
}

case "${1:-start}" in
  start)
    echo "Starting the QEC research lab (local only; no IBM Quantum access)"
    start aegis-api 8765 "$ROOT" env OMP_NUM_THREADS=1 .venv/bin/python dashboard/server.py --port 8765 --no-browser --api-only
    if [ -x "$MIDQWEST_DIR/.venv/bin/python" ]; then
      start sim-api 8000 "$MIDQWEST_DIR" .venv/bin/python dashboard/serve.py --port 8000 --no-browser --api-only
    else
      echo "  sim-api: $MIDQWEST_DIR/.venv not found; set MIDQWEST_DIR to the MidQwest checkout"
    fi
    if [ ! -d lab/node_modules ]; then (cd lab && npm ci); fi
    if [ ! -f lab/.next/BUILD_ID ]; then (cd lab && npm run build); fi
    start lab 3100 "$ROOT/lab" npx next start -H 127.0.0.1 -p 3100
    echo
    echo "  Research lab:  http://127.0.0.1:3100/"
    echo "  APIs:          http://127.0.0.1:8765/api/status   http://127.0.0.1:8000/api/docs"
    ;;
  stop)
    [ -f "$PIDS" ] || { echo "nothing started by dev.sh"; exit 0; }
    while read -r name pid; do kill "$pid" 2>/dev/null && echo "  stopped $name ($pid)"; done < "$PIDS"
    rm -f "$PIDS"
    ;;
  status)
    for p in 3100 8765 8000; do listening "$p" && echo "  :$p up" || echo "  :$p down"; done
    ;;
  *) echo "usage: $0 [start|stop|status]" >&2; exit 1 ;;
esac
