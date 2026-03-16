#!/bin/bash
# Stop Goodyear AP Chatbot Local Services

echo "Stopping Goodyear AP Chatbot Services..."

if [ -f mock_api.pid ]; then
    kill -9 $(cat mock_api.pid) 2>/dev/null
    rm mock_api.pid
    echo "Stopped External Mock APIs."
else
    # Fallback to lsof
    kill -9 $(lsof -t -i:8003) 2>/dev/null
fi

if [ -f mock_sso.pid ]; then
    kill -9 $(cat mock_sso.pid) 2>/dev/null
    rm mock_sso.pid
    echo "Stopped SSO & Proxy Server."
else
    # Fallback to lsof
    kill -9 $(lsof -t -i:8002) 2>/dev/null
fi

echo "All services stopped."
