#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AP_DIR="$ROOT_DIR/accounts-payable-chatbot"
PROC_DIR="$ROOT_DIR/procurement-automation"

ensure_port_allowed() {
    local port="$1"
    if ! ufw status | grep -q "^${port}/tcp[[:space:]]\+ALLOW IN"; then
        echo "Opening firewall port ${port}/tcp..."
        ufw allow "${port}/tcp" >/dev/null
    else
        echo "Firewall port ${port}/tcp already allowed."
    fi
}

check_http() {
    local name="$1"
    local url="$2"
    for _ in $(seq 1 10); do
        if curl -sS --max-time 5 "$url" >/dev/null 2>&1; then
            echo "[OK] $name -> $url"
            return
        fi
        sleep 1
    done
    echo "[WARN] $name not reachable -> $url"
}

echo "Ensuring required firewall ports are open..."
ensure_port_allowed 8000
ensure_port_allowed 8002
ensure_port_allowed 8003
ufw reload >/dev/null

echo "Starting Accounts Payable demo services..."
"$AP_DIR/start_services.sh"

echo "Starting Procurement backend..."
if command -v systemctl >/dev/null 2>&1; then
    systemctl start procurement-backend.service
else
    "$PROC_DIR/start_backend.sh"
fi

echo
echo "Service health summary:"
check_http "Procurement backend" "http://127.0.0.1:8000/health"
check_http "AP SSO UI" "http://127.0.0.1:8002/"
check_http "AP mock API" "http://127.0.0.1:8003/docs"

echo
echo "Ports:"
echo " - Procurement backend: http://127.0.0.1:8000"
echo " - AP SSO UI:           http://127.0.0.1:8002"
echo " - AP mock API:         http://127.0.0.1:8003/docs"
