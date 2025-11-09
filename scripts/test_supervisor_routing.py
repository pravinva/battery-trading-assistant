#!/usr/bin/env python3
"""
Test script for Multi-Agent Supervisor

Tests routing logic and agent initialization without making actual API calls.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from agents.supervisor import SupervisorAgent
from agents.data_agent import DataAgent
from agents.docs_agent import DocsAgent

# Configuration
GENIE_ROOM_ID = "01f0bca10415147a91fe3c98f80e596e"
INDEX_NAME = "ea_trading.battery_trading.battery_docs_index"
ENDPOINT_NAME = "one-env-shared-endpoint-10"

print("=" * 80)
print("Multi-Agent Supervisor - Routing Test")
print("=" * 80)

# Initialize agents
print("\n🔧 Initializing agents...")
data_agent = DataAgent(genie_room_id=GENIE_ROOM_ID)
docs_agent = DocsAgent(index_name=INDEX_NAME, endpoint_name=ENDPOINT_NAME)
supervisor = SupervisorAgent(data_agent=data_agent, docs_agent=docs_agent)
print("✅ All agents initialized\n")

# Test questions
test_questions = [
    ("What is the current SoC for RESS2?", "Data query"),
    ("How is throughput calculated?", "Docs query"),
    ("What's the SoC for RESS2 and how are SoC limits defined?", "Hybrid query"),
    ("Show me revenue for all batteries", "Data query"),
    ("Explain the AEMO bidding process", "Docs query"),
]

print("=" * 80)
print("Testing Routing Logic")
print("=" * 80)

for question, expected_type in test_questions:
    print(f"\n📝 Question: {question}")
    print(f"   Expected: {expected_type}")
    print("-" * 80)
    
    # Check routing
    data_can = data_agent.can_handle(question)
    docs_can = docs_agent.can_handle(question)
    is_hybrid = supervisor._is_hybrid_query(question)
    
    print(f"   Data Agent can handle: {data_can}")
    print(f"   Docs Agent can handle: {docs_can}")
    print(f"   Is hybrid query: {is_hybrid}")
    
    # Determine routing
    if is_hybrid or (data_can and docs_can):
        route = "Both agents (parallel)"
    elif data_can:
        route = "Data Agent"
    elif docs_can:
        route = "Docs Agent"
    else:
        route = "Default (Data Agent)"
    
    print(f"   → Routes to: {route}")

print("\n" + "=" * 80)
print("✅ Routing logic test complete!")
print("=" * 80)
print("\nNote: This test only checks routing logic.")
print("To test actual execution, use: python3 scripts/02_agent_supervisor.py")

