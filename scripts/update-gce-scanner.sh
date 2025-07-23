#!/bin/bash
# update-gce-scanner.sh

echo "=== Updating GCE Scanner for GMP Compatibility ==="
echo ""

# Stop the scanner
echo "Stopping GCE scanner..."
docker-compose stop gce_scanner

# Remove old image to force rebuild
echo "Removing old image..."
docker rmi $(docker images | grep vapter_gce_scanner | awk '{print $3}') 2>/dev/null || true

# Rebuild with new dependencies
echo "Rebuilding container with updated dependencies..."
docker-compose build --no-cache gce_scanner

# Start the scanner
echo "Starting GCE scanner..."
docker-compose up -d gce_scanner

# Wait a moment for startup
sleep 5

# Run debug script first
echo ""
echo "Running debug diagnostics..."
docker-compose exec gce_scanner python debug_gmp.py

# Test the connection
echo ""
echo "Testing GCE connection..."
docker-compose exec gce_scanner python test_gce.py

echo ""
echo "=== Update Complete ==="
echo ""
echo "If you still see version errors, try:"
echo "1. Check the debug output above"
echo "2. Update GCE to a compatible version"
echo "3. Use requirements-alt.txt for latest python-gvm from GitHub:"
echo "   docker-compose exec gce_scanner pip install -r requirements-alt.txt"
echo ""
echo "Check the logs for any issues:"
echo "  docker-compose logs -f gce_scanner"