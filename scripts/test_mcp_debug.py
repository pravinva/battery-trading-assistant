#!/usr/bin/env python3
"""
Debug script to test MCP query_genie_via_mcp function locally
"""

import os
import sys
from pathlib import Path

# Set environment variables
os.environ["USE_GENIE_MCP"] = "true"
os.environ["GENIE_ROOM_ID"] = "01f0bca10415147a91fe3c98f80e596e"
os.environ["DEBUG"] = "true"

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 80)
print("Testing query_genie_via_mcp locally")
print("=" * 80)
print(f"USE_GENIE_MCP: {os.environ.get('USE_GENIE_MCP')}")
print(f"GENIE_ROOM_ID: {os.environ.get('GENIE_ROOM_ID')}")
print()

try:
    # Import using importlib to handle module name with numbers
    import importlib.util
    agent_script_path = Path(__file__).parent.parent / "scripts" / "02_agent_development_local.py"
    
    spec = importlib.util.spec_from_file_location("agent_dev", agent_script_path)
    agent_dev = importlib.util.module_from_spec(spec)
    
    print("Loading agent module...")
    spec.loader.exec_module(agent_dev)
    print("✅ Agent module loaded")
    print()
    
    # Check if json is imported
    if hasattr(agent_dev, 'json'):
        print(f"✅ json module found in agent_dev: {type(agent_dev.json)}")
    else:
        print("❌ json module not found in agent_dev")
    
    # Check if query_genie_via_mcp exists
    if hasattr(agent_dev, 'query_genie_via_mcp'):
        print("✅ query_genie_via_mcp function found")
    else:
        print("❌ query_genie_via_mcp function not found")
        sys.exit(1)
    
    # Test calling the function
    print()
    print("=" * 80)
    print("Calling query_genie_via_mcp")
    print("=" * 80)
    
    test_question = "What is the current SoC for RESS2?"
    print(f"Question: {test_question}")
    print()
    
    try:
        result = agent_dev.query_genie_via_mcp(test_question, False)
        print("✅ Success!")
        print()
        print("Response:")
        print("-" * 80)
        print(result[:500])
        print("-" * 80)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print()
        print("Full traceback:")
        print("-" * 80)
        traceback.print_exc()
        print("-" * 80)
        
        # Check if json is accessible
        print()
        print("Debugging json access:")
        try:
            import json
            print(f"✅ json imported in test script: {type(json)}")
        except Exception as je:
            print(f"❌ Cannot import json: {je}")
        
        try:
            json_test = agent_dev.json
            print(f"✅ json accessible via agent_dev.json: {type(json_test)}")
        except AttributeError:
            print("❌ json not accessible via agent_dev.json")
        except Exception as je:
            print(f"❌ Error accessing agent_dev.json: {je}")

except Exception as e:
    print(f"❌ Failed to load or test: {e}")
    import traceback
    traceback.print_exc()

