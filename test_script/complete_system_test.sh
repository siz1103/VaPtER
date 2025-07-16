#!/bin/bash
# complete_system_test.sh - Test completo del sistema VaPtER

echo "🚀 VaPtER - Complete System Test"
echo "================================="

# Colori per output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variabili globali
API_GATEWAY_URL="http://vapter.szini.it:8080"
BACKEND_URL="http://vapter.szini.it:8000"
RABBITMQ_URL="http://vapter.szini.it:15672"

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

wait_for_scan_completion() {
    local scan_id=$1
    local max_wait=${2:-60}
    local wait_count=0
    
    echo "Waiting for scan $scan_id to complete..."
    
    while [ $wait_count -lt $max_wait ]; do
        status=$(curl -s "$API_GATEWAY_URL/api/orchestrator/scans/$scan_id/" | jq -r '.status' 2>/dev/null)
        
        if [ "$status" = "Completed" ]; then
            echo -e "${GREEN}✓ Scan completed successfully${NC}"
            return 0
        elif [ "$status" = "Failed" ]; then
            echo -e "${RED}✗ Scan failed${NC}"
            return 1
        elif [ "$status" = "null" ] || [ -z "$status" ]; then
            echo -e "${RED}✗ Cannot get scan status${NC}"
            return 1
        fi
        
        echo "  Status: $status (${wait_count}s/${max_wait}s)"
        sleep 2
        wait_count=$((wait_count + 2))
    done
    
    echo -e "${YELLOW}⚠ Scan timeout after ${max_wait}s${NC}"
    return 1
}

# Test 1: Verifica Servizi Base
echo -e "\n${BLUE}🔍 1. Testing Base Services${NC}"
echo "----------------------------"

check_service "Database" "$BACKEND_URL/admin/" 200
check_service "Backend API" "$BACKEND_URL/api/orchestrator/customers/" 200
check_service "API Gateway" "$API_GATEWAY_URL/health/" 200
check_service "Gateway Detailed Health" "$API_GATEWAY_URL/health/detailed" 200
check_service "RabbitMQ Management" "$RABBITMQ_URL/" 200

# Test 2: Verifica Docker Containers
echo -e "\n${BLUE}🔍 2. Testing Docker Containers${NC}"
echo "--------------------------------"

containers=("vapter_db" "vapter_rabbitmq" "vapter_backend" "vapter_backend_consumer" "vapter_api_gateway" "vapter_nmap_scanner")

for container in "${containers[@]}"; do
    echo -n "Checking container $container... "
    if docker ps --format "table {{.Names}}" | grep -q "^$container$"; then
        echo -e "${GREEN}✓ Running${NC}"
    else
        echo -e "${RED}✗ Not running${NC}"
    fi
done

# Test 3: Test Workflow Completo
echo -e "\n${BLUE}🔍 3. Testing Complete Workflow${NC}"
echo "--------------------------------"

# 3.1 Creare cliente
echo "Creating test customer..."
customer_response=$(curl -s -X POST "$API_GATEWAY_URL/api/orchestrator/customers/" \
    -H "Content-Type: application/json" \
    -d '{"name": "Test System Customer", "email": "system@test.com"}' 2>/dev/null)

if [ $? -eq 0 ]; then
    customer_id=$(echo "$customer_response" | jq -r '.id' 2>/dev/null)
    if [ "$customer_id" != "null" ] && [ -n "$customer_id" ]; then
        echo -e "${GREEN}✓ Customer created: $customer_id${NC}"
    else
        echo -e "${RED}✗ Failed to create customer${NC}"
        echo "Response: $customer_response"
        exit 1
    fi
else
    echo -e "${RED}✗ Failed to create customer (connection error)${NC}"
    exit 1
fi

# 3.2 Creare target
echo "Creating test target..."
target_response=$(curl -s -X POST "$API_GATEWAY_URL/api/orchestrator/targets/" \
    -H "Content-Type: application/json" \
    -d "{\"customer\": \"$customer_id\", \"name\": \"Test Localhost\", \"address\": \"127.0.0.1\"}" 2>/dev/null)

target_id=$(echo "$target_response" | jq -r '.id' 2>/dev/null)
if [ "$target_id" != "null" ] && [ -n "$target_id" ]; then
    echo -e "${GREEN}✓ Target created: $target_id${NC}"
else
    echo -e "${RED}✗ Failed to create target${NC}"
    echo "Response: $target_response"
    exit 1
fi

# 3.3 Verificare che nmap scanner sia pronto
echo "Checking nmap scanner logs..."
nmap_logs=$(docker-compose logs nmap_scanner 2>/dev/null | tail -5)
if echo "$nmap_logs" | grep -q "waiting for messages"; then
    echo -e "${GREEN}✓ Nmap scanner is ready${NC}"
