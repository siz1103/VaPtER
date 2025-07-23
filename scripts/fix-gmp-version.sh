#!/bin/bash
# fix-gmp-version.sh

echo "=== Fixing GMP Version Compatibility ==="
echo ""
echo "This script will install the latest python-gvm from GitHub"
echo "which should support GMP 22.x"
echo ""

# Install latest python-gvm from GitHub
echo "Installing latest python-gvm..."
docker-compose exec -T gce_scanner pip uninstall -y python-gvm
docker-compose exec -T gce_scanner pip install git+https://github.com/greenbone/python-gvm.git@main

# Test the fix
echo ""
echo "Testing connection..."
docker-compose exec gce_scanner python debug_gmp.py

echo ""
echo "If the connection test passed, try:"
echo "  docker-compose restart gce_scanner"
echo "  docker-compose logs -f gce_scanner"