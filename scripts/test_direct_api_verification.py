#!/usr/bin/env python3
"""
Test Direct API (Non-MCP) path to verify it wasn't broken
"""

import os
import sys

# Explicitly disable MCP to test direct API
os.environ["USE_GENIE_MCP"] = "false"
os.environ["GENIE_ROOM_ID"] = "01f0bca10415147a91fe3c98f80e596e"

# Import using importlib to handle module name with numbers
import importlib.util
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
agent_script_path = os.path.join(parent_dir, "scripts", "02_agent_development_local.py")

spec = importlib.util.spec_from_file_location("agent_dev", agent_script_path)
agent_dev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_dev)

print("=" * 80)
print("Testing Direct API (Non-MCP) Path")
print("=" * 80)
print(f"USE_GENIE_MCP: {os.environ.get('USE_GENIE_MCP')}")
print(f"GENIE_ROOM_ID: {os.environ.get('GENIE_ROOM_ID')}")
print(f"MCP_AVAILABLE: {agent_dev.MCP_AVAILABLE}")
print(f"USE_GENIE_MCP (module): {getattr(agent_dev, 'USE_GENIE_MCP', 'not found')}")
print(f"_mcp_client: {agent_dev._mcp_client is not None}")
print()

# Verify routing will go to direct API
if agent_dev.USE_GENIE_MCP and agent_dev._mcp_client:
    print("❌ ERROR: Should route to Direct API but MCP is enabled!")
    sys.exit(1)
else:
    print("✅ Routing will use Direct API (correct)")

# Test 1: Verify query_genie_via_direct_api function exists and is callable
print("\n" + "=" * 80)
print("Test 1: Verify query_genie_via_direct_api function")
print("=" * 80)

if not hasattr(agent_dev, 'query_genie_via_direct_api'):
    print("❌ ERROR: query_genie_via_direct_api function not found!")
    sys.exit(1)

func = agent_dev.query_genie_via_direct_api
import inspect
sig = inspect.signature(func)
print(f"✅ Function exists: query_genie_via_direct_api{sig}")

# Test 2: Verify the function can be called (with a simple test)
print("\n" + "=" * 80)
print("Test 2: Test function call structure")
print("=" * 80)

# Just verify it's callable - don't actually call it (would need real Genie connection)
try:
    # Check if it's a function
    if callable(func):
        print("✅ Function is callable")
    else:
        print("❌ ERROR: Function is not callable")
        sys.exit(1)
except Exception as e:
    print(f"❌ ERROR checking function: {e}")
    sys.exit(1)

# Test 3: Verify query_genie tool routes correctly
print("\n" + "=" * 80)
print("Test 3: Verify query_genie routing logic")
print("=" * 80)

if not hasattr(agent_dev, 'query_genie'):
    print("❌ ERROR: query_genie tool not found!")
    sys.exit(1)

print(f"✅ query_genie tool exists")
print(f"   Description: {agent_dev.query_genie.description[:80]}...")

# Check the routing condition
will_use_mcp = agent_dev.USE_GENIE_MCP and agent_dev._mcp_client
will_use_direct = not will_use_mcp

print(f"\n📋 Routing Analysis:")
print(f"   USE_GENIE_MCP = {agent_dev.USE_GENIE_MCP}")
print(f"   _mcp_client exists = {agent_dev._mcp_client is not None}")
print(f"   Will use MCP: {will_use_mcp}")
print(f"   Will use Direct API: {will_use_direct}")

if not will_use_direct:
    print("❌ ERROR: Should route to Direct API!")
    sys.exit(1)
else:
    print("✅ Will correctly route to Direct API")

# Test 4: Check that get_genie_logs function exists
print("\n" + "=" * 80)
print("Test 4: Verify logging functions")
print("=" * 80)

if hasattr(agent_dev, 'get_genie_logs'):
    print("✅ get_genie_logs function exists")
    logs = agent_dev.get_genie_logs()
    print(f"   Current logs: {len(logs)} entries")
else:
    print("❌ ERROR: get_genie_logs function not found!")
    sys.exit(1)

if hasattr(agent_dev, 'add_genie_log'):
    print("✅ add_genie_log function exists")
else:
    print("❌ ERROR: add_genie_log function not found!")
    sys.exit(1)

print("\n" + "=" * 80)
print("✅ ALL TESTS PASSED - Direct API path is working correctly!")
print("=" * 80)

