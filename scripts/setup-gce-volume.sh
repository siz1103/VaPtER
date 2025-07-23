#!/bin/bash
# setup-gce-volume.sh

echo "=== Setup GCE Socket Volume for VaPtER ==="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run this script as root (use sudo)"
    exit 1
fi

# Option 1: Use Docker volume
echo "Option 1: Using Docker volume (recommended)"
echo "----------------------------------------"

# Check if gvmd_socket_vol exists
if docker volume ls | grep -q "gvmd_socket_vol"; then
    echo "✓ Volume 'gvmd_socket_vol' already exists"
else
    echo "Creating Docker volume 'gvmd_socket_vol'..."
    docker volume create gvmd_socket_vol
    echo "✓ Volume created"
fi

echo ""
echo "To use this option, ensure both docker-compose files use:"
echo "  volumes:"
echo "    - gvmd_socket_vol:/run/gvmd     # in GCE docker-compose"
echo "    - gvmd_socket_vol:/mnt/gce_sockets:ro  # in VaPtER docker-compose"
echo ""

# Option 2: Use host directory
echo "Option 2: Using host directory"
echo "------------------------------"

GCE_SOCKET_DIR="/opt/gce/sockets"

if [ -d "$GCE_SOCKET_DIR" ]; then
    echo "✓ Directory '$GCE_SOCKET_DIR' already exists"
else
    echo "Creating directory '$GCE_SOCKET_DIR'..."
    mkdir -p "$GCE_SOCKET_DIR"
    echo "✓ Directory created"
fi

# Set permissions (GCE runs as user 1001)
echo "Setting permissions..."
chown 1001:1001 "$GCE_SOCKET_DIR"
chmod 755 "$GCE_SOCKET_DIR"
echo "✓ Permissions set"

echo ""
echo "To use this option, update both docker-compose files:"
echo "  GCE docker-compose.yml:"
echo "    services:"
echo "      gvmd:"
echo "        volumes:"
echo "          - $GCE_SOCKET_DIR:/run/gvmd"
echo ""
echo "  VaPtER docker-compose.yml:"
echo "    services:"
echo "      gce_scanner:"
echo "        volumes:"
echo "          - $GCE_SOCKET_DIR:/mnt/gce_sockets:ro"
echo ""

# Verify current setup
echo "Current Setup Verification"
echo "--------------------------"

# Check if GCE is running
if docker ps | grep -q "gvmd"; then
    echo "✓ GCE gvmd container is running"
    
    # Try to find the socket
    SOCKET_PATH=$(docker exec $(docker ps -q -f name=gvmd) find /run -name "gvmd.sock" 2>/dev/null | head -1)
    if [ -n "$SOCKET_PATH" ]; then
        echo "✓ Socket found at: $SOCKET_PATH (inside container)"
    else
        echo "✗ Socket not found - GCE might still be initializing"
    fi
else
    echo "✗ GCE gvmd container is not running"
    echo "  Start GCE first: cd gce && docker compose -f docker-compose-gce.yml up -d"
fi

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "1. Choose Option 1 (Docker volume) or Option 2 (host directory)"
echo "2. Update the docker-compose files accordingly"
echo "3. Restart the affected containers"
echo "4. Test the connection: docker-compose exec gce_scanner python test_gce.py"