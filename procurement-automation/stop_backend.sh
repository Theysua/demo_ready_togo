#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$ROOT_DIR/procurement_backend.pid"
PORT=8000
STOPPED=0

if [ ! -f "$PID_FILE" ]; then
    EXISTING_PID="$(ss -ltnp | awk -v port=":$PORT" '$4 ~ port {print $NF}' | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' | head -n 1)"
    if [ -n "$EXISTING_PID" ] && kill -0 "$EXISTING_PID" 2>/dev/null; then
        kill "$EXISTING_PID"
        echo "Stopped procurement backend on port $PORT (PID $EXISTING_PID)."
        exit 0
    fi
    echo "No PID file found. Backend may already be stopped."
    exit 0
fi

PID="$(cat "$PID_FILE")"

if kill -0 "$PID" 2>/dev/null; then
    kill "$PID"
    echo "Stopped procurement backend (PID $PID)."
    STOPPED=1
else
    echo "Process $PID is not running."
fi

rm -f "$PID_FILE"

if [ "$STOPPED" -eq 0 ]; then
    EXISTING_PID="$(ss -ltnp | awk -v port=":$PORT" '$4 ~ port {print $NF}' | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' | head -n 1)"
    if [ -n "$EXISTING_PID" ] && kill -0 "$EXISTING_PID" 2>/dev/null; then
        kill "$EXISTING_PID"
        echo "Stopped procurement backend on port $PORT (PID $EXISTING_PID)."
    fi
fi
