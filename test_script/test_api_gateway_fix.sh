#!/bin/bash
# test_api_gateway_fix.sh - Script per testare il fix dell'API Gateway

echo "🔧 API Gateway Configuration Fix Test"
echo "====================================="

# 1. Test di debug della configurazione
echo "🔍 1. Testing configuration debug..."
echo "------------------------------------"

if docker-compose exec api_gateway python3 debug_config.py 2>&1; then
    echo "✅ Configuration debug successful"
else
    echo "❌ Configuration debug failed"
    echo "Let's check what's happening..."
    
    # Check if the debug script exists
    if docker-compose exec api_gateway ls -la debug_config.py 2>/dev/null; then
        echo "Debug script exists"
    else
        echo "Debug script missing, creating it..."
        docker-compose exec api_gateway bash -c 'cat > debug_config.py << EOF
import os
print("Environment variables:")
for key in sorted(os.environ.keys()):
    if "CORS" in key or "BACKEND" in key or "DEBUG" in key:
        print(f"{key}={os.environ[key]}")

try:
    from app.config import settings
    print("✅ Config loaded successfully")
    print(f"CORS Origins: {settings.cors_origins_list}")
except Exception as e:
    print(f"❌ Config error: {e}")
EOF'
        
        # Try again
        docker-compose exec api_gateway python3 debug_config.py
    fi
fi

echo ""
echo "🔄 2. Restarting API Gateway..."
echo "------------------------------"

docker-compose restart api_gateway

echo "Waiting for API Gateway to start..."
sleep 10

echo ""
echo "🧪 3. Testing API Gateway endpoints..."
echo "------------------------------------"

# Test health endpoint
echo -n "Testing health endpoint: "
if curl -s -f "http://vapter.szini.it:8080/health/" > /dev/null 2>&1; then
    echo "✅ OK"
else
    echo "❌ FAILED"
fi

# Test root endpoint
echo -n "Testing root endpoint: "
if curl -s -f "http://vapter.szini.it:8080/" > /dev/null 2>&1; then
    echo "✅ OK"
else
    echo "❌ FAILED"
fi

# Test detailed health
echo -n "Testing detailed health: "
if curl -s -f "http://vapter.szini.it:8080/health/detailed" > /dev/null 2>&1; then
    echo "✅ OK"
else
    echo "❌ FAILED"
fi

# Test CORS headers
echo -n "Testing CORS headers: "
cors_test=$(curl -s -H "Origin: http://localhost:3000" -H "Access-Control-Request-Method: GET" -X OPTIONS "http://vapter.szini.it:8080/health/")
if echo "$cors_test" | grep -q "Access-Control-Allow-Origin"; then
    echo "✅ OK"
else
    echo "❌ FAILED"
fi

echo ""
echo "📊 4. Checking API Gateway logs..."
echo "--------------------------------"

echo "Last 10 lines of API Gateway logs:"
docker-compose logs --tail=10 api_gateway

echo ""
echo "🎯 Test Summary"
echo "==============="

# Check if API Gateway is running
if docker-compose ps api_gateway | grep -q "Up"; then
    echo "✅ API Gateway container is running"
    
    # Check if it's responding
    if curl -s -f "http://vapter.szini.it:8080/health/" > /dev/null 2>&1; then
        echo "✅ API Gateway is responding to requests"
        echo "✅ Configuration fix successful!"
        echo ""
        echo "🚀 API Gateway is ready! Test it at:"
        echo "   - Health: http://vapter.szini.it:8080/health/"
        echo "   - Docs: http://vapter.szini.it:8080/docs"
        echo "   - API: http://vapter.szini.it:8080/api/orchestrator/"
    else
        echo "❌ API Gateway is not responding"
        echo "Check the logs above for errors"
    fi
else
    echo "❌ API Gateway container is not running"
    echo "Try: docker-compose up -d api_gateway"
fi