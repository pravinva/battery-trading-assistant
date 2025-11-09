#!/usr/bin/env python3
"""
Test to reproduce the json scoping error by simulating exception scenarios
"""

import os
import sys
from pathlib import Path

# Set environment variables
os.environ["USE_GENIE_MCP"] = "true"
os.environ["GENIE_ROOM_ID"] = "01f0bca10415147a91fe3c98f80e596e"

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 80)
print("Testing json scoping in exception scenarios")
print("=" * 80)

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
    
    # Check json import
    print("Checking json import:")
    try:
        import json as json_module
        print(f"✅ json module imported: {type(json_module)}")
        print(f"✅ json.loads available: {hasattr(json_module, 'loads')}")
        print(f"✅ json.dumps available: {hasattr(json_module, 'dumps')}")
    except Exception as e:
        print(f"❌ Cannot import json: {e}")
    
    # Check if json is in agent_dev
    if hasattr(agent_dev, 'json'):
        print(f"✅ json in agent_dev: {type(agent_dev.json)}")
    else:
        print("⚠️  json not directly accessible via agent_dev.json")
    
    # Check JSONDecodeError import
    try:
        from json import JSONDecodeError
        print(f"✅ JSONDecodeError imported: {JSONDecodeError}")
    except Exception as e:
        print(f"❌ Cannot import JSONDecodeError: {e}")
    
    # Test accessing json in the function scope
    print()
    print("=" * 80)
    print("Testing json access in function scope")
    print("=" * 80)
    
    # Get the function code to inspect
    import inspect
    func_code = inspect.getsource(agent_dev.query_genie_via_mcp)
    
    # Check for json references
    json_refs = []
    for i, line in enumerate(func_code.split('\n'), 1):
        if 'json' in line.lower():
            json_refs.append((i, line.strip()))
    
    print(f"Found {len(json_refs)} lines referencing 'json':")
    for line_num, line in json_refs[:10]:  # Show first 10
        print(f"  Line {line_num}: {line}")
    
    # Try to call the function and catch any json-related errors
    print()
    print("=" * 80)
    print("Calling function to test json access")
    print("=" * 80)
    
    test_question = "What is the current SoC for RESS2?"
    try:
        result = agent_dev.query_genie_via_mcp(test_question, False)
        print("✅ Function call succeeded")
        print(f"Response length: {len(result)}")
    except UnboundLocalError as e:
        if 'json' in str(e):
            print(f"❌ UnboundLocalError for json: {e}")
            print()
            print("This indicates json is being treated as a local variable.")
            print("Checking for local json imports or assignments...")
            
            # Look for local json assignments
            for line_num, line in json_refs:
                if 'import json' in line or 'json =' in line:
                    print(f"  ⚠️  Found potential local json reference at line {line_num}: {line}")
        else:
            raise
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

except Exception as e:
    print(f"❌ Failed: {e}")
    import traceback
    traceback.print_exc()

