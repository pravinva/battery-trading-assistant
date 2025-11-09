#!/usr/bin/env python3
"""
Test query_genie with MCP implementation
"""

import os
import sys

# Set environment variables
os.environ["USE_GENIE_MCP"] = "true"
os.environ["GENIE_ROOM_ID"] = "01f0bca10415147a91fe3c98f80e596e"

# Import using importlib to handle module name with numbers
import importlib.util
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
agent_script_path = os.path.join(parent_dir, "scripts", "02_agent_development_local.py")

spec = importlib.util.spec_from_file_location("agent_dev", agent_script_path)
agent_dev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_dev)

# Get the query_genie tool function
query_genie = agent_dev.query_genie

print("=" * 80)
print("Testing query_genie with MCP")
print("=" * 80)
print(f"USE_GENIE_MCP: {os.environ.get('USE_GENIE_MCP')}")
print(f"GENIE_ROOM_ID: {os.environ.get('GENIE_ROOM_ID')}")
print()

# Test query
test_question = "What is the current SoC for RESS2?"
print(f"Question: {test_question}")
print()

try:
    result = query_genie.invoke({"question": test_question})
    print("✅ Success!")
    print()
    print("Response:")
    print("-" * 80)
    print(result)
    print("-" * 80)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

