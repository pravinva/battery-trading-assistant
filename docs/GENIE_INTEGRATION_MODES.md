# Genie Integration: MCP vs Direct API

## Current Behavior

### Single Agent Mode
- **Uses**: `query_genie` tool from `scripts/02_agent_development_local.py`
- **Routing**: Checks `USE_GENIE_MCP` environment variable and `_mcp_client`
- **MCP Toggle**: Available in sidebar (only shown in Single Agent mode)
- **Behavior**: 
  - If MCP toggle is ON → Uses `query_genie_via_mcp()`
  - If MCP toggle is OFF → Uses `query_genie_via_direct_api()`

### Multi-Agent Supervisor Mode
- **Uses**: `DataAgent` which calls Genie functions from `scripts/02_agent_development_local.py`
- **Routing**: NOW respects `USE_GENIE_MCP` flag from agent module (FIXED)
- **MCP Toggle**: Available in sidebar (applies to both modes)
- **Behavior**:
  - If MCP toggle is ON → Uses `query_genie_via_mcp()` via DataAgent
  - If MCP toggle is OFF → Uses `query_genie_via_direct_api()` via DataAgent

## How It Works

### Single Agent Mode Flow
```
User Query
  ↓
LangGraph Agent
  ↓
query_genie tool
  ↓
Checks: USE_GENIE_MCP && _mcp_client?
  ├─ YES → query_genie_via_mcp()
  └─ NO  → query_genie_via_direct_api()
```

### Multi-Agent Supervisor Mode Flow
```
User Query
  ↓
Supervisor Agent
  ↓
DataAgent.process()
  ↓
_get_query_genie_func()
  ↓
Checks: agent_module.USE_GENIE_MCP && agent_module._mcp_client?
  ├─ YES → query_genie_via_mcp()
  └─ NO  → query_genie_via_direct_api()
```

## Configuration

The MCP toggle in the sidebar controls `USE_GENIE_MCP` environment variable, which:
1. Is set before loading the agent module
2. Is read by `scripts/02_agent_development_local.py` to initialize MCP client
3. Is checked by both Single Agent and Multi-Agent Supervisor modes

## Summary

- **Single Agent**: Can use MCP or Direct API (controlled by toggle)
- **Multi-Agent Supervisor**: Can use MCP or Direct API (controlled by toggle) ✅ FIXED
- **Both modes**: Respect the same `USE_GENIE_MCP` setting

