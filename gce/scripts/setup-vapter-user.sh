#!/bin/bash
# gce/scripts/setup-vapter-user.sh

# Script to create vapter_api user in GCE

set -e

# Load environment variables
if [ -f "../.env.gce" ]; then
    export $(cat ../.env.gce | grep -v '^#' | xargs)
else
    echo "Error: .env.gce file not found!"
    echo "Please create it from .env.gce.example"
    exit 1
fi

echo "=== Setting up VaPtER API user in GCE ==="
echo ""

# Default values if not set in .env
VAPTER_USER=${GCE_VAPTER_USER:-vapter_api}
VAPTER_PASSWORD=${GCE_VAPTER_PASSWORD:-vapter_gce_password}

echo "Creating user: $VAPTER_USER"
echo ""

# Wait for GVMD to be ready
echo "Waiting for GVMD to be ready..."
max_attempts=30
attempt=0

while [ ! -S /run/gvmd/gvmd.sock ]; do
    echo "Waiting for GVMD socket... (attempt $((attempt+1))/$max_attempts)"
    sleep 5
    attempt=$((attempt+1))
    if [ $attempt -ge $max_attempts ]; then
        echo "ERROR: GVMD socket not available after $max_attempts attempts"
        exit 1
    fi
done

echo "GVMD is ready!"
echo ""

# Check if user already exists
echo "Checking if user already exists..."
if gvmd --get-users | grep -q "^$VAPTER_USER$"; then
    echo "User '$VAPTER_USER' already exists"
    
    # Update password
    echo "Updating password..."
    gvmd --user="$VAPTER_USER" --new-password="$VAPTER_PASSWORD"
    echo "✓ Password updated successfully"
else
    echo "Creating new user..."
    # Create user with Admin role
    gvmd --create-user="$VAPTER_USER" --password="$VAPTER_PASSWORD"
    
    # Get user ID
    USER_ID=$(gvmd --get-users --verbose | grep "$VAPTER_USER" | awk '{print $2}')
    
    # Assign Admin role
    echo "Assigning Admin role..."
    ADMIN_ROLE_ID=$(gvmd --get-roles | grep -E "Admin.*" | head -1 | awk '{print $1}')
    gvmd --modify-user="$USER_ID" --role="$ADMIN_ROLE_ID"
    
    echo "✓ User created successfully with Admin role"
fi

echo ""
echo "=== Setup complete ==="
echo ""
echo "User credentials for VaPtER:"
echo "  Username: $VAPTER_USER"
echo "  Password: (as configured in .env.gce)"
echo ""
echo "Update your VaPtER .env file with:"
echo "  GCE_USERNAME=$VAPTER_USER"
echo "  GCE_PASSWORD=$VAPTER_PASSWORD"