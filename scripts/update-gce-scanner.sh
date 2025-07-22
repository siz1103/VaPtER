#!/bin/bash
# update-gce-scanner.sh

echo "=== Updating GCE Scanner for GMP Compatibility ==="
echo ""

# Stop the scanner
echo "Stopping GCE scanner..."
docker-compose stop gce_scanner

# Rebuild with new dependencies
echo "Rebuilding container with updated dependencies..."
docker-compose build --no-cache gce_scanner

# Start the scanner
echo "Starting GCE scanner..."
docker-compose up -d gce_scanner

# Wait a moment for startup
sleep 5

# Test the connection
echo ""
echo "Testing GCE connection..."
docker-compose exec gce_scanner python test_gce.py

echo ""
echo "=== Update Complete ==="
echo ""
echo "Check the logs for any issues:"
echo "  docker-compose logs -f gce_scanner"