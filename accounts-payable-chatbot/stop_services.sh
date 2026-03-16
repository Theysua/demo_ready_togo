#!/bin/bash
# Stop Goodyear AP Chatbot Local Services

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "Stopping Goodyear AP Chatbot Services..."

if [ -f mock_api.pid ]; then
    kill "$(cat mock_api.pid)" 2>/dev/null || true
    rm mock_api.pid
    echo "Stopped External Mock APIs."
else
    # Fallback to lsof
    kill "$(lsof -t -i:8003)" 2>/dev/null || true
fi

if [ -f mock_sso.pid ]; then
    kill "$(cat mock_sso.pid)" 2>/dev/null || true
    rm mock_sso.pid
    echo "Stopped SSO & Proxy Server."
else
    # Fallback to lsof
    kill "$(lsof -t -i:8002)" 2>/dev/null || true
fi

echo "All services stopped."
