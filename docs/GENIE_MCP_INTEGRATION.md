# Genie MCP Server Integration Guide

This document explains how to migrate from direct Genie API calls to using the Genie MCP (Model Context Protocol) server.

## Overview

### Current Implementation (Direct API)
- Uses `genie.start_conversation()` directly
- Manual polling and status checking
- Direct attachment extraction
- Custom error handling

### MCP Server Approach
- Uses Databricks managed MCP server for Genie Spaces
- Standardized MCP protocol for tool communication
- Built-in connection management and authentication
- Can be used with Multi-Agent Supervisor pattern

## Benefits of MCP Server

1. **Standardization**: MCP is an open standard - tools work with any agent
2. **Simplified Integration**: No need to handle Genie API details directly
3. **Multi-Agent Support**: Can coordinate multiple Genie Spaces via Multi-Agent Supervisor
4. **Better Tool Management**: Tools are exposed as MCP resources
5. **Unified Authentication**: Uses Unity Catalog connections

## Architecture Comparison

### Current Architecture
```
Agent → query_genie tool → Direct Genie API → Genie Space → SQL → Results
```

### MCP Architecture
```
Agent → MCP Client → Genie MCP Server → Genie Space → SQL → Results
```

## Setup Steps

### 1. Install Databricks AI Bridge

```bash
# For LangChain/LangGraph (recommended)
pip install databricks-langchain

# Or install from source
pip install git+https://github.com/databricks/databricks-ai-bridge.git#subdirectory=integrations/langchain
```

### 2. Enable Genie MCP Server

The Genie MCP server is a **managed MCP server** provided by Databricks. To use it:

1. Go to your Databricks workspace
2. Navigate to **Agents** → **MCP Servers**
3. The Genie MCP server should be available as a managed server
4. Configure it to connect to your Genie Space (`battery-trading-agent`)

### 3. Configure MCP Connection

The Genie MCP server exposes Genie Spaces as MCP resources. You'll need to:

1. **Set up Unity Catalog Connection** (if using external MCP):
   ```python
   # MCP servers use Unity Catalog connections for authentication
   # This is handled automatically for managed servers
   ```

2. **Configure Genie Space Access**:
   - Ensure your agent has access to the Genie Space
   - The MCP server will use Unity Catalog permissions

### 4. Modify Agent to Use MCP

Instead of direct API calls, use MCP client:

```python
from databricks.langchain.mcp import DatabricksMCPClient
from langchain_core.tools import StructuredTool

# Initialize MCP client
mcp_client = DatabricksMCPClient(
    server_url="<mcp-server-url>",  # Managed server URL
    # Authentication handled automatically via Unity Catalog
)

# Create MCP tool wrapper
def query_genie_mcp(question: str) -> str:
    """Query Genie via MCP server"""
    # Use MCP client to call Genie Space
    result = mcp_client.call_tool(
        tool_name="genie_query",  # Tool name exposed by Genie MCP server
        arguments={"question": question, "space_id": GENIE_ROOM_ID}
    )
    return result
```

## Integration Approaches

### Approach 1: Direct MCP Tool (Recommended)

Replace `query_genie` tool with MCP-based tool:

```python
from databricks.langchain.mcp import DatabricksMCPClient

# Initialize MCP client (cached)
@st.cache_resource
def get_mcp_client():
    return DatabricksMCPClient(
        server_url=os.environ.get("GENIE_MCP_SERVER_URL"),
        # Authentication via Unity Catalog
    )

@tool
def query_genie_mcp(
    question: Annotated[str, "A natural language question about battery data"]
) -> str:
    """Query Databricks Genie via MCP server"""
    mcp_client = get_mcp_client()
    
    # Call Genie through MCP
    result = mcp_client.call_tool(
        tool_name="query_genie_space",
        arguments={
            "space_id": GENIE_ROOM_ID,
            "question": question
        }
    )
    
    return result
```

### Approach 2: Multi-Agent Supervisor Pattern

Use Multi-Agent Supervisor to coordinate multiple agents:

```python
from databricks.agent_bricks import MultiAgentSupervisor

# Create supervisor
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
            "description": "Technical documentation search"
        }
    ]
)

# Supervisor automatically routes queries to appropriate agent
response = supervisor.query(user_question)
```

## Key Differences

| Aspect | Direct API | MCP Server |
|--------|------------|------------|
| **API Calls** | Manual `genie.start_conversation()`, polling | MCP client handles communication |
| **Status Polling** | Custom polling logic | Handled by MCP server |
| **Error Handling** | Custom exception handling | Standardized MCP error responses |
| **Authentication** | WorkspaceClient credentials | Unity Catalog connections |
| **Multi-Agent** | Manual coordination | Built-in supervisor support |
| **Tool Discovery** | Hardcoded tools | Dynamic tool discovery via MCP |

## Migration Checklist

- [ ] Install `databricks-langchain` package
- [ ] Enable Genie MCP server in workspace
- [ ] Configure Genie Space access for MCP server
- [ ] Replace `query_genie` tool with MCP-based tool
- [ ] Update error handling for MCP responses
- [ ] Test chart creation with MCP (if supported)
- [ ] Update system prompt if needed
- [ ] Test conversation context retention
- [ ] Performance comparison (MCP vs direct API)

## MCP Server Capabilities

According to Databricks documentation, the Genie MCP server provides:

1. **Genie Spaces**: Expose Genie Spaces as MCP resources
2. **Query Execution**: Execute queries against Genie Spaces
3. **Result Formatting**: Standardized result format
4. **Authentication**: Unity Catalog-based authentication
5. **Tool Discovery**: Dynamic tool/resource discovery

## Resources

- [Databricks AI Bridge GitHub](https://github.com/databricks/databricks-ai-bridge)
- [MCP on Databricks Documentation](https://docs.databricks.com/aws/en/generative-ai/mcp/)
- [Multi-Agent Supervisor Guide](https://docs.databricks.com/aws/en/generative-ai/agent-bricks/multi-agent-supervisor)
- [LangChain MCP Integration](https://github.com/databricks/databricks-ai-bridge/tree/main/integrations/langchain)

## Next Steps

1. Review the Databricks AI Bridge repository structure
2. Check if Genie MCP server is available in your workspace
3. Test MCP client connection
4. Create proof-of-concept MCP-based tool
5. Compare performance and functionality
6. Decide on migration approach (direct MCP vs Multi-Agent Supervisor)

