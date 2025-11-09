#!/usr/bin/env python3
"""
Test query_genie tool via LangChain wrapper (like Streamlit does)
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
print("Testing query_genie tool via LangChain wrapper")
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
    
    # Get the query_genie tool (wrapped by @tool decorator)
    query_genie_tool = agent_dev.query_genie
    
    print(f"Tool type: {type(query_genie_tool)}")
    print(f"Tool name: {query_genie_tool.name}")
    print()
    
    # Test calling the tool via invoke (like LangChain does)
    print("=" * 80)
    print("Calling query_genie tool via invoke()")
    print("=" * 80)
    
    test_question = "What is the current SoC for RESS2?"
    print(f"Question: {test_question}")
    print()
    
    try:
        # Call via invoke like LangChain does
        result = query_genie_tool.invoke({"question": test_question})
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

except Exception as e:
    print(f"❌ Failed to load or test: {e}")
    import traceback
    traceback.print_exc()