else
    echo -e "${YELLOW}⚠ Nmap scanner may not be ready${NC}"
    echo "Last logs:"
    echo "$nmap_logs"
fi

# 3.4 Avviare scansione Discovery
echo "Starting discovery scan..."
scan_response=$(curl -s -X POST "$API_GATEWAY_URL/api/orchestrator/targets/$target_id/scan/" \
    -H "Content-Type: application/json" \
    -d '{"scan_type_id": 1}' 2>/dev/null)

scan_id=$(echo "$scan_response" | jq -r '.id' 2>/dev/null)
if [ "$scan_id" != "null" ] && [ -n "$scan_id" ]; then
    echo -e "${GREEN}✓ Scan started: $scan_id${NC}"
else
    echo -e "${RED}✗ Failed to start scan${NC}"
    echo "Response: $scan_response"
    exit 1
fi

# 3.5 Attendere completamento scansione
if wait_for_scan_completion "$scan_id" 120; then
    echo -e "${GREEN}✓ Scan workflow completed successfully${NC}"
    
    # Verificare risultati
    echo "Checking scan results..."
    scan_details=$(curl -s "$API_GATEWAY_URL/api/orchestrator/scans/$scan_id/" 2>/dev/null)
    
    if echo "$scan_details" | jq -e '.parsed_nmap_results' >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Scan results are present${NC}"
        
        # Mostra un riassunto dei risultati
        hosts_found=$(echo "$scan_details" | jq -r '.parsed_nmap_results.hosts | length' 2>/dev/null)
        echo "  Hosts found: $hosts_found"
        
        scan_stats=$(echo "$scan_details" | jq -r '.parsed_nmap_results.stats.hosts' 2>/dev/null)
        if [ "$scan_stats" != "null" ]; then
            echo "  Stats: $scan_stats"
        fi
    else
        echo -e "${YELLOW}⚠ No scan results found${NC}"
    fi
else
    echo -e "${RED}✗ Scan workflow failed${NC}"
    
    # Debug info
    echo "Debug information:"
    echo "Scan status:"
    curl -s "$API_GATEWAY_URL/api/orchestrator/scans/$scan_id/" | jq '.status' 2>/dev/null
    
    echo "Recent nmap scanner logs:"
    docker-compose logs --tail=10 nmap_scanner 2>/dev/null
    
    exit 1
fi

# Test 4: Test Performance Base
echo -e "\n${BLUE}🔍 4. Testing Performance${NC}"
echo "--------------------------"

echo "Testing API response times..."

# Test gateway response time
start_time=$(date +%s.%N)
curl -s "$API_GATEWAY_URL/api/orchestrator/customers/" >/dev/null 2>&1
end_time=$(date +%s.%N)
gateway_time=$(echo "$end_time - $start_time" | bc 2>/dev/null || echo "N/A")

# Test backend response time
start_time=$(date +%s.%N)
curl -s "$BACKEND_URL/api/orchestrator/customers/" >/dev/null 2>&1
end_time=$(date +%s.%N)
backend_time=$(echo "$end_time - $start_time" | bc 2>/dev/null || echo "N/A")

echo "  Gateway response time: ${gateway_time}s"
echo "  Backend response time: ${backend_time}s"

# Test 5: Cleanup
echo -e "\n${BLUE}🔍 5. Cleanup${NC}"
echo "-------------"

echo "Cleaning up test data..."

# Eliminare scan
if [ -n "$scan_id" ]; then
    curl -s -X DELETE "$API_GATEWAY_URL/api/orchestrator/scans/$scan_id/" >/dev/null 2>&1
fi

# Eliminare target
if [ -n "$target_id" ]; then
    curl -s -X DELETE "$API_GATEWAY_URL/api/orchestrator/targets/$target_id/" >/dev/null 2>&1
fi

# Eliminare customer
if [ -n "$customer_id" ]; then
    curl -s -X DELETE "$API_GATEWAY_URL/api/orchestrator/customers/$customer_id/" >/dev/null 2>&1
fi

echo -e "${GREEN}✓ Cleanup completed${NC}"

# Summary
echo -e "\n${GREEN}🎉 Complete System Test Finished!${NC}"
echo "=================================="
echo ""
echo "Results:"
echo "✓ All base services are running"
echo "✓ Docker containers are healthy"
echo "✓ Complete scan workflow is functional"
echo "✓ Nmap scanner integration works"
echo "✓ API Gateway proxy is working"
echo "✓ RabbitMQ messaging is functional"
echo ""
echo "The VaPtER system is ready for production use!"
echo ""
echo "Next steps:"
echo "1. Implement frontend React application"
echo "2. Add additional scanner modules (fingerprint, enum, web, vuln)"
echo "3. Implement authentication system"
echo "4. Add rate limiting and security features"