# Genie MCP Server Implementation Plan

## Current State Analysis

### Current Implementation
- **Tool**: `query_genie` - Direct Genie Conversational API calls
- **Method**: `genie.start_conversation()` → polling → extract attachments → get results
- **Complexity**: ~800 lines of code handling API details, polling, error handling
- **Dependencies**: `databricks-sdk` for direct API access

### Target State
- **Tool**: `query_genie_mcp` - MCP-based Genie access
- **Method**: MCP client → Genie MCP server → Genie Space → results
- **Complexity**: Simplified, standardized MCP protocol
- **Dependencies**: `databricks-langchain` for MCP integration

## Implementation Steps

### Phase 1: Research and Setup

1. **Verify MCP Server Availability**
   - Check if Genie MCP server is available in workspace
   - Navigate to: Workspace → Agents → MCP Servers
   - Verify Genie Spaces MCP server is listed

2. **Install Dependencies**
   ```bash
   pip install databricks-langchain
   # Or from source:
   pip install git+https://github.com/databricks/databricks-ai-bridge.git#subdirectory=integrations/langchain
   ```

3. **Understand MCP Server API**
   - Review Databricks AI Bridge repository structure
   - Check available tools/resources exposed by Genie MCP server
   - Understand authentication mechanism (Unity Catalog)

### Phase 2: Create MCP-Based Tool

Create new tool that uses MCP instead of direct API:

```python
from databricks.langchain.mcp import DatabricksMCPClient
from langchain_core.tools import tool
from typing import Annotated

@tool
def query_genie_mcp(
    question: Annotated[str, "A natural language question about battery data"]
) -> str:
    """Query Databricks Genie via MCP server.
    
    This tool uses the Genie MCP server instead of direct API calls.
    Benefits:
    - Standardized MCP protocol
    - Built-in connection management
    - Support for Multi-Agent Supervisor pattern
    """
    # Initialize MCP client (cached)
    mcp_client = get_mcp_client()
    
    # Call Genie through MCP
    # Note: Exact API depends on Genie MCP server implementation
    result = mcp_client.call_tool(
        tool_name="genie_query",  # Tool name from MCP server
        arguments={
            "space_id": GENIE_ROOM_ID,
            "question": question
        }
    )
    
    # Process result (may need to handle chart creation separately)
    return format_mcp_response(result)
```

### Phase 3: Handle Chart Creation

MCP server may not support chart creation directly. Options:

1. **Post-process MCP results**: Extract query results and create charts locally
2. **Hybrid approach**: Use MCP for query, direct API for charts
3. **Check MCP capabilities**: See if Genie MCP server exposes chart creation tools

### Phase 4: Multi-Agent Supervisor (Optional)

If using Multi-Agent Supervisor pattern:

```python
from databricks.agent_bricks import MultiAgentSupervisor

supervisor = MultiAgentSupervisor(
    agents=[
        {
            "name": "battery_data",
            "type": "genie_space",
            "space_id": GENIE_ROOM_ID,
            "description": "Battery trading data queries via Genie"
        },
        {
            "name": "documentation",
            "type": "vector_search",
            "index": INDEX_NAME,
            "description": "Technical documentation search"
        }
    ]
)

# Agent automatically routes to appropriate sub-agent
response = supervisor.query(user_question)
```

## Key Questions to Answer

1. **What tools does Genie MCP server expose?**
   - Tool names and signatures
   - Input/output formats
   - Chart creation support

2. **How does authentication work?**
   - Unity Catalog connections
   - Workspace credentials
   - Token management

3. **What's the response format?**
   - How are SQL queries returned?
   - How are query results formatted?
   - Can charts be embedded?

4. **Performance comparison?**
   - Is MCP faster/slower than direct API?
   - Latency differences
   - Connection overhead

## Testing Strategy

1. **Unit Test MCP Client**
   - Test connection to Genie MCP server
   - Test tool invocation
   - Test error handling

2. **Integration Test**
   - Replace `query_genie` with `query_genie_mcp`
   - Test same queries work correctly
   - Verify chart creation (if supported)

3. **Performance Test**
   - Compare response times
   - Measure API call overhead
   - Check memory usage

4. **Feature Parity Test**
   - All current features work
   - Chart rendering works
   - Error handling works
   - Conversation context works

## Migration Path

### Option A: Parallel Implementation
- Keep both tools (`query_genie` and `query_genie_mcp`)
- Use feature flag to switch between them
- Gradually migrate queries to MCP

### Option B: Direct Replacement
- Replace `query_genie` with `query_genie_mcp`
- Update all references
- Test thoroughly before merging

### Option C: Hybrid Approach
- Use MCP for simple queries
- Use direct API for complex queries (charts, etc.)
- Gradually migrate features to MCP

## Documentation Updates Needed

- Update README with MCP approach
- Document MCP server setup
- Update tool descriptions
- Add troubleshooting guide

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| MCP server not available | Check workspace availability first |
| Different API/response format | Create adapter layer |
| Performance degradation | Benchmark before full migration |
| Missing features (charts) | Hybrid approach or post-processing |
| Breaking changes | Feature flag for gradual rollout |

## Success Criteria

- [ ] MCP-based tool works for all current queries
- [ ] Chart creation works (or alternative solution)
- [ ] Performance is acceptable (within 20% of current)
- [ ] Error handling is robust
- [ ] Code is simpler/maintainable
- [ ] Documentation is updated

