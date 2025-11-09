# How Your Agent Can Talk to Genie via MCP Server

Based on the [Databricks AI Bridge](https://github.com/databricks/databricks-ai-bridge) and [MCP documentation](https://docs.databricks.com/aws/en/generative-ai/mcp/), here's how your agent can interact with Genie through MCP servers.

## Current Architecture vs MCP Architecture

### Current (Direct API)
```
Your Agent (LangGraph)
    ↓
query_genie tool
    ↓
Direct Genie API (genie.start_conversation)
    ↓
Manual polling & status checking
    ↓
Extract attachments & results
    ↓
Format response
```

### MCP Architecture
```
Your Agent (LangGraph)
    ↓
MCP Client (databricks-langchain)
    ↓
Genie MCP Server (Managed by Databricks)
    ↓
Genie Space (battery-trading-agent)
    ↓
SQL Execution & Results
    ↓
Standardized MCP Response
```

## Key Benefits

1. **Standardization**: MCP is an open protocol - your tools work with any MCP-compatible agent
2. **Simplified Code**: No need to handle Genie API polling, status checks, attachment extraction
3. **Multi-Agent Support**: Can use Multi-Agent Supervisor to coordinate multiple Genie Spaces
4. **Tool Discovery**: MCP servers expose tools dynamically - no hardcoding
5. **Unified Auth**: Uses Unity Catalog connections for secure access

## How It Works

### 1. Genie MCP Server (Managed)

Databricks provides a **managed MCP server** for Genie Spaces. This server:
- Exposes Genie Spaces as MCP resources
- Handles authentication via Unity Catalog
- Manages connections and polling automatically
- Provides standardized tool interface

### 2. MCP Client Integration

The `databricks-langchain` package provides MCP client integration:

```python
from databricks.langchain.mcp import DatabricksMCPClient

# MCP client connects to managed Genie MCP server
mcp_client = DatabricksMCPClient(
    # Server URL/connection handled automatically for managed servers
    # Authentication via Unity Catalog
)
```

### 3. Tool Invocation

Instead of calling Genie API directly, you call MCP tools:

```python
# Current approach (direct API)
genie = w.genie
conversation_wait = genie.start_conversation(GENIE_ROOM_ID, question)
# ... manual polling, status checking, attachment extraction ...

# MCP approach (simplified)
result = mcp_client.call_tool(
    tool_name="query_genie_space",  # Tool exposed by Genie MCP server
    arguments={
        "space_id": GENIE_ROOM_ID,
        "question": question
    }
)
# Result is already formatted - no manual extraction needed
```

## Implementation Approach

### Option 1: Replace Direct API with MCP Tool

Replace your `query_genie` tool with an MCP-based version:

```python
from databricks.langchain.mcp import DatabricksMCPClient
from langchain_core.tools import tool

@tool
def query_genie_mcp(
    question: Annotated[str, "Natural language question about battery data"]
) -> str:
    """Query Genie via MCP server - simplified, standardized approach"""
    
    # Get MCP client (cached)
    mcp_client = get_mcp_client()
    
    # Call Genie through MCP
    result = mcp_client.call_tool(
        tool_name="genie_query",  # Actual name depends on MCP server
        arguments={
            "space_id": GENIE_ROOM_ID,
            "question": question
        }
    )
    
    # MCP server handles:
    # - Starting conversation
    # - Polling for completion
    # - Extracting results
    # - Formatting response
    
    return result
```

### Option 2: Multi-Agent Supervisor Pattern

Use Multi-Agent Supervisor to coordinate Genie with other agents:

```python
from databricks.agent_bricks import MultiAgentSupervisor

# Create supervisor with multiple agents
supervisor = MultiAgentSupervisor(
    agents=[
        {
            "name": "battery_genie",
            "type": "genie_space",
            "space_id": GENIE_ROOM_ID,
            "description": "Battery trading data queries"
        },
        {
            "name": "docs_search", 
            "type": "vector_search",
            "index": INDEX_NAME,
            "description": "Technical documentation"
        }
    ],
    instructions="Route data queries to battery_genie, documentation questions to docs_search"
)

# Supervisor automatically routes queries
response = supervisor.query(user_question)
```

## What You Need to Do

### Step 1: Install Dependencies

```bash
pip install databricks-langchain
# Or from source:
pip install git+https://github.com/databricks/databricks-ai-bridge.git#subdirectory=integrations/langchain
```

### Step 2: Verify MCP Server Availability

1. Go to your Databricks workspace
2. Navigate to **Agents** → **MCP Servers**
3. Look for "Genie Spaces" or "Genie" MCP server
4. Verify it's enabled and configured

### Step 3: Understand MCP Server API

The Genie MCP server exposes tools/resources. You need to discover:
- **Tool names**: What tools are available? (e.g., `query_genie_space`, `genie_query`)
- **Tool signatures**: What arguments do they accept?
- **Response format**: How are results returned?
- **Chart support**: Can charts be created via MCP?

### Step 4: Create MCP-Based Tool

Replace your current `query_genie` implementation with MCP-based version.

### Step 5: Handle Chart Creation

MCP server may not directly support chart creation. Options:
- **Post-process**: Extract query results from MCP response, create charts locally
- **Hybrid**: Use MCP for queries, direct API for charts
- **Check capabilities**: See if MCP server exposes chart tools

## Key Differences

| Aspect | Direct API | MCP Server |
|--------|------------|------------|
| **Code Complexity** | ~800 lines (polling, extraction) | ~50 lines (simple tool call) |
| **Status Polling** | Manual implementation | Handled by MCP server |
| **Error Handling** | Custom exceptions | Standardized MCP errors |
| **Authentication** | WorkspaceClient | Unity Catalog connections |
| **Multi-Agent** | Manual coordination | Built-in supervisor |
| **Tool Discovery** | Hardcoded | Dynamic via MCP |

## Research Needed

Before implementing, you need to:

1. **Check MCP Server Documentation**
   - What tools does Genie MCP server expose?
   - What are the tool signatures?
   - How are results formatted?

2. **Test MCP Connection**
   - Can you connect to Genie MCP server?
   - What authentication is required?
   - Are there any connection issues?

3. **Verify Feature Parity**
   - Does MCP support chart creation?
   - Can it handle complex queries?
   - Is conversation context maintained?

4. **Performance Testing**
   - Is MCP faster/slower than direct API?
   - What's the latency overhead?
   - Are there connection pooling benefits?

## Next Steps

1. **Review Databricks AI Bridge Repository**
   - Check `integrations/langchain` directory
   - Look for MCP client examples
   - Understand API structure

2. **Check Workspace MCP Servers**
   - Verify Genie MCP server is available
   - Check configuration options
   - Review available tools/resources

3. **Create Proof of Concept**
   - Simple MCP tool that queries Genie
   - Test basic functionality
   - Compare with current implementation

4. **Decide on Approach**
   - Direct MCP tool replacement?
   - Multi-Agent Supervisor?
   - Hybrid approach?

## Resources

- [Databricks AI Bridge GitHub](https://github.com/databricks/databricks-ai-bridge)
- [MCP on Databricks Docs](https://docs.databricks.com/aws/en/generative-ai/mcp/)
- [Multi-Agent Supervisor Guide](https://docs.databricks.com/aws/en/generative-ai/agent-bricks/multi-agent-supervisor)
- [LangChain MCP Integration](https://github.com/databricks/databricks-ai-bridge/tree/main/integrations/langchain)

## Questions to Answer

1. What exact tools does the Genie MCP server expose?
2. How do you initialize the MCP client for Genie?
3. What's the response format from MCP tools?
4. Does MCP support chart creation or do we need post-processing?
5. How does conversation context work with MCP?
6. What's the performance comparison?

These questions need to be answered by:
- Reviewing the databricks-ai-bridge repository code
- Testing MCP server connection in your workspace
- Checking Databricks documentation for Genie MCP specifics

