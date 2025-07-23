#!/bin/bash
# plugins/gce_scanner/start_scanner.sh

echo "Starting GCE Scanner with auto-fix support..."

# Try to start the scanner
python gce_scanner.py

# Check exit code
if [ $? -ne 0 ]; then
    echo ""
    echo "Scanner failed to start. Attempting auto-fix..."
    echo ""
    
    # Check if it's a GMP version error by testing connection
    python debug_gmp.py 2>&1 | grep -q "unsupported version"
    
    if [ $? -eq 0 ]; then
        echo "Detected GMP version issue. Installing latest python-gvm..."
        pip uninstall -y python-gvm
        pip install git+https://github.com/greenbone/python-gvm.git@main
        
        echo ""
        echo "Retrying scanner startup..."
        python gce_scanner.py
    else
        echo "Error is not related to GMP version. Check logs for details."
        exit 1
    fi
fi