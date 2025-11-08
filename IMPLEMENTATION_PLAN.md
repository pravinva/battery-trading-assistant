# Battery Trading Assistant - Implementation Plan

## Overview
Build a production-ready agentic AI assistant using Databricks Mosaic AI Agent Framework that combines:
- **Unstructured data**: Battery integration PDF via Vector Search (RAG)
- **Structured data**: Synthetic Delta Lake tables via SQL tools
- **Deployment**: Databricks App with Streamlit chat interface

## Implementation Phases

### Phase 1: Environment Setup ✅
- [x] Create Python virtual environment
- [x] Create project directory structure
- [x] Copy battery.pdf to data/ directory
- [ ] Install dependencies
- [ ] Verify Databricks CLI configuration

### Phase 2: Data Preparation (Notebook 01)
**Objective**: Create Delta tables and Vector Search index

**Tasks**:
1. Create Unity Catalog catalog and schema (`ea_trading.battery_trading`)
2. Create Delta tables:
   - `battery_assets` - Asset metadata (capacity, location, partner)
   - `battery_telemetry` - Time-series SoC and capability data
   - `battery_dispatch` - Dispatch and revenue data
3. Process battery.pdf:
   - Extract text using PyPDF
   - Chunk using LangChain RecursiveCharacterTextSplitter
   - Store chunks in `battery_documents` Delta table
4. Create Vector Search:
   - Create endpoint (`ea_trading_endpoint`)
   - Create index on `battery_documents` table
   - Sync index
   - Test retrieval

**Dependencies**: `databricks-vectorsearch`, `pypdf`, `langchain-text-splitters`, `pyspark`

### Phase 3: Agent Development (Notebook 02)
**Objective**: Build agent with tools and LangGraph orchestration

**Tasks**:
1. Create agent tools:
   - `search_battery_docs` - Vector Search for PDF documentation
   - `get_battery_status` - Query current SoC and capabilities
   - `get_battery_revenue` - Calculate revenue over time period
   - `get_battery_info` - Get asset specifications
2. Build LangGraph agent:
   - Initialize ChatDatabricks LLM
   - Create ReAct agent with tools
   - Define system prompt
3. Test agent with various query types:
   - Structured queries (SoC, revenue)
   - Unstructured queries (technical docs)
   - Hybrid queries (combining both)
4. Log agent to MLflow

**Dependencies**: `databricks-agents`, `mlflow`, `langgraph`, `langchain-community`

### Phase 4: Agent Evaluation (Notebook 03)
**Objective**: Evaluate agent performance

**Tasks**:
1. Create evaluation dataset with diverse query types
2. Run MLflow evaluation
3. Measure metrics:
   - Retrieval precision
   - Response quality
   - Groundedness
4. Generate evaluation report

**Dependencies**: `databricks-agents`, `mlflow`, `pandas`

### Phase 5: Deployment (Notebook 04)
**Objective**: Deploy agent to production

**Tasks**:
1. Register agent model to Unity Catalog
2. Deploy to Model Serving endpoint
3. Create Streamlit Databricks App:
   - Build chat interface
   - Connect to serving endpoint
   - Add status indicators
4. Test end-to-end deployment

**Dependencies**: `databricks-sdk`, `streamlit`, `mlflow`

### Phase 6: Supporting Code
**Objective**: Create reusable agent and app components

**Tasks**:
1. Create `agent/config.py` - Configuration management
2. Create `agent/tools.py` - Tool definitions (if extracting from notebook)
3. Create `agent/agent.py` - Agent implementation (if extracting from notebook)
4. Create `app/requirements.txt` - App dependencies
5. Create `README.md` - Setup and usage instructions

## Key Decisions & Clarifications Needed

### Questions:
1. **Vector Search Endpoint**: Should we create a new endpoint or use existing? (Plan: Create new `ea_trading_endpoint`)
2. **Embedding Model**: Which model to use? (Plan: `databricks-gte-large-en` as specified)
3. **LLM Endpoint**: Which model for agent? (Plan: `databricks-meta-llama-3-1-70b-instruct`)
4. **Volume Path**: Where to store PDF? (Plan: `/Volumes/ea_trading/battery_trading/pdfs/battery.pdf`)
5. **User Email**: For app directory path (Need to get from Databricks workspace)

### Technical Approach:
- **Chunking Strategy**: RecursiveCharacterTextSplitter with 512 tokens, 50 overlap
- **Vector Index**: Delta Sync Index with TRIGGERED pipeline
- **Agent Framework**: LangGraph ReAct agent
- **Deployment**: Model Serving endpoint + Databricks App

## Next Steps
1. ✅ Environment setup complete
2. ⏭️ Create Notebook 01 (Data Preparation)
3. ⏭️ Create Notebook 02 (Agent Development)
4. ⏭️ Create Notebook 03 (Evaluation)
5. ⏭️ Create Notebook 04 (Deployment)
6. ⏭️ Create supporting code files
7. ⏭️ Create README

## Testing Strategy
- Unit test each tool individually
- Test agent with sample queries
- Validate Vector Search retrieval quality
- Test end-to-end in Streamlit app
- Run evaluation suite

