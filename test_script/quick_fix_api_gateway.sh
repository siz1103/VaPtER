#!/bin/bash
# quick_fix_api_gateway.sh - Comandi rapidi per fixare l'API Gateway

echo "🛠️  API Gateway Quick Fix"
echo "========================"

echo "1. Stopping API Gateway..."
docker-compose stop api_gateway

echo "2. Rebuilding API Gateway with fixes..."
docker-compose build api_gateway

echo "3. Starting API Gateway..."
docker-compose up -d api_gateway

echo "4. Waiting for startup..."
sleep 15

echo "5. Testing API Gateway..."
if curl -s -f "http://vapter.szini.it:8080/health/" > /dev/null 2>&1; then
    echo "✅ API Gateway is working!"
    
    # Test detailed health
    echo "Testing detailed health..."
    detailed_health=$(curl -s "http://vapter.szini.it:8080/health/detailed")
    echo "$detailed_health" | jq .
    
    echo ""
    echo "🎉 Fix applied successfully!"
    echo "API Gateway is ready at: http://vapter.szini.it:8080"
    
else
    echo "❌ API Gateway is still not working"
    echo "Let's check the logs:"
    docker-compose logs --tail=20 api_gateway
fi