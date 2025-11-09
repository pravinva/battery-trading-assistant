#!/usr/bin/env python3
"""
Test script to discover Genie MCP server tools and capabilities
Run this to understand what tools the Genie MCP server exposes
"""

import os
from databricks.sdk import WorkspaceClient

# Try to import MCP client
# Based on: https://docs.databricks.com/aws/en/generative-ai/mcp/managed-mcp
try:
    from databricks_mcp import DatabricksMCPClient
    MCP_AVAILABLE = True
except ImportError:
    print("❌ databricks-mcp not installed")
    print("Install with: pip install databricks-mcp")
    exit(1)

# Configuration
GENIE_ROOM_ID = os.environ.get("GENIE_ROOM_ID", "01f0bca10415147a91fe3c98f80e596e")
GENIE_MCP_SERVER_URL = os.environ.get("GENIE_MCP_SERVER_URL", None)

print("=" * 80)
print("Genie MCP Server Tool Discovery")
print("=" * 80)
print(f"Genie Room ID: {GENIE_ROOM_ID}")
print(f"MCP Server URL: {GENIE_MCP_SERVER_URL or 'Using default managed server'}")
print()

# Initialize workspace client
w = WorkspaceClient()

# Initialize workspace client for authentication
w = WorkspaceClient()
workspace_hostname = w.config.host

# Build Genie MCP server URL
# Pattern: https://<workspace-hostname>/api/2.0/mcp/genie/{genie_space_id}
if GENIE_MCP_SERVER_URL:
    mcp_server_url = GENIE_MCP_SERVER_URL
else:
    mcp_server_url = f"{workspace_hostname}/api/2.0/mcp/genie/{GENIE_ROOM_ID}"

print(f"MCP Server URL: {mcp_server_url}")

# Initialize MCP client
# Based on docs: DatabricksMCPClient(server_url=..., workspace_client=...)
try:
    mcp_client = DatabricksMCPClient(server_url=mcp_server_url, workspace_client=w)
    print("✅ MCP client initialized")
except Exception as e:
    print(f"❌ Failed to initialize MCP client: {e}")
    print("\nTroubleshooting:")
    print("1. Verify MCP server is enabled in workspace (Agents → MCP Servers)")
    print("2. Check if Genie MCP server is listed")
    print("3. Verify Unity Catalog permissions")
    print("4. Ensure Genie space ID is correct")
    exit(1)

# Discover available tools
# Based on docs: mcp_client.list_tools() returns list of Tool objects
print("\n" + "=" * 80)
print("Discovering Available Tools")
print("=" * 80)

try:
    tools = mcp_client.list_tools()
    print(f"✅ Found {len(tools)} tools:")
    print()
    for tool in tools:
        print(f"Tool: {tool.name}")
        print(f"  Description: {tool.description}")
        print(f"  Input Schema: {tool.inputSchema}")
        print()
except Exception as e:
    print(f"❌ Error discovering tools: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test a query using the discovered tools
print("\n" + "=" * 80)
print("Testing Genie Query via MCP")
print("=" * 80)

test_question = "What tables are available in the database?"

if not tools:
    print("⚠️  No tools found to test")
else:
    # Use the first tool (or find the query tool)
    genie_tool = None
    for tool in tools:
        if "query" in tool.name.lower() or "genie" in tool.name.lower():
            genie_tool = tool
            break
    
    if not genie_tool:
        genie_tool = tools[0]  # Use first tool
    
    print(f"Using tool: {genie_tool.name}")
    print(f"Question: {test_question}")
    
    # Determine correct argument name from tool schema
    schema = genie_tool.inputSchema
    properties = schema.get("properties", {})
    
    tool_args = {}
    # Common parameter names: "question", "content", "query", "text"
    for param_name in ["question", "content", "query", "text"]:
        if param_name in properties:
            tool_args[param_name] = test_question
            break
    
    # If no standard parameter found, try with "question" anyway
    if not tool_args:
        tool_args["question"] = test_question
    
    print(f"Tool arguments: {tool_args}")
    
    try:
        result = mcp_client.call_tool(genie_tool.name, tool_args)
        print(f"\n✅ Success!")
        print(f"Result type: {type(result)}")
        
        # Extract content from ToolResult
        if hasattr(result, 'content'):
            content = result.content
            print(f"Result content type: {type(content)}")
            print(f"Result content preview:\n{str(content)[:500]}...")
        else:
            print(f"Result preview:\n{str(result)[:500]}...")
            
    except Exception as e:
        print(f"\n❌ Error calling tool: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 80)
print("Discovery Complete")
print("=" * 80)

