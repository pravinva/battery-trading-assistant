#!/usr/bin/env python3
"""Test script to verify Genie API logging works"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Set environment
os.environ['GENIE_ROOM_ID'] = '01f0bca10415147a91fe3c98f80e596e'

# Import and test
print("Testing query_genie function...")
print(f"GENIE_ROOM_ID: {os.environ.get('GENIE_ROOM_ID')}")

# Import the module dynamically (to avoid module name issues)
import importlib.util
agent_script_path = Path(__file__).parent.parent / "scripts" / "02_agent_development_local.py"
spec = importlib.util.spec_from_file_location("agent_module", agent_script_path)
agent_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_module)

query_genie = agent_module.query_genie

# Test with a simple question
print("\nCalling query_genie...")
try:
    result = query_genie("What is the current SoC for RESS2?")
    print(f"\nResult (first 500 chars):\n{result[:500]}")
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()

# Check debug log
debug_log = "/tmp/genie_debug.log"
if os.path.exists(debug_log):
    print(f"\n{'='*80}")
    print(f"Debug log contents ({os.path.getsize(debug_log)} bytes):")
    print(f"{'='*80}")
    with open(debug_log, "r") as f:
        print(f.read())
else:
    print(f"\nDebug log not found at {debug_log}")

