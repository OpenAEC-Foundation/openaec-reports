#!/bin/bash
set -e

echo "=== Deploy openaec-reports-rs (Rust) ==="

echo "1/4 Pulling latest code..."
cd /opt/openaec/bm-reports-api && git pull origin main

echo "2/4 Building Rust container..."
cd /opt/openaec && docker compose build --no-cache openaec-reports-rs

echo "3/4 Deploying..."
docker compose up -d openaec-reports-rs

echo "4/4 Health check..."
sleep 5
if curl -sf https://report-rs.open-aec.com/api/health > /dev/null; then
    echo "✓ Rust API is live: $(curl -s https://report-rs.open-aec.com/api/health)"
else
    echo "✗ Health check failed!"
    docker compose logs --tail=20 openaec-reports-rs
    exit 1
fi

echo "=== Deploy complete ==="
docker compose ps openaec-reports-rs
