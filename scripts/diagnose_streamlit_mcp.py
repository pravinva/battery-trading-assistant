#!/usr/bin/env python3
"""
Diagnostic script to test MCP initialization in Streamlit-like context
"""

import os
import sys
from pathlib import Path

# Simulate Streamlit environment
os.environ["USE_GENIE_MCP"] = "true"
os.environ["GENIE_ROOM_ID"] = "01f0bca10415147a91fe3c98f80e596e"

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 80)
print("Diagnostic: Testing MCP in Streamlit-like Context")
print("=" * 80)
print()

try:
    import importlib.util
    
    # Clear modules like Streamlit does
    modules_to_remove = [k for k in sys.modules.keys() if 'agent' in k.lower() or '02_agent' in k.lower() or 'scripts' in k.lower()]
    for mod in modules_to_remove:
        if mod in sys.modules:
            del sys.modules[mod]
    
    import importlib
    importlib.invalidate_caches()
    
    print("✅ Cleared module cache")
    print()
    
    # Load agent module like Streamlit does
    agent_script_path = Path(__file__).parent.parent / "scripts" / "02_agent_development_local.py"
    spec = importlib.util.spec_from_file_location("agent_module", agent_script_path)
    agent_module = importlib.util.module_from_spec(spec)
    
    print("Loading agent module...")
    spec.loader.exec_module(agent_module)
    print("✅ Agent module loaded")
    print()
    
    # Check MCP client
    print("Checking MCP client initialization...")
    if hasattr(agent_module, '_mcp_client'):
        if agent_module._mcp_client:
            print("✅ MCP client is initialized")
            print(f"   MCP Server URL: {getattr(agent_module, '_mcp_server_url', 'N/A')}")
        else:
            print("❌ MCP client is None")
            print("   This means MCP initialization failed")
    else:
        print("❌ _mcp_client attribute not found")
    print()
    
    # Check USE_MCP flag
    if hasattr(agent_module, 'USE_MCP'):
        print(f"USE_MCP flag: {agent_module.USE_MCP}")
    else:
        print("❌ USE_MCP flag not found")
    print()
    
    # Check if query_genie tool exists
    if hasattr(agent_module, 'query_genie'):
        print("✅ query_genie tool found")
        tool = agent_module.query_genie
        print(f"   Tool type: {type(tool)}")
        print(f"   Tool name: {tool.name}")
    else:
        print("❌ query_genie tool not found")
    print()
    
    # Try to invoke the tool
    print("=" * 80)
    print("Testing query_genie tool invocation...")
    print("=" * 80)
    
    test_question = "What is the current SoC for RESS2?"
    print(f"Question: {test_question}")
    print()
    
    try:
        result = tool.invoke({"question": test_question})
        print("✅ Tool invocation succeeded!")
        print()
        print("Response preview:")
        print("-" * 80)
        print(result[:500])
        print("-" * 80)
    except Exception as e:
        print(f"❌ Tool invocation failed: {e}")
        import traceback
        print()
        print("Full traceback:")
        print("-" * 80)
        traceback.print_exc()
        print("-" * 80)
        
        # Check what error type it is
        error_str = str(e).lower()
        if "broken pipe" in error_str or "errno 32" in error_str:
            print()
            print("🔍 This is a network connection error (broken pipe)")
            print("   Possible causes:")
            print("   - Network interruption")
            print("   - MCP server connection timeout")
            print("   - Databricks workspace connectivity issue")
        elif "json" in error_str and ("local variable" in error_str or "not defined" in error_str):
            print()
            print("🔍 This is a JSON scoping error")
            print("   The module needs to be reloaded")
        elif "mcp" in error_str or "client" in error_str:
            print()
            print("🔍 This is an MCP client initialization error")
            print("   Check:")
            print("   - databricks-mcp is installed: pip install databricks-mcp")
            print("   - MCP server is enabled in workspace")
            print("   - GENIE_ROOM_ID is correct")
    
    print()
    print("=" * 80)
    print("Diagnostic Complete")
    print("=" * 80)

except Exception as e:
    print(f"❌ Diagnostic failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

