#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AP_DIR="$ROOT_DIR/accounts-payable-chatbot"

echo "Stopping Accounts Payable demo services..."
"$AP_DIR/stop_services.sh"

echo "Stopping Procurement backend..."
if command -v systemctl >/dev/null 2>&1; then
    systemctl stop procurement-backend.service || true
else
    "$ROOT_DIR/procurement-automation/stop_backend.sh"
fi

echo "All demo services stopped."
