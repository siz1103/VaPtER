#!/bin/bash
# gce/scripts/setup-admin.sh
# Script per configurare l'utente admin di GCE

set -e

echo "Waiting for GVMD to be ready..."

# Wait for gvmd socket to be available
max_attempts=60
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

echo "GVMD socket is available"

# Wait a bit more to ensure gvmd is fully initialized
sleep 10

# Check if admin user exists
if gvm-cli socket --gmp-username admin --gmp-password admin --xml "<get_users/>" 2>/dev/null | grep -q "<name>admin</name>"; then
    echo "Admin user already exists"
    
    # Update password if different from default
    if [ "$GCE_ADMIN_PASSWORD" != "admin" ]; then
        echo "Updating admin password..."
        gvm-cli socket --gmp-username admin --gmp-password admin --xml "<modify_user user_id='admin'><password>$GCE_ADMIN_PASSWORD</password></modify_user>"
        echo "Admin password updated successfully"
    fi
else
    echo "Creating admin user..."
    # Create admin user with gmp protocol
    gvm-cli socket --xml "<create_user><name>$GCE_ADMIN_USER</name><password>$GCE_ADMIN_PASSWORD</password><role>Admin</role></create_user>"
    echo "Admin user created successfully"
fi

echo "Setup completed!"
echo "You can now login with:"
echo "  Username: $GCE_ADMIN_USER"
echo "  Password: (the one you set in .env.gce)"