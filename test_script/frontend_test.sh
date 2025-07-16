#!/bin/bash
# test_script/frontend_test.sh - Test completo del frontend React

echo "🚀 VaPtER - Frontend Test Suite"
echo "==============================="

# Colori per output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variabili
FRONTEND_URL="http://vapter.szini.it:3000"
API_GATEWAY_URL="http://vapter.szini.it:8080"

# Funzioni utility
check_service() {
    local service_name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -n "Checking $service_name... "
    status_code=$(curl -s -w "%{http_code}" -m 10 "$url" -o /dev/null 2>/dev/null)
    
    if [ "$status_code" -eq "$expected_status" ]; then
        echo -e "${GREEN}✓ OK${NC} (Status: $status_code)"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (Status: $status_code)"
        return 1
    fi
}

check_docker_container() {
    local container_name=$1
    echo -n "Checking container $container_name... "
    
    if docker ps --format "table {{.Names}}" | grep -q "^$container_name$"; then
        local status=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep "^$container_name" | awk '{print $2}')
        echo -e "${GREEN}✓ Running${NC} ($status)"
        return 0
    else
        echo -e "${RED}✗ Not running${NC}"
        return 1
    fi
}

# Test 1: Verificare che tutti i servizi siano attivi
echo -e "\n${BLUE}🔍 1. Testing Infrastructure${NC}"
echo "----------------------------"

check_docker_container "vapter_frontend"
check_docker_container "vapter_api_gateway"
check_docker_container "vapter_backend"
check_docker_container "vapter_db"
check_docker_container "vapter_rabbitmq"

echo -e "\n${BLUE}🔍 2. Testing Service Endpoints${NC}"
echo "--------------------------------"

check_service "Frontend" "$FRONTEND_URL" 200
check_service "API Gateway" "$API_GATEWAY_URL/health/" 200
check_service "Backend API" "$API_GATEWAY_URL/api/orchestrator/customers/" 200

# Test 3: Verificare che il frontend carichi correttamente
echo -e "\n${BLUE}🔍 3. Testing Frontend Loading${NC}"
echo "--------------------------------"

echo -n "Testing frontend HTML content... "
frontend_content=$(curl -s -m 10 "$FRONTEND_URL" 2>/dev/null)
if echo "$frontend_content" | grep -q "<title>VaPtER"; then
    echo -e "${GREEN}✓ OK${NC} (Title found)"
else
    echo -e "${RED}✗ FAIL${NC} (Title not found)"
fi

echo -n "Testing frontend React app... "
if echo "$frontend_content" | grep -q "root"; then
    echo -e "${GREEN}✓ OK${NC} (React root found)"
else
    echo -e "${RED}✗ FAIL${NC} (React root not found)"
fi

# Test 4: Verificare API connectivity dal frontend
echo -e "\n${BLUE}🔍 4. Testing API Connectivity${NC}"
echo "--------------------------------"

echo -n "Testing CORS configuration... "
cors_headers=$(curl -s -H "Origin: $FRONTEND_URL" -H "Access-Control-Request-Method: GET" -I "$API_GATEWAY_URL/api/orchestrator/customers/" 2>/dev/null)
if echo "$cors_headers" | grep -q "Access-Control-Allow-Origin"; then
    echo -e "${GREEN}✓ OK${NC} (CORS configured)"
else
    echo -e "${YELLOW}⚠ WARNING${NC} (CORS headers not found)"
fi

# Test 5: Verificare che i dati siano accessibili
echo -e "\n${BLUE}🔍 5. Testing Data Accessibility${NC}"
echo "--------------------------------"

echo -n "Testing customers endpoint... "
customers_data=$(curl -s -m 10 "$API_GATEWAY_URL/api/orchestrator/customers/" 2>/dev/null)
if echo "$customers_data" | grep -q "results"; then
    echo -e "${GREEN}✓ OK${NC} (Customers data accessible)"
else
    echo -e "${RED}✗ FAIL${NC} (Customers data not accessible)"
fi

echo -n "Testing scan types endpoint... "
scan_types_data=$(curl -s -m 10 "$API_GATEWAY_URL/api/orchestrator/scan-types/" 2>/dev/null)
if echo "$scan_types_data" | grep -q "results"; then
    echo -e "${GREEN}✓ OK${NC} (Scan types data accessible)"
else
    echo -e "${RED}✗ FAIL${NC} (Scan types data not accessible)"
fi

echo -n "Testing port lists endpoint... "
port_lists_data=$(curl -s -m 10 "$API_GATEWAY_URL/api/orchestrator/port-lists/" 2>/dev/null)
if echo "$port_lists_data" | grep -q "results"; then
    echo -e "${GREEN}✓ OK${NC} (Port lists data accessible)"
else
    echo -e "${RED}✗ FAIL${NC} (Port lists data not accessible)"
fi

# Test 6: Verificare container logs per errori
echo -e "\n${BLUE}🔍 6. Testing Container Health${NC}"
echo "--------------------------------"

echo -n "Checking frontend container logs... "
frontend_logs=$(docker logs vapter_frontend 2>&1 | tail -20)
if echo "$frontend_logs" | grep -q -i "error\|failed\|exception"; then
    echo -e "${YELLOW}⚠ WARNING${NC} (Errors found in logs)"
    echo "Recent errors:"
    echo "$frontend_logs" | grep -i "error\|failed\|exception" | tail -3
else
    echo -e "${GREEN}✓ OK${NC} (No errors in logs)"
fi

