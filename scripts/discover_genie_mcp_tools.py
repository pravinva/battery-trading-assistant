#!/usr/bin/env python3
"""
Test script to discover Genie MCP server tools and capabilities
Run this to understand what tools the Genie MCP server exposes
"""

import os
from databricks.sdk import WorkspaceClient

# Try to import MCP client
try:
    from databricks.langchain.mcp import DatabricksMCPClient
    MCP_AVAILABLE = True
except ImportError:
    print("❌ databricks-langchain not installed")
    print("Install with: pip install databricks-langchain")
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

# Initialize MCP client
try:
    if GENIE_MCP_SERVER_URL:
        mcp_client = DatabricksMCPClient(server_url=GENIE_MCP_SERVER_URL)
    else:
        # Try to use default managed Genie MCP server
        mcp_client = DatabricksMCPClient()
    print("✅ MCP client initialized")
except Exception as e:
    print(f"❌ Failed to initialize MCP client: {e}")
    print("\nTroubleshooting:")
    print("1. Verify MCP server is enabled in workspace (Agents → MCP Servers)")
    print("2. Check if Genie MCP server is listed")
    print("3. Verify Unity Catalog permissions")
    exit(1)

# Try to discover available tools
print("\n" + "=" * 80)
print("Discovering Available Tools")
print("=" * 80)

try:
    # Try to list tools/resources
    if hasattr(mcp_client, 'list_tools'):
        tools = mcp_client.list_tools()
        print(f"Found {len(tools) if tools else 0} tools:")
        for tool in tools or []:
            print(f"  - {tool}")
    elif hasattr(mcp_client, 'tools'):
        tools = mcp_client.tools
        print(f"Found {len(tools) if tools else 0} tools:")
        for tool in tools or []:
            print(f"  - {tool}")
    else:
        print("⚠️  Could not discover tools automatically")
        print("Available MCP client methods:")
        methods = [m for m in dir(mcp_client) if not m.startswith('_')]
        for method in methods:
            print(f"  - {method}")
except Exception as e:
    print(f"⚠️  Error discovering tools: {e}")
    print("\nTrying alternative approach...")
    # Try to inspect the client object
    print("\nMCP Client attributes:")
    attrs = [attr for attr in dir(mcp_client) if not attr.startswith('_')]
    for attr in attrs[:20]:  # Show first 20
        print(f"  - {attr}")

# Try to test a query
print("\n" + "=" * 80)
print("Testing Genie Query via MCP")
print("=" * 80)

test_question = "What tables are available in the database?"

# Try different possible tool names
possible_tool_names = [
    "query_genie_space",
    "genie_query",
    "query_genie",
    "genie_space_query",
    "query",
]

for tool_name in possible_tool_names:
    print(f"\nTrying tool: {tool_name}")
    try:
        result = mcp_client.call_tool(
            tool_name=tool_name,
            arguments={
                "space_id": GENIE_ROOM_ID,
                "question": test_question
            }
        )
        print(f"✅ Success with {tool_name}!")
        print(f"Result type: {type(result)}")
        print(f"Result preview: {str(result)[:200]}...")
        break
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        continue
else:
    print("\n⚠️  None of the common tool names worked")
    print("You may need to:")
    print("1. Check MCP server documentation")
    print("2. Inspect MCP server configuration in workspace")
    print("3. Use MCP server's tool discovery API")

print("\n" + "=" * 80)
print("Discovery Complete")
print("=" * 80)

