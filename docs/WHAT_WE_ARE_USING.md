# What We're Using vs databricks-ai-bridge

## Current Implementation

### What We're Using:
1. **`databricks.sdk`** - Direct SDK for:
   - `WorkspaceClient` - Workspace management
   - `genie` API - Direct Genie Conversation API calls
   - `statement_execution` - SQL execution

2. **`databricks.vector_search.client`** - Direct Vector Search client:
   - `VectorSearchClient` - Vector Search operations
   - `similarity_search()` - Query vector indexes

3. **`databricks_mcp`** - MCP client (separate package):
   - `DatabricksMCPClient` - Model Context Protocol integration
   - Used for Genie MCP server access

4. **`databricks_langchain`** - For LLM:
   - `ChatDatabricks` - LangChain integration for Databricks LLM endpoints

### What We're NOT Using:
- **`databricks-ai-bridge` Multi-Agent Supervisor APIs** - We built a custom implementation

## About databricks-ai-bridge

According to [GitHub](https://github.com/databricks/databricks-ai-bridge), `databricks-ai-bridge` provides:

1. **`databricks-langchain`** - LangChain/LangGraph integration package
   - Provides shared APIs for Databricks AI features
   - Integrates Genie and Vector Search with LangChain

2. **`databricks-openai`** - OpenAI SDK integration package
   - Similar integration for OpenAI SDK users

3. **Generic `databricks-ai-bridge`** - Base package
   - Core APIs for Databricks AI features

## Our Custom Multi-Agent Supervisor

We built a **custom Multi-Agent Supervisor** that:
- Uses direct SDK calls (not the bridge layer)
- Routes queries intelligently between specialized agents
- Executes agents in parallel for hybrid queries
- Synthesizes responses from multiple agents

## Why Not Use databricks-ai-bridge?

The `databricks-ai-bridge` SDK is available, but:
1. **We're using direct SDK calls** - More control, less abstraction
2. **Custom routing logic** - Our implementation has specific routing needs
3. **Future migration path** - We can migrate to `databricks-ai-bridge` when ready

## Next Steps

1. ✅ **Integrated with Streamlit** - Added toggle to switch between Single Agent and Multi-Agent Supervisor
2. ✅ **Refined routing** - Improved keyword detection for better query routing
3. 🔄 **Future**: Migrate to `databricks-ai-bridge` Multi-Agent Supervisor APIs when available

