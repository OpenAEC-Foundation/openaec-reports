#!/bin/bash
set -e

echo "=== Deploy openaec-reports ==="

echo "1/4 Pulling latest code..."
cd /opt/openaec/bm-reports-api && git pull origin main

echo "2/4 Building container..."
cd /opt/openaec && docker compose build --no-cache bm-reports-api

echo "3/4 Deploying..."
docker compose up -d bm-reports-api

echo "4/4 Health check..."
sleep 3
if curl -sf https://report.open-aec.com/api/health > /dev/null; then
    echo "✓ API is live: $(curl -s https://report.open-aec.com/api/health)"
else
    echo "✗ Health check failed!"
    docker compose logs --tail=20 bm-reports-api
    exit 1
fi

echo "=== Deploy complete ==="
docker compose ps bm-reports-api
