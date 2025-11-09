#!/usr/bin/env python3
"""
Test query_genie locally to debug the status error - call the underlying function
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the actual function from the module
import importlib.util
spec = importlib.util.spec_from_file_location(
    "agent_dev", 
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts", "02_agent_development_local.py")
)
agent_dev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_dev)

# Get the actual function, not the tool wrapper
# The function is defined as query_genie, but it's wrapped in @tool decorator
# We need to access the underlying function
import inspect

# Find the actual function
query_genie_func = None
for name, obj in inspect.getmembers(agent_dev):
    if name == 'query_genie' and inspect.isfunction(obj):
        query_genie_func = obj
        break

if not query_genie_func:
    # Try to get it from the tool
    if hasattr(agent_dev.query_genie, 'func'):
        query_genie_func = agent_dev.query_genie.func
    elif hasattr(agent_dev.query_genie, '_func'):
        query_genie_func = agent_dev.query_genie._func

print("=" * 80)
print("Testing query_genie Locally")
print("=" * 80)

# Test question
question = "What is the current SoC for RESS2?"

print(f"\nQuestion: {question}")
print(f"GENIE_ROOM_ID: {os.environ.get('GENIE_ROOM_ID', 'NOT SET')}")

if not query_genie_func:
    print("\n✗ Could not find query_genie function")
    print(f"Available attributes: {[x for x in dir(agent_dev) if 'query' in x.lower()]}")
    sys.exit(1)

try:
    print("\nCalling query_genie function...")
    response = query_genie_func(question)
    print(f"\n✓ Success!")
    print(f"Response length: {len(response)} characters")
    print(f"Response preview: {response[:200]}...")
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("Test Complete")
print("=" * 80)
