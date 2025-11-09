#!/usr/bin/env python3
"""
Test Multi-Agent Supervisor with Real Queries

This script tests the Multi-Agent Supervisor with actual Genie and Vector Search calls.
"""

import warnings
import os
import sys
from pathlib import Path

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
os.environ["PYTHONWARNINGS"] = "ignore"

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from agents.supervisor import SupervisorAgent
from agents.data_agent import DataAgent
from agents.docs_agent import DocsAgent

# Configuration
CATALOG = "ea_trading"
SCHEMA = "battery_trading"
ENDPOINT_NAME = "one-env-shared-endpoint-10"
INDEX_NAME = f"{CATALOG}.{SCHEMA}.battery_docs_index"
GENIE_ROOM_ID = os.environ.get("GENIE_ROOM_ID", "01f0bca10415147a91fe3c98f80e596e")

print("=" * 80)
print("Multi-Agent Supervisor - Real Query Test")
print("=" * 80)
print()
print(f"Configuration:")
print(f"  Genie Room ID: {GENIE_ROOM_ID}")
print(f"  Vector Search Index: {INDEX_NAME}")
print(f"  Vector Search Endpoint: {ENDPOINT_NAME}")
print()

# Initialize agents
print("🔧 Initializing agents...")
try:
    data_agent = DataAgent(genie_room_id=GENIE_ROOM_ID)
    docs_agent = DocsAgent(index_name=INDEX_NAME, endpoint_name=ENDPOINT_NAME)
    supervisor = SupervisorAgent(data_agent=data_agent, docs_agent=docs_agent)
    print("✅ All agents initialized\n")
except Exception as e:
    print(f"❌ Error initializing agents: {e}")
    sys.exit(1)

# Test queries
test_cases = [
    {
        "question": "What is the current SoC for RESS2?",
        "expected_agent": "Data Agent",
        "description": "Simple data query"
    },
    {
        "question": "How is throughput calculated for batteries?",
        "expected_agent": "Docs Agent",
        "description": "Documentation query"
    },
    {
        "question": "Show me revenue for all batteries in the last 12 hours",
        "expected_agent": "Data Agent",
        "description": "Data aggregation query"
    },
    {
        "question": "Explain the AEMO bidding process",
        "expected_agent": "Docs Agent",
        "description": "Process explanation query"
    },
    {
        "question": "What is the current SoC for RESS2 and how are SoC limits defined?",
        "expected_agent": "Both Agents",
        "description": "Hybrid query"
    },
]

print("=" * 80)
print("Testing with Real Queries")
print("=" * 80)

results = []

for i, test_case in enumerate(test_cases, 1):
    question = test_case["question"]
    expected = test_case["expected_agent"]
    description = test_case["description"]
    
    print(f"\n{'=' * 80}")
    print(f"Test {i}/{len(test_cases)}: {description}")
    print(f"{'=' * 80}")
    print(f"Question: {question}")
    print(f"Expected Agent: {expected}")
    print("-" * 80)
    
    # Check routing
    data_can = data_agent.can_handle(question)
    docs_can = docs_agent.can_handle(question)
    is_hybrid = supervisor._is_hybrid_query(question)
    
    print(f"Routing Analysis:")
    print(f"  Data Agent can handle: {data_can}")
    print(f"  Docs Agent can handle: {docs_can}")
    print(f"  Is hybrid query: {is_hybrid}")
    
    # Determine actual routing
    if is_hybrid or (data_can and docs_can):
        actual_route = "Both Agents"
    elif data_can:
        actual_route = "Data Agent"
    elif docs_can:
        actual_route = "Docs Agent"
    else:
        actual_route = "Default (Data Agent)"
    
    print(f"  → Routes to: {actual_route}")
    
    # Process query
    print(f"\n🔄 Processing query...")
    try:
        response = supervisor.process(question)
        
        # Get logs
        logs = supervisor.get_logs()
        
        print(f"\n✅ Response received ({len(response)} characters)")
        print(f"\n📋 Execution Logs:")
        for log in logs:
            print(f"   {log}")
        
        print(f"\n📝 Response Preview (first 500 chars):")
        print("-" * 80)
        print(response[:500])
        if len(response) > 500:
            print("...")
        print("-" * 80)
        
        # Check for errors
        has_error = "[Data Agent Error]" in response or "[Docs Agent Error]" in response
        if has_error:
            print(f"\n⚠️  Response contains errors")
        else:
            print(f"\n✅ Response looks good")
        
        results.append({
            "test": i,
            "question": question,
            "expected": expected,
            "actual_route": actual_route,
            "success": not has_error,
            "response_length": len(response),
            "has_error": has_error
        })
        
    except Exception as e:
        print(f"\n❌ Error processing query: {e}")
        import traceback
        traceback.print_exc()
        results.append({
            "test": i,
            "question": question,
            "expected": expected,
            "actual_route": actual_route,
            "success": False,
            "error": str(e)
        })
    
    print()

# Summary
print("\n" + "=" * 80)
print("Test Summary")
print("=" * 80)

successful = sum(1 for r in results if r.get("success", False))
total = len(results)

print(f"\nTotal Tests: {total}")
print(f"Successful: {successful}")
print(f"Failed: {total - successful}")
print()

for result in results:
    status = "✅" if result.get("success", False) else "❌"
    print(f"{status} Test {result['test']}: {result['question'][:50]}...")
    print(f"   Route: {result.get('actual_route', 'Unknown')}")
    if result.get("has_error"):
        print(f"   ⚠️  Contains errors")
    elif result.get("success"):
        print(f"   Response length: {result.get('response_length', 0)} chars")

print("\n" + "=" * 80)
print("Testing Complete!")
print("=" * 80)

