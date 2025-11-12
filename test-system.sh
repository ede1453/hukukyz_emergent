#!/bin/bash

echo "🧪 HukukYZ - System Test"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

BACKEND_URL="http://localhost:8001"
FRONTEND_URL="http://localhost:3000"
QDRANT_URL="http://localhost:6333"

TESTS_PASSED=0
TESTS_FAILED=0

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

test_service() {
    local name=$1
    local url=$2
    
    if curl -s -f "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name is running"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} $name is NOT running"
        ((TESTS_FAILED++))
        return 1
    fi
}

test_api() {
    local name=$1
    local method=$2
    local endpoint=$3
    local expected=$4
    
    response=$(curl -s -X "$method" "$BACKEND_URL$endpoint")
    
    if echo "$response" | grep -q "$expected"; then
        echo -e "${GREEN}✓${NC} $name"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} $name"
        echo "  Expected: $expected"
        echo "  Got: $response"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Test services
echo "📡 Testing Services..."
test_service "Qdrant" "$QDRANT_URL/health"
test_service "Backend" "$BACKEND_URL/health"
test_service "Frontend" "$FRONTEND_URL"

echo ""
echo "🔌 Testing Backend Endpoints..."
test_api "Health endpoint" "GET" "/health" "healthy"
test_api "Document stats" "GET" "/api/documents/stats" "total_documents"
test_api "Collections list" "GET" "/api/documents/collections" "ticaret_hukuku"

echo ""
echo "🤖 Testing Chat API..."
response=$(curl -s -X POST "$BACKEND_URL/api/chat/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Test", "session_id": "test"}')

if echo "$response" | grep -q "answer"; then
    echo -e "${GREEN}✓${NC} Chat API is working"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} Chat API failed"
    ((TESTS_FAILED++))
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Test Results"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
