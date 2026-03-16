#!/bin/bash
# Start Goodyear AP Chatbot Local Services

echo "Starting Goodyear AP Chatbot Services..."

# Activate virtual environment
source .venv/bin/activate

# 1. Start External Mock API Tool Server (Port 8003)
echo "Starting External Mock APIs on Port 8003..."
nohup python mock_api.py > mock_api.log 2>&1 &
echo $! > mock_api.pid

# 2. Start SSO Frontend & Proxy Server (Port 8002)
echo "Starting SSO & Proxy Server on Port 8002..."
nohup python mock_sso/main.py > mock_sso_final.log 2>&1 &
echo $! > mock_sso.pid

echo "Services started successfully!"
echo " - Local Web UI: http://localhost:8002"
echo " - Mock Tools API: http://localhost:8003/docs"
