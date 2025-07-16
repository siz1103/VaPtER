#!/bin/bash
# quick_test.sh - Script di test rapido per l'API Gateway

echo "🚀 VaPtER - Test Rapido API Gateway"
echo "=================================="

# Colori per output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funzione per test con timeout
test_endpoint() {
    local url=$1
    local description=$2
    local expected_status=${3:-200}
    
    echo -n "Testing $description... "
    
    # Test con timeout di 10 secondi
    response=$(curl -s -w "%{http_code}" -m 10 "$url" 2>/dev/null)
    status_code="${response: -3}"
    
    if [ "$status_code" -eq "$expected_status" ]; then
        echo -e "${GREEN}✓ OK${NC} (Status: $status_code)"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (Status: $status_code, Expected: $expected_status)"
        return 1
    fi
}

echo ""
echo "🔍 1. Testing API Gateway Health"
echo "--------------------------------"

test_endpoint "http://vapter.szini.it:8080/health/" "Gateway Base Health"
test_endpoint "http://vapter.szini.it:8080/health/detailed" "Gateway Detailed Health"
test_endpoint "http://vapter.szini.it:8080/health/readiness" "Gateway Readiness"
test_endpoint "http://vapter.szini.it:8080/health/liveness" "Gateway Liveness"

echo ""
echo "🔍 2. Testing Gateway Documentation"
echo "----------------------------------"

test_endpoint "http://vapter.szini.it:8080/docs" "Gateway Swagger UI"
test_endpoint "http://vapter.szini.it:8080/" "Gateway Root"

echo ""
echo "🔍 3. Testing API Proxy Functionality"
echo "------------------------------------"

test_endpoint "http://vapter.szini.it:8080/api/orchestrator/customers/" "Customers via Gateway"
test_endpoint "http://vapter.szini.it:8080/api/orchestrator/port-lists/" "Port Lists via Gateway"
test_endpoint "http://vapter.szini.it:8080/api/orchestrator/scan-types/" "Scan Types via Gateway"

echo ""
echo "🔍 4. Testing Backend Direct Access"
echo "----------------------------------"

test_endpoint "http://vapter.szini.it:8000/api/orchestrator/customers/" "Customers Direct Backend"
test_endpoint "http://vapter.szini.it:8000/admin/" "Django Admin"

echo ""
echo "🔍 5. Testing RabbitMQ Management"
echo "--------------------------------"

test_endpoint "http://vapter.szini.it:15672/" "RabbitMQ Management UI"

echo ""
echo "🔍 6. Testing Request Headers"
echo "----------------------------"

echo -n "Testing Gateway Custom Headers... "
response=$(curl -s -I http://vapter.szini.it:8080/api/orchestrator/customers/ 2>/dev/null)

if echo "$response" | grep -q "X-Request-ID"; then
    echo -e "${GREEN}✓ X-Request-ID present${NC}"
else
    echo -e "${RED}✗ X-Request-ID missing${NC}"
fi

if echo "$response" | grep -q "X-Process-Time"; then
    echo -e "${GREEN}✓ X-Process-Time present${NC}"
else
    echo -e "${RED}✗ X-Process-Time missing${NC}"
fi

echo ""
echo "🔍 7. Testing Error Handling"
echo "---------------------------"

test_endpoint "http://vapter.szini.it:8080/api/orchestrator/nonexistent/" "404 Error Handling" 404

echo ""
echo "📊 Test Summary"
echo "==============="

# Test POST functionality
echo -n "Testing POST via Gateway... "
post_response=$(curl -s -w "%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -d '{"name": "Test API Gateway", "email": "test@gateway.com"}' \
    http://vapter.szini.it:8080/api/orchestrator/customers/ 2>/dev/null)

post_status="${post_response: -3}"

if [ "$post_status" -eq "201" ]; then
    echo -e "${GREEN}✓ POST Working${NC}"
else
    echo -e "${YELLOW}⚠ POST Status: $post_status${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Test completato!${NC}"
echo ""
echo "Next steps:"
echo "1. Verificare i logs: docker-compose logs -f api_gateway"
echo "2. Testare manualmente: http://vapter.szini.it:8080/docs"
echo "3. Procedere con l'implementazione del frontend o dei moduli scanner"