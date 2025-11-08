#!/bin/bash

# Test the PayOffOrInvest API

echo "Testing PayOffOrInvest API..."
echo ""

# Test 1: Health check
echo "1. Health check:"
curl -s http://localhost:8001/ | python -m json.tool
echo ""
echo ""

# Test 2: Create analysis (retired user with $5M portfolio)
echo "2. Creating analysis for retired user with $5M portfolio..."
ANALYSIS_ID=$(curl -s -X POST http://localhost:8001/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "employment_status": "retired",
    "mortgage": {
      "balance": 500000,
      "rate": 3.0,
      "years": 25
    },
    "financial": {
      "portfolio": 5000000,
      "spending": 200000,
      "spending_includes_mortgage": true
    }
  }' | python -c "import sys, json; print(json.load(sys.stdin)['analysis_id'])")

echo "Analysis ID: $ANALYSIS_ID"
echo ""

# Test 3: Stream progress
echo "3. Streaming analysis progress..."
echo "(Press Ctrl+C to stop if it hangs)"
echo ""

curl -N http://localhost:8001/api/analysis/$ANALYSIS_ID/progress

echo ""
echo ""

# Test 4: Get final results
echo "4. Getting final results..."
sleep 2
curl -s http://localhost:8001/api/analysis/$ANALYSIS_ID/results | python -m json.tool

echo ""
echo "Test complete!"
