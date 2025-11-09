#!/usr/bin/env python3
"""
Local test script for Genie MCP integration
Tests query_genie_via_mcp function with various scenarios
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
print("Local Test: Genie MCP Integration")
print("=" * 80)
print(f"USE_GENIE_MCP: {os.environ.get('USE_GENIE_MCP')}")
print(f"GENIE_ROOM_ID: {os.environ.get('GENIE_ROOM_ID')}")
print(f"DEBUG: {os.environ.get('DEBUG')}")
print()

try:
    # Import using importlib to handle module name with numbers
    import importlib.util
    agent_script_path = Path(__file__).parent.parent / "scripts" / "02_agent_development_local.py"
    
    if not agent_script_path.exists():
        print(f"❌ Agent script not found at {agent_script_path}")
        sys.exit(1)
    
    spec = importlib.util.spec_from_file_location("agent_dev", agent_script_path)
    agent_dev = importlib.util.module_from_spec(spec)
    
    print("Loading agent module...")
    spec.loader.exec_module(agent_dev)
    print("✅ Agent module loaded")
    print()
    
    # Test 1: Check MCP client initialization
    print("=" * 80)
    print("Test 1: MCP Client Initialization")
    print("=" * 80)
    if hasattr(agent_dev, '_mcp_client') and agent_dev._mcp_client:
        print("✅ MCP client initialized")
        print(f"   MCP Server URL: {getattr(agent_dev, '_mcp_server_url', 'N/A')}")
    else:
        print("❌ MCP client not initialized")
        print("   This might be expected if USE_GENIE_MCP=false")
    print()
    
    # Test 2: Check json_module import
    print("=" * 80)
    print("Test 2: JSON Module Import")
    print("=" * 80)
    try:
        import json
        print(f"✅ json module available: {type(json)}")
        
        # Check if query_genie_via_mcp has json_module
        import inspect
        source = inspect.getsource(agent_dev.query_genie_via_mcp)
        if "import json as json_module" in source:
            print("✅ query_genie_via_mcp imports json_module")
        else:
            print("⚠️  query_genie_via_mcp does not import json_module")
    except Exception as e:
        print(f"❌ Error checking json: {e}")
    print()
    
    # Test 3: Test query_genie_via_mcp function directly
    print("=" * 80)
    print("Test 3: Direct Function Call")
    print("=" * 80)
    test_question = "What is the current SoC for RESS2?"
    print(f"Question: {test_question}")
    print()
    
    try:
        result = agent_dev.query_genie_via_mcp(test_question, False)
        print("✅ Function call succeeded!")
        print()
        print("Response preview:")
        print("-" * 80)
        print(result[:500])
        print("-" * 80)
        print()
        print(f"Full response length: {len(result)} characters")
    except Exception as e:
        print(f"❌ Function call failed: {e}")
        import traceback
        print()
        print("Full traceback:")
        print("-" * 80)
        traceback.print_exc()
        print("-" * 80)
    print()
    
    # Test 4: Test via LangChain tool wrapper (like Streamlit does)
    print("=" * 80)
    print("Test 4: LangChain Tool Wrapper")
    print("=" * 80)
    if hasattr(agent_dev, 'query_genie'):
        query_genie_tool = agent_dev.query_genie
        print(f"Tool type: {type(query_genie_tool)}")
        print(f"Tool name: {query_genie_tool.name}")
        print()
        
        test_question2 = "Show me revenue for all batteries in the last 12 hours"
        print(f"Question: {test_question2}")
        print()
        
        try:
            result = query_genie_tool.invoke({"question": test_question2})
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
    else:
        print("❌ query_genie tool not found")
    print()
    
    # Test 5: Check error handling for network errors
    print("=" * 80)
    print("Test 5: Error Handling")
    print("=" * 80)
    import inspect
    source = inspect.getsource(agent_dev.query_genie_via_mcp)
    
    error_checks = [
        ("broken pipe", "broken pipe" in source.lower()),
        ("errno 32", "errno 32" in source.lower()),
        ("ConnectionError", "ConnectionError" in source),
        ("OSError", "OSError" in source),
        ("json scoping", "json" in source.lower() and "json_module" in source),
    ]
    
    print("Error handling checks:")
    for check_name, passed in error_checks:
        status = "✅" if passed else "❌"
        print(f"  {status} {check_name}")
    print()
    
    # Test 6: Check genie logs
    print("=" * 80)
    print("Test 6: Genie Logs")
    print("=" * 80)
    if hasattr(agent_dev, 'get_genie_logs'):
        logs = agent_dev.get_genie_logs()
        if logs:
            print(f"✅ Found {len(logs)} log entries:")
            print()
            # Show all logs, not just last 5
            for i, log in enumerate(logs, 1):
                print(f"   {i}. {log}")
            print()
            print("📋 These logs show the MCP execution flow:")
            print("   - Tool discovery")
            print("   - Tool calls")
            print("   - Success/failure status")
        else:
            print("ℹ️  No logs yet (logs are cleared after reading)")
            print("   Run a query first to generate logs")
    else:
        print("❌ get_genie_logs function not found")
    print()
    
    print("=" * 80)
    print("Test Complete")
    print("=" * 80)
    print()
    print("💡 Tip: Logs are also displayed in Streamlit UI under:")
    print("   '💾 SQL Query Results' → '📋 Execution Logs (MCP vs Direct API)'")

except Exception as e:
    print(f"❌ Failed to run tests: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