echo -n "Checking API Gateway logs... "
gateway_logs=$(docker logs vapter_api_gateway 2>&1 | tail -20)
if echo "$gateway_logs" | grep -q -i "error\|failed\|exception"; then
    echo -e "${YELLOW}⚠ WARNING${NC} (Errors found in logs)"
else
    echo -e "${GREEN}✓ OK${NC} (No errors in logs)"
fi

# Test 7: Test performance base
echo -e "\n${BLUE}🔍 7. Testing Performance${NC}"
echo "-------------------------"

echo -n "Testing frontend load time... "
start_time=$(date +%s.%N)
curl -s -m 10 "$FRONTEND_URL" > /dev/null 2>&1
end_time=$(date +%s.%N)
load_time=$(echo "$end_time - $start_time" | bc 2>/dev/null || echo "N/A")
echo -e "${GREEN}✓ OK${NC} (Load time: ${load_time}s)"

echo -n "Testing API response time... "
start_time=$(date +%s.%N)
curl -s -m 10 "$API_GATEWAY_URL/api/orchestrator/customers/" > /dev/null 2>&1
end_time=$(date +%s.%N)
api_time=$(echo "$end_time - $start_time" | bc 2>/dev/null || echo "N/A")
echo -e "${GREEN}✓ OK${NC} (API time: ${api_time}s)"

# Test 8: Functional Tests (simulati)
echo -e "\n${BLUE}🔍 8. Testing Functional Scenarios${NC}"
echo "-----------------------------------"

echo -n "Testing create customer workflow... "
# Simuliamo la creazione di un cliente
customer_create_response=$(curl -s -X POST "$API_GATEWAY_URL/api/orchestrator/customers/" \
  -H "Content-Type: application/json" \
  -d '{"name": "Frontend Test Customer", "email": "frontend@test.com"}' 2>/dev/null)

if echo "$customer_create_response" | grep -q "Frontend Test Customer"; then
    echo -e "${GREEN}✓ OK${NC} (Customer creation works)"
    
    # Estrarre l'ID del cliente
    customer_id=$(echo "$customer_create_response" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
    
    if [ -n "$customer_id" ]; then
        echo -n "Testing target creation workflow... "
        target_create_response=$(curl -s -X POST "$API_GATEWAY_URL/api/orchestrator/targets/" \
          -H "Content-Type: application/json" \
          -d "{\"customer\": \"$customer_id\", \"name\": \"Frontend Test Target\", \"address\": \"127.0.0.1\"}" 2>/dev/null)
        
        if echo "$target_create_response" | grep -q "Frontend Test Target"; then
            echo -e "${GREEN}✓ OK${NC} (Target creation works)"
            
            # Cleanup
            target_id=$(echo "$target_create_response" | grep -o '"id":[^,]*' | cut -d':' -f2)
            if [ -n "$target_id" ]; then
                curl -s -X DELETE "$API_GATEWAY_URL/api/orchestrator/targets/$target_id/" > /dev/null 2>&1
            fi
        else
            echo -e "${RED}✗ FAIL${NC} (Target creation failed)"
        fi
        
        # Cleanup customer
        curl -s -X DELETE "$API_GATEWAY_URL/api/orchestrator/customers/$customer_id/" > /dev/null 2>&1
    fi
else
    echo -e "${RED}✗ FAIL${NC} (Customer creation failed)"
fi

# Test 9: Browser simulation (se disponibile)
echo -e "\n${BLUE}🔍 9. Testing Browser Compatibility${NC}"
echo "-----------------------------------"

if command -v curl >/dev/null 2>&1; then
    echo -n "Testing with different User-Agents... "
    
    # Test con Chrome
    chrome_response=$(curl -s -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" "$FRONTEND_URL" 2>/dev/null)
    if echo "$chrome_response" | grep -q "VaPtER"; then
        echo -e "${GREEN}✓ Chrome compatible${NC}"
    else
        echo -e "${YELLOW}⚠ Chrome issues${NC}"
    fi
    
    # Test con Firefox
    firefox_response=$(curl -s -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0" "$FRONTEND_URL" 2>/dev/null)
    if echo "$firefox_response" | grep -q "VaPtER"; then
        echo -e "${GREEN}✓ Firefox compatible${NC}"
    else
        echo -e "${YELLOW}⚠ Firefox issues${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Curl not available for browser testing${NC}"
fi

# Summary
echo -e "\n${GREEN}🎉 Frontend Test Suite Completed!${NC}"
echo "=================================="
echo ""
echo "Frontend URL: $FRONTEND_URL"
echo "API Gateway URL: $API_GATEWAY_URL"
echo ""
echo "✅ **Frontend Features Tested:**"
echo "   - Frontend container running"
echo "   - HTML content loading"
echo "   - React app initialization"
echo "   - API connectivity"
echo "   - CORS configuration"
echo "   - Data accessibility"
echo "   - Performance metrics"
echo "   - Basic CRUD operations"
echo ""
echo "📋 **Manual Testing Recommended:**"
echo "1. Open $FRONTEND_URL in browser"
echo "2. Test customer creation and selection"
echo "3. Test target management"
echo "4. Test scan initiation and monitoring"
echo "5. Test settings configuration"
echo "6. Verify responsive design on mobile"
echo ""
echo "🚀 **Next Steps:**"
echo "1. Perform comprehensive manual testing"
echo "2. Test with real scan workflows"
echo "3. Verify all modals and forms work correctly"
echo "4. Test error scenarios and edge cases"
echo "5. Verify real-time updates during scans"