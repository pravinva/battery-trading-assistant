#!/usr/bin/env python3
"""
Test Genie Direct API end-to-end to verify it works like our code
"""

import os
import sys
from pathlib import Path

# Set environment variables
os.environ["USE_GENIE_MCP"] = "false"
os.environ["GENIE_ROOM_ID"] = "01f0bca10415147a91fe3c98f80e596e"

sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 80)
print("Testing Genie Direct API End-to-End")
print("=" * 80)

try:
    # Import agent module
    import importlib.util
    spec = importlib.util.spec_from_file_location("agent", "scripts/02_agent_development_local.py")
    agent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(agent)
    
    print("✅ Agent module loaded")
    print()
    
    # Test query_genie_via_direct_api
    question = "What is the current SoC for RESS2?"
    print(f"Question: {question}")
    print()
    
    print("Calling query_genie_via_direct_api...")
    result = agent.query_genie_via_direct_api(question, False)
    
    print()
    print("=" * 80)
    print("Result:")
    print("=" * 80)
    print(result)
    print()
    
    # Check if result contains actual data
    if "RESS" in result and ("62" in result or "82" in result or "SoC" in result):
        print("✅ SUCCESS: Result contains expected data")
    elif result == question:
        print("❌ FAILED: Result is just the question (not processed)")
    elif "Genie Error" in result or "did not process" in result:
        print("❌ FAILED: Genie error")
    else:
        print("⚠️  UNKNOWN: Result doesn't match expected pattern")
        print(f"   Result length: {len(result)}")
        print(f"   Result preview: {result[:200]}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

