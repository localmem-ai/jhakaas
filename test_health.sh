#!/bin/bash
# Quick health check for Cloud Run worker
# Usage: ./test_health.sh <CLOUD_RUN_URL>

WORKER_URL="${1}"

if [ -z "$WORKER_URL" ]; then
    echo "Usage: ./test_health.sh <CLOUD_RUN_URL>"
    echo "Example: ./test_health.sh https://jhakaas-worker-xxx.a.run.app"
    exit 1
fi

echo "Testing: $WORKER_URL/health"
echo ""

curl -s "$WORKER_URL/health" | python3 -m json.tool

echo ""
