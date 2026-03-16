#!/bin/bash
# Start Goodyear AP Chatbot Local Services

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "Starting Goodyear AP Chatbot Services..."

if [ ! -d .venv ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install -r requirements.txt >/tmp/ap_chatbot_pip.log 2>&1

is_running_on_port() {
    local port="$1"
    ss -ltn "( sport = :$port )" | tail -n +2 | grep -q .
}

# 1. Start External Mock API Tool Server (Port 8003)
if is_running_on_port 8003; then
    echo "External Mock APIs already running on Port 8003."
    if [ -f mock_api.pid ] && ! kill -0 "$(cat mock_api.pid)" 2>/dev/null; then
        rm -f mock_api.pid
    fi
else
    echo "Starting External Mock APIs on Port 8003..."
    nohup python mock_api.py > mock_api.log 2>&1 &
    echo $! > mock_api.pid
fi

# 2. Start SSO Frontend & Proxy Server (Port 8002)
if is_running_on_port 8002; then
    echo "SSO & Proxy Server already running on Port 8002."
    if [ -f mock_sso.pid ] && ! kill -0 "$(cat mock_sso.pid)" 2>/dev/null; then
        rm -f mock_sso.pid
    fi
else
    echo "Starting SSO & Proxy Server on Port 8002..."
    nohup python mock_sso/main.py > mock_sso_final.log 2>&1 &
    echo $! > mock_sso.pid
fi

echo "Services started successfully!"
echo " - Local Web UI: http://localhost:8002"
echo " - Mock Tools API: http://localhost:8003/docs"
