#!/bin/bash
# gce/start-gce.sh

# Script di avvio facilitato per Greenbone Community Edition

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Greenbone Community Edition Startup Script ==="
echo ""

# Check if .env.gce exists
if [ ! -f ".env.gce" ]; then
    echo "Creating .env.gce from template..."
    cp .env.gce.example .env.gce
    echo "✓ Created .env.gce"
    echo ""
    echo "⚠️  Please edit .env.gce and set your passwords!"
    echo "   Then run this script again."
    exit 1
fi

# Load environment variables
export $(cat .env.gce | grep -v '^#' | xargs)

# Function to check if GCE is already running
check_gce_running() {
    if docker compose -f docker-compose-gce.yml ps | grep -q "Up"; then
        return 0
    else
        return 1
    fi
}

# Function to wait for service
wait_for_service() {
    local service=$1
    local max_attempts=60
    local attempt=0
    
    echo -n "Waiting for $service to be ready"
    while [ $attempt -lt $max_attempts ]; do
        if docker compose -f docker-compose-gce.yml logs $service 2>&1 | grep -q "ready\|started\|listening"; then
            echo " ✓"
            return 0
        fi
        echo -n "."
        sleep 5
        attempt=$((attempt+1))
    done
    echo " ✗"
    return 1
}

# Check if already running
if check_gce_running; then
    echo "GCE is already running!"
    echo ""
    docker compose -f docker-compose-gce.yml ps
    echo ""
    echo "Web UI: https://localhost:${GCE_WEB_PORT:-8443}"
    echo "Username: ${GCE_ADMIN_USER:-admin}"
    exit 0
fi

# Start GCE
echo "Starting Greenbone Community Edition..."
echo "This may take a while on first run (downloading feeds)..."
echo ""

docker compose -f docker-compose-gce.yml --env-file .env.gce up -d

# Show initial status
echo ""
echo "Containers started. Waiting for services to be ready..."
echo ""

# Wait for key services
wait_for_service "pg-gvm"
wait_for_service "redis-server"
wait_for_service "gvmd"

echo ""
echo "Checking feed sync status..."
docker compose -f docker-compose-gce.yml logs vulnerability-tests | tail -20

# Create vapter_api user if needed
if [ -f "scripts/setup-vapter-user.sh" ]; then
    echo ""
    echo "Setting up VaPtER API user..."
    docker compose -f docker-compose-gce.yml exec -u gvmd gvmd bash /scripts/setup-vapter-user.sh || true
fi

# Final status
echo ""
echo "=== GCE Startup Complete ==="
echo ""
docker compose -f docker-compose-gce.yml ps
echo ""
echo "Access Points:"
echo "  Web UI: https://localhost:${GCE_WEB_PORT:-8443}"
echo "  API: http://localhost:${GCE_API_PORT:-9390}"
echo ""
echo "Credentials:"
echo "  Admin: ${GCE_ADMIN_USER:-admin} / (password in .env.gce)"
echo "  API User: ${GCE_VAPTER_USER:-vapter_api} / (password in .env.gce)"
echo ""
echo "Logs: docker compose -f docker-compose-gce.yml logs -f"
echo "Stop: docker compose -f docker-compose-gce.yml down"
echo ""

# Reminder about socket volume
echo "⚠️  Remember to configure the socket volume for VaPtER integration!"
echo "   Run: sudo ../setup-gce-volume.sh"