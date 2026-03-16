#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$ROOT_DIR/procurement_backend.pid"
LOG_FILE="$ROOT_DIR/procurement.log"
PORT=8000

cd "$ROOT_DIR"

if [ ! -d .venv ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install -r requirements.txt >/tmp/procurement_backend_pip.log 2>&1

if [ -f "$PID_FILE" ]; then
    PID="$(cat "$PID_FILE")"
    if kill -0 "$PID" 2>/dev/null; then
        echo "Procurement backend already running (PID $PID)."
        exit 0
    fi
    rm -f "$PID_FILE"
fi

if ss -ltn "( sport = :$PORT )" | tail -n +2 | grep -q .; then
    EXISTING_PID="$(ss -ltnp | awk -v port=":$PORT" '$4 ~ port {print $NF}' | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' | head -n 1)"
    if [ -n "$EXISTING_PID" ] && kill -0 "$EXISTING_PID" 2>/dev/null; then
        echo "$EXISTING_PID" >"$PID_FILE"
        echo "Procurement backend already running on port $PORT (PID $EXISTING_PID)."
        exit 0
    fi
    echo "Port $PORT is already in use. Stop the existing process first."
    exit 1
fi

nohup .venv/bin/uvicorn app:app --host 0.0.0.0 --port "$PORT" >"$LOG_FILE" 2>&1 &
echo $! >"$PID_FILE"

for _ in $(seq 1 20); do
    if curl -sS --max-time 2 "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then
        echo "Procurement backend started successfully."
        echo "PID: $(cat "$PID_FILE")"
        echo "Health: http://127.0.0.1:$PORT/health"
        exit 0
    fi
    sleep 1
done

echo "Backend failed to become healthy. Check $LOG_FILE"
exit 1
