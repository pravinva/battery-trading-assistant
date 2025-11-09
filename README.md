# Battery Trading AI Assistant

A production-ready agentic AI assistant using Databricks Mosaic AI Agent Framework that combines structured Delta Lake queries with unstructured PDF documentation retrieval.

## Project Overview

This project builds a unified agent that:
1. **Retrieves unstructured data** from battery integration PDF via Vector Search
2. **Queries structured data** from synthetic Delta Lake tables via SQL tools
3. **Orchestrates multi-tool reasoning** to answer complex battery trading questions
4. **Deploys as Databricks App** with Streamlit chat interface
5. **Evaluates with Agent Evaluation** to measure retrieval quality

## Project Structure

```
battery-trading-assistant/
├── notebooks/
│   ├── 01_data_preparation.py          # Create synthetic tables + vector index
│   ├── 02_agent_development.py         # Build agent with tools
│   ├── 03_agent_evaluation.py          # Evaluate with Agent Evaluation
│   └── 04_deployment.py                # Deploy to Model Serving
├── agent/
│   ├── agent.py                        # Main agent implementation
│   ├── tools.py                        # Custom UC function tools
│   └── config.py                       # Configuration
├── app/
│   ├── app.py                          # Streamlit frontend
│   ├── app.yaml                        # Databricks App config
│   └── requirements.txt                # Dependencies
├── data/
│   └── battery.pdf                     # Source documentation
├── requirements.txt                    # Local development dependencies
└── README.md                           # This file
```

## Prerequisites

1. **Databricks Workspace** with:
   - Unity Catalog enabled
   - Vector Search access
   - Model Serving access
   - Databricks Apps enabled

2. **Databricks CLI** configured:
   ```bash
   # Check your config
   cat ~/.databrickscfg
   ```

3. **Python Environment**:
   ```bash
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

## Setup Instructions

### 1. Upload PDF to Databricks Volumes

First, upload `battery.pdf` to a Unity Catalog Volume:

```python
# In Databricks notebook or using CLI
# Create volume if needed
# Path: /Volumes/ea_trading/battery_trading/pdfs/battery.pdf
```

Or use Databricks CLI:
```bash
databricks fs cp data/battery.pdf dbfs:/Volumes/ea_trading/battery_trading/pdfs/battery.pdf
```

### 2. Upload Notebooks to Databricks

Upload the notebooks to your Databricks workspace:

```bash
# Using Databricks CLI
databricks workspace import notebooks/01_data_preparation.py /Users/<your_email>/battery-trading/01_data_preparation
databricks workspace import notebooks/02_agent_development.py /Users/<your_email>/battery-trading/02_agent_development
databricks workspace import notebooks/03_agent_evaluation.py /Users/<your_email>/battery-trading/03_agent_evaluation
databricks workspace import notebooks/04_deployment.py /Users/<your_email>/battery-trading/04_deployment
```

Or manually upload via Databricks UI:
1. Go to Workspace → Create → Notebook
2. Upload each `.py` file from the `notebooks/` directory

### 3. Run Notebooks in Sequence

Execute the notebooks in order:

#### Phase 1: Data Preparation (`01_data_preparation.py`)
- Creates Unity Catalog catalog and schema
- Creates Delta tables (battery_assets, battery_telemetry, battery_dispatch)
- Processes and chunks battery.pdf
- Creates Vector Search index

**Expected Output:**
- 4 Delta tables created
- Vector Search endpoint and index created
- Test retrieval successful

#### Phase 2: Agent Development (`02_agent_development.py`)
- Creates 4 agent tools (Vector Search, Status, Revenue, Info)
- Builds LangGraph ReAct agent
- Tests agent with various queries
- Logs agent to MLflow

**Expected Output:**
- Agent created and tested
- MLflow run ID for logged agent
- Copy this run ID for next notebook

#### Phase 3: Agent Evaluation (`03_agent_evaluation.py`)
- Creates evaluation dataset (8 questions covering structured, unstructured, and hybrid queries)
- Runs MLflow Agent Evaluation
- Measures retrieval quality and response accuracy

**Expected Output:**
- Evaluation metrics:
  - **Retrieval Precision**: Relevance of retrieved documentation chunks (0.0-1.0)
  - **Response Relevance**: How well answer addresses question (1-5 scale)
  - **Groundedness**: How well answer is supported by data (1-5 scale)
- Evaluation results table with per-question scores

**Viewing Results:**
- **MLflow UI**: Go to Experiments → `/Users/<your_email>/battery_agent_dev` → `battery_agent_evaluation` run
- **Metrics Tab**: View overall metrics (precision, relevance, groundedness)
- **Artifacts Tab**: Download `eval_results_table.parquet` for detailed per-question results
- See `docs/AGENT_EVALUATION_GUIDE.md` for detailed instructions

#### Phase 4: Deployment (`04_deployment.py`)
- Registers agent model to Unity Catalog
- Deploys to Model Serving endpoint
- Creates Streamlit Databricks App

**Expected Output:**
- Model registered in Unity Catalog
- Serving endpoint deployed
- App files created in workspace

### 4. Deploy Databricks App

1. Go to Databricks Apps in your workspace
2. Click "Create App"
3. Select source: `/Workspace/Users/<your_email>/battery-trading-app`
4. Launch and share with your team

## Configuration

Update these values in `agent/config.py` or notebooks as needed:

- `CATALOG`: Unity Catalog catalog name (default: "ea_trading")
- `SCHEMA`: Schema name (default: "battery_trading")
- `LLM_ENDPOINT`: LLM endpoint for agent (default: "databricks-meta-llama-3-1-70b-instruct")
- `EMBEDDING_MODEL`: Embedding model for Vector Search (default: "databricks-gte-large-en")

## Usage Examples

### Query Current Battery Status
```
What is the current SoC for RESS2?
```

### Query Technical Documentation
```
How is throughput calculated for batteries?
```

### Hybrid Query (Combines Both)
```
What's DPNTBESS current SoC and what are the SoC limits for availability?
```

### Revenue Analysis
```
Show me the revenue performance for all batteries in the last 24 hours
```

## Key Features

1. **Unified Intelligence**: One interface for both structured (SQL) and unstructured (RAG/docs) data
2. **Mosaic AI Agent Framework**: Production-grade orchestration with MLflow tracking
3. **Unity Catalog Governance**: All tools governed, lineage tracked
4. **Agent Evaluation**: Built-in quality metrics (retrieval, groundedness, relevance)
5. **Streamlit UI**: User-friendly chat interface with chart rendering
6. **Dual Genie Integration**: 
   - **Genie MCP Server** (Model Context Protocol) - Recommended for production
   - **Direct Genie API** (Conversational API) - Fallback option
7. **Performance Optimized**: Fast response times with minimal API calls
8. **Conversation Context**: Maintains chat history for follow-up questions
9. **Automatic Routing**: Intelligently routes between MCP and Direct API based on availability
10. **Execution Logging**: Tracks which method (MCP vs Direct API) is used for each query

## How the App Works

### Streamlit Interface Behavior

The app provides an interactive chat interface built with Streamlit:

#### **Chat Interface**
- **Conversation History**: All messages are retained in the session, allowing follow-up questions
- **Message Display**: 
  - User messages appear on the right (green theme)
  - Agent responses appear on the left with Energy Australia branding
  - Sources are shown in expandable sections below each response
- **Quick Query Buttons**: Pre-defined queries for common questions (SoC, revenue, throughput)
- **Real-time Updates**: Responses stream in as the agent processes queries

#### **Chart Rendering**
- **Automatic Detection**: Charts are automatically detected and rendered when embedded in responses
- **Plotly Integration**: Uses Plotly for interactive, high-quality visualizations
- **Chart Types**: Supports line charts, bar charts, and pie charts based on data characteristics
- **Explicit Requests Only**: Charts are created only when users explicitly request visualization (e.g., "plot", "chart", "graph", "visualize")
- **No Code Output**: The agent creates visualizations directly - no code examples provided

#### **Source Tracking**
- **Tool Usage**: Shows which tools were used (Vector Search, Genie SQL)
- **Expandable Details**: Click to expand and see:
  - Retrieved documentation chunks (for Vector Search queries)
  - Generated SQL queries (for Genie queries)
  - Raw query results
- **Transparency**: Full visibility into how answers were generated

#### **Performance**
- **Fast Initial Load**: Agent is cached and loads only when needed
- **Optimized API Calls**: Minimal redundant calls to Genie API
- **Conditional Debugging**: Debug logging only when `DEBUG=true` environment variable is set

### App Flow

```
User Question
    ↓
Streamlit App (app/app.py)
    ├── MCP Toggle Check
    ├── Set USE_GENIE_MCP environment variable
    └── Load Agent Module
    ↓
Agent Invocation (LangGraph)
    ↓
Tool Selection (search_battery_docs OR query_genie)
    ↓
Tool Execution
    ├── Vector Search → Documentation chunks
    └── query_genie Tool → Routing Logic
        ├── Check USE_GENIE_MCP flag
        ├── Check _mcp_client availability
        └── Route to:
            ├── MCP Server Path:
            │   ├── Discover MCP tools
            │   ├── Call Genie tool via MCP
            │   ├── Extract JSON response
            │   └── Parse content, query, data
            └── Direct API Path:
                ├── Start conversation
                ├── Wait for completion
                ├── Extract attachments
                ├── Fetch query results
                └── Format response
    ↓
Response Assembly
    ├── Text answer
    ├── Chart (if requested)
    ├── Sources
    └── Execution logs (MCP vs Direct API)
    ↓
Streamlit Rendering
    ├── Display text
    ├── Render Plotly chart
    ├── Show sources
    └── Show execution logs (expander)
```

## How the Agent Works

### Agent Architecture

The agent is built using **LangGraph** (Databricks Mosaic AI Agent Framework) with a ReAct (Reasoning + Acting) pattern:

```
┌─────────────────────────────────────────────────────────┐
│                    LangGraph Agent                       │
│  ┌──────────────────────────────────────────────────┐   │
│  │         LLM (Claude Sonnet 4.5)                  │   │
│  │  - Understands user intent                       │   │
│  │  - Selects appropriate tool                       │   │
│  │  - Synthesizes final answer                      │   │
│  └──────────────────────────────────────────────────┘   │
│                         ↓                                │
│  ┌──────────────────────────────────────────────────┐   │
│  │              Tool Selection                      │   │
│  │  • search_battery_docs (Vector Search)          │   │
│  │  • query_genie (Dynamic SQL)                     │   │
│  └──────────────────────────────────────────────────┘   │
│                         ↓                                │
│  ┌──────────────────────────────────────────────────┐   │
│  │            Tool Execution                        │   │
│  │  ┌──────────────┐      ┌──────────────────┐    │   │
│  │  │ Vector Search│      │  query_genie Tool │    │   │
│  │  │              │      │                  │    │   │
│  │  │ • Embed query│      │  ┌──────────────┐│    │   │
│  │  │ • Search docs│      │  │Routing Logic ││    │   │
│  │  │ • Return top │      │  └──────┬───────┘│    │   │
│  │  │   chunks     │      │         │        │    │   │
│  │  └──────────────┘      │    ┌────┴────┐   │    │   │
│  │                        │    │  MCP?   │   │    │   │
│  │                        │    └────┬────┘   │    │   │
│  │                        │         │        │    │   │
│  │                        │    ┌───┴───┐   │    │   │
│  │                        │    │ YES   │NO │    │   │
│  │                        │    └───┬───┴───┘   │    │   │
│  │                        │        │          │    │   │
│  │                        │  ┌─────┴─────┐   │    │   │
│  │                        │  │           │   │    │   │
│  │                        │  ▼           ▼   │    │   │
│  │                        │┌──────┐  ┌──────────┐│    │   │
│  │                        ││ MCP  │  │  Direct  ││    │   │
│  │                        ││Server│  │   API    ││    │   │
│  │                        │└──────┘  └──────────┘│    │   │
│  │                        │  │           │       │    │   │
│  │                        │  │           │       │    │   │
│  │                        │  ▼           ▼       │    │   │
│  │                        │• Discover   • Start  │    │   │
│  │                        │  tools      conv    │    │   │
│  │                        │• Call tool  • Poll  │    │   │
│  │                        │• Parse JSON • Extract│    │   │
│  │                        │            • Fetch   │    │   │
│  │                        └──────────┬───────────┘    │   │
│  │                                   │                │   │
│  │                                   ▼                │   │
│  │                        • Generate SQL              │   │
│  │                        • Execute query             │   │
│  │                        • Return results            │   │
│  │                        • Create chart              │   │
│  │                        • Log execution method      │   │
│  └──────────────────────────────────────────────────┘   │
│                         ↓                                │
│  ┌──────────────────────────────────────────────────┐   │
│  │         Response Synthesis                       │   │
│  │  • Combine tool results                         │   │
│  │  • Format answer                                │   │
│  │  • Add sources                                  │   │
│  │  • Embed charts (if requested)                   │   │
│  │  • Include execution logs                        │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Code Flow: query_genie Tool

The `query_genie` tool implements intelligent routing between MCP and Direct API:

```python
@tool
def query_genie(question: str) -> str:
    """Query Databricks Genie for SQL generation"""
    
    # Detect visualization request
    is_visualization_request = detect_visualization_keywords(question)
    
    # Route based on configuration
    if USE_GENIE_MCP and _mcp_client:
        # Route to MCP Server
        add_genie_log("🔌 Routing to Genie MCP server")
        return query_genie_via_mcp(question, is_visualization_request)
    else:
        # Route to Direct API
        add_genie_log("🔌 Routing to Direct Genie API")
        return query_genie_via_direct_api(question, is_visualization_request)
```

**Key Functions:**

1. **`query_genie_via_mcp()`**: 
   - Discovers MCP tools via `list_tools()`
   - Calls Genie tool via `call_tool()`
   - Parses JSON response from MCP result
   - Extracts `content`, `query`, and `data` fields

2. **`query_genie_via_direct_api()`**:
   - Starts conversation via `start_conversation()`
   - Waits for completion (Wait object or polling)
   - Extracts attachments from message
   - Fetches query results via Statement Execution API
   - Formats response with SQL and results

3. **`get_genie_logs()`**: Returns execution logs showing which method was used

4. **`add_genie_log()`**: Safely adds log entries (won't break flow if logging fails)

### Tool Selection Logic

The agent uses intelligent tool selection based on question type:

#### **1. search_battery_docs (Vector Search)**
**When Used:**
- Questions about "how", "why", "explain"
- Technical concepts and processes
- Documentation lookups
- Examples: "How is throughput calculated?", "What are SoC limits?"

**How It Works:**
1. Embeds user question using `databricks-gte-large-en` model
2. Searches Vector Search index (`ea_trading.battery_trading.battery_docs_index`)
3. Retrieves top 3-5 most relevant documentation chunks
4. Returns chunks with metadata (page numbers, source)

#### **2. query_genie (Dynamic SQL Generation)**
**When Used:**
- Data queries (SoC, revenue, throughput, comparisons)
- Questions requiring SQL execution
- Time-series analysis
- Examples: "What's the current SoC for RESS2?", "Show revenue for last 24 hours"

**How It Works:**

**MCP Path:**
1. Discovers available tools from MCP server (`list_tools()`)
2. Finds Genie query tool (name contains "query")
3. Calls tool via MCP (`call_tool(tool_name, {"query": question})`)
4. Extracts JSON response from MCP result
5. Parses `content`, `query`, and `data` fields
6. Formats response with SQL and results
7. Creates charts if explicitly requested

**Direct API Path:**
1. Sends natural language question to Genie Conversational API (`start_conversation()`)
2. Waits for completion (Wait object or polling)
3. Extracts attachments from completed message
4. Extracts SQL query and `statement_id` from attachments
5. Fetches query results via Statement Execution API
6. Returns formatted results
7. Creates charts if explicitly requested (see Chart Creation below)

**Automatic Routing:**
- Checks `USE_GENIE_MCP` environment variable
- Checks if `_mcp_client` is initialized
- Routes to MCP if both conditions are true
- Falls back to Direct API otherwise
- Logs which method is used for debugging

### Conversation Flow

The agent maintains conversation context:

```python
# Conversation history is built from session state
message_history = [
    HumanMessage(content="What's the SoC for RESS2?"),
    AIMessage(content="RESS2 current SoC is 82.7%..."),
    HumanMessage(content="What about DPNTBESS?"),  # Can reference previous context
    AIMessage(content="DPNTBESS current SoC is 67.2%...")
]

# Full history is passed to agent
response = agent.invoke({
    "messages": message_history
})
```

**Key Behaviors:**
- **Context Retention**: Previous questions and answers are remembered
- **Follow-up Questions**: Can ask "What about X?" referring to previous context
- **Multi-turn Conversations**: Supports complex multi-step queries

### Chart Creation Behavior

Charts are created **only when explicitly requested** by the user:

#### **Explicit Visualization Keywords**
- "plot", "chart", "graph", "visualize", "visualization"
- "show me a chart", "display a graph", "create a chart"

#### **Chart Creation Process**
1. **Detection**: Agent detects explicit visualization request in question
2. **Data Retrieval**: Genie executes SQL and returns query results
3. **Chart Generation**: `create_plotly_chart()` function:
   - Converts query data to pandas DataFrame
   - Detects chart type (line/bar/pie) based on data and question
   - Creates Plotly figure with proper styling
   - Extracts column names from SQL result manifest
   - Sets axis labels and titles
4. **Embedding**: Chart JSON is embedded in response with markers:
   ```
   [PLOTLY_CHART_START]
   {"type": "line", "json": {...}, "title": "..."}
   [PLOTLY_CHART_END]
   ```
5. **Rendering**: Streamlit app extracts and renders chart using Plotly

#### **Chart Types**
- **Line Charts**: Time-series data (dates, timestamps)
- **Bar Charts**: Categorical comparisons
- **Pie Charts**: Proportions and distributions

#### **No Automatic Charts**
- Charts are **NOT** created automatically for multi-row results
- Charts are **NOT** created unless user explicitly requests visualization
- This improves performance for data-only queries

### Performance Optimizations

The agent has been optimized for fast response times:

#### **1. Removed Redundant API Calls**
- **Before**: Called `list_conversation_messages` + `get_message` (redundant)
- **After**: Extract attachments directly from `start_conversation` Wait object
- **Savings**: ~500ms-2s per query

#### **2. Direct Attachment Extraction**
- **Before**: Multiple API calls to get message details
- **After**: Extract attachments directly from completed message
- **Savings**: ~300ms-1s per query

#### **3. Conditional Debug Logging**
- **Before**: Extensive file I/O and logging on every query
- **After**: Debug logging only when `DEBUG=true` environment variable is set
- **Savings**: ~100-500ms per query (depending on logging volume)

#### **4. Simplified Message Extraction**
- **Before**: Complex fallback logic with multiple API calls
- **After**: Streamlined extraction from Wait object result
- **Savings**: Reduced complexity and faster execution

#### **5. Chart Creation Only When Needed**
- **Before**: Charts created automatically for multi-row results
- **After**: Charts only when explicitly requested
- **Savings**: Significant time savings for data-only queries

### Error Handling

The agent has robust error handling:

1. **Genie API Failures**: Raises exceptions (doesn't fall back to hardcoded SQL)
2. **Missing Data**: Explicitly fails if Genie cannot provide valid answer
3. **Timeout Handling**: Uses Wait object with 60-second timeout
4. **Status Polling**: Only polls if message isn't already completed
5. **Tool Validation**: Validates tools are correctly configured before use

### System Prompt

The agent uses a comprehensive system prompt that:
- Defines role as Energy Australia battery trading expert
- Specifies tool usage guidelines
- Enforces professional tone
- Instructs chart creation behavior
- Guides response formatting

## Genie Integration: MCP vs Direct API

The agent supports **two methods** for interacting with Databricks Genie:

1. **Genie MCP Server** (Model Context Protocol) - Recommended for production
2. **Direct Genie API** (Conversational API) - Fallback option

### Architecture Overview

```
User Question → Agent → query_genie Tool → [Routing Logic] → [MCP Server OR Direct API] → SQL Generation → Query Execution → Results
```

### Routing Logic

The agent automatically routes queries based on configuration:

```python
if USE_GENIE_MCP and _mcp_client:
    # Route to MCP Server
    return query_genie_via_mcp(question, is_visualization_request)
else:
    # Route to Direct API
    return query_genie_via_direct_api(question, is_visualization_request)
```

**Configuration:**
- **Enable MCP**: Set `USE_GENIE_MCP=true` environment variable or toggle in Streamlit UI
- **MCP Server URL**: Automatically constructed as `https://<workspace-hostname>/api/2.0/mcp/genie/{genie_space_id}`
- **Fallback**: If MCP is unavailable or fails, automatically falls back to Direct API

### Method 1: Genie MCP Server (Recommended)

**What is MCP?**
- **Model Context Protocol (MCP)** is a standardized protocol for connecting AI agents to external tools
- Databricks provides a **managed MCP server** for Genie Spaces, Vector Search indexes, and Unity Catalog functions
- MCP offers a unified, standardized API for tool interaction

**Benefits:**
- ✅ Standardized protocol (not Databricks-specific)
- ✅ Tool discovery via `list_tools()`
- ✅ Better error handling and connection management
- ✅ Future-proof architecture

**How It Works:**

```
1. Initialize MCP Client
   ↓
2. Discover Tools (list_tools())
   ↓
3. Find Genie Query Tool
   ↓
4. Call Tool via MCP (call_tool())
   ↓
5. Extract Response from MCP Result
   ↓
6. Parse JSON Response (content, query, data)
   ↓
7. Format and Return
```

**Implementation:**

```python
# Initialize MCP client
_mcp_client = DatabricksMCPClient(
    server_url=f"{workspace_hostname}/api/2.0/mcp/genie/{GENIE_ROOM_ID}",
    workspace_client=w
)

# Discover tools
tools = _mcp_client.list_tools()
genie_tool = [t for t in tools if "query" in t.name.lower()][0]

# Call tool
result = _mcp_client.call_tool(genie_tool.name, {"query": question})

# Extract response
content = result.content[0].text
parsed = json.loads(content)
genie_response = parsed.get("content")
sql_query = parsed.get("query")
query_data = parsed.get("data")
```

**Error Handling:**
- Network errors (broken pipe, connection errors) are caught and reported clearly
- Falls back to Direct API if MCP initialization fails
- Logs all execution steps for debugging

### Method 2: Direct Genie API (Fallback)

The agent uses the **Databricks Genie Conversational API** to dynamically generate and execute SQL queries. This is the original implementation and serves as a fallback when MCP is unavailable.

**How It Works:**

```
1. Start Conversation (start_conversation)
   ↓
2. Wait for Completion (Wait object or polling)
   ↓
3. Extract Attachments from Message
   ↓
4. Extract SQL Query and statement_id
   ↓
5. Fetch Query Results (Statement Execution API)
   ↓
6. Format Response
```

#### Step 1: Start Conversation

```python
conversation_wait = genie.start_conversation(GENIE_ROOM_ID, question)
```

- Sends natural language question to Genie space
- Returns a `Wait[GenieMessage]` object
- Extracts `message_id` and `conversation_id` from response

#### Step 2: Wait for Completion

**Optimized Approach:**
- Uses `Wait` object's built-in waiting mechanism (faster than manual polling)
- Falls back to manual polling only if Wait object doesn't work
- Maximum wait time: 60 seconds

**Manual Polling (Fallback):**
Following [Genie API best practices](https://docs.databricks.com/aws/en/genie/conversation-api#-best-practices-for-using-the-genie-api):

```python
# Poll every 1-3 seconds with exponential backoff
# Max polling time: 30 seconds (optimized for speed)
while status not in ['COMPLETED', 'FAILED', 'CANCELLED']:
    message_details = genie.get_message(
        space_id=GENIE_ROOM_ID, 
        conversation_id=conversation_id, 
        message_id=message_id
    )
    status = message_details.status
    # Check status and wait with exponential backoff
```

**Key Points:**
- Polls every 1 second initially, up to 3 seconds max interval
- Exponential backoff: `poll_interval = min(poll_interval * 1.2, 3)`
- Breaks immediately when status is `COMPLETED`
- Maximum polling time: 30 seconds (optimized for UI responsiveness)

#### Step 3: Extract Response from Attachments

When status is `COMPLETED`, Genie's response is in the `attachments` array:

```python
attachments = message_details.attachments  # List of GenieAttachment objects

for attachment in attachments:
    # Extract SQL query (GenieQueryAttachment object)
    query_obj = attachment.query  # GenieQueryAttachment
    sql_query = query_obj.query   # Actual SQL string
    
    # Extract statement_id for query results
    statement_id = query_obj.statement_id  # UUID for fetching results
    
    # Extract text response (if available)
    text_response = attachment.text  # Usually None for SQL queries
```

**Response Structure:**
```
GenieMessage
├── status: MessageStatus.COMPLETED
├── attachments: [
│     GenieAttachment(
│       attachment_id: "...",
│       query: GenieQueryAttachment(
│         query: "SELECT ...",           # SQL string
│         statement_id: "uuid",          # For fetching results
│         description: "...",
│         query_result_metadata: {...}
│       ),
│       text: None                       # Usually None for SQL
│     )
│   ]
└── query_result: Result(...)            # Metadata only
```

#### Step 4: Fetch Query Results

Genie doesn't return query results directly. Instead, use the `statement_id` from the attachment:

```python
# Use statement execution API to get actual results
from databricks.sdk.service.sql import StatementState

result = w.statement_execution.get_statement(statement_id)

if result.status.state == StatementState.SUCCEEDED:
    query_data = result.result.data_array  # List of rows
    # Each row is a list: ['battery_id', 'value']
```

**Why `statement_id`?**
- Genie executes SQL asynchronously
- `statement_id` is the execution handle
- Use Databricks Statement Execution API to fetch results
- Results are in `data_array` format: `[['DPNTBESS', '183.95'], ['GANNBG1', '334.41'], ...]`

### Response Decoding Flow

```
1. Start Conversation
   ↓
2. Poll for Status (COMPLETED/FAILED/CANCELLED)
   ↓
3. Extract Attachments Array
   ↓
4. For each attachment:
   ├── Extract SQL: attachment.query.query
   ├── Extract statement_id: attachment.query.statement_id
   └── Extract text: attachment.text (usually None)
   ↓
5. Fetch Results via Statement Execution API
   ↓
6. Format Response:
   ├── Genie's answer (if text available)
   ├── Generated SQL query
   └── Query results (from statement_id)
```

### Key Implementation Details

#### Status Handling

```python
# Handle MessageStatus enum (not just strings)
status_str = str(message_status)
if (message_status in ['COMPLETED', 'FAILED', 'CANCELLED'] or 
    'COMPLETED' in status_str):
    # Break polling loop
```

#### Query Extraction

```python
# GenieQueryAttachment is an object, not a string
query_obj = attachment.query  # GenieQueryAttachment object
sql_query = query_obj.query    # Extract SQL string
statement_id = query_obj.statement_id  # Extract statement ID
```

#### Error Handling

- **Timeout**: If polling exceeds 2 minutes, use last known status
- **Missing Data**: Fail explicitly if no valid answer extracted
- **API Errors**: Raise exceptions (don't return error strings) to prevent fallback

### Testing the API

Use the test script to inspect Genie responses:

```bash
export GENIE_ROOM_ID="your-space-id"
python3 scripts/test_genie_api.py
```

This script:
- Starts a conversation
- Polls for status
- Extracts attachments
- Fetches query results
- Prints full response structure

### Best Practices

Following [Databricks Genie API best practices](https://docs.databricks.com/aws/en/genie/conversation-api#-best-practices-for-using-the-genie-api):

1. **Polling**: 1-5 second intervals with exponential backoff (max 10 seconds)
2. **Timeout**: 2 minutes max (reduced for UI responsiveness)
3. **Status Check**: Break immediately on `COMPLETED`
4. **Error Handling**: Fail explicitly, don't silently fall back
5. **New Conversations**: Start fresh conversation for each session

### Troubleshooting

**Issue**: Genie returns question instead of answer
- **Cause**: Polling too early, status not COMPLETED yet
- **Fix**: Ensure status is `COMPLETED` before extracting response

**Issue**: Can't extract SQL query
- **Cause**: `attachment.query` is `GenieQueryAttachment` object, not string
- **Fix**: Extract `attachment.query.query` (nested `.query` attribute)

**Issue**: No query results
- **Cause**: Using `attachment_id` instead of `statement_id`
- **Fix**: Use `attachment.query.statement_id` with Statement Execution API

**Issue**: Different SQL in Genie UI vs Streamlit
- **Cause**: Genie may interpret questions differently based on context
- **Fix**: Add clear instructions and SQL examples to Genie space (see `docs/GENIE_INSTRUCTIONS.md`)

### Related Documentation

- **Genie Setup**: `docs/GENIE_INSTRUCTIONS.md` - How to configure Genie space
- **SQL Expressions**: `docs/GENIE_SQL_EXPRESSIONS_GUIDE.md` - Measures, dimensions, filters
- **Query Consistency**: `docs/GENIE_QUERY_CONSISTENCY.md` - Handling different SQL interpretations
- **Test Questions**: `docs/GENIE_TEST_QUESTIONS.md` - Recommended test queries

## Troubleshooting

### Vector Search Index Not Found
- Ensure notebook 01 completed successfully
- Check that index name matches: `ea_trading.battery_trading.battery_docs_index`
- Verify Vector Search endpoint exists: `ea_trading_endpoint`

### Model Serving Endpoint Not Ready
- Wait for deployment (can take 5-10 minutes)
- Check endpoint status in Databricks UI
- Verify model is registered in Unity Catalog

### PDF Not Found
- Ensure battery.pdf is uploaded to `/Volumes/ea_trading/battery_trading/pdfs/battery.pdf`
- Check Unity Catalog permissions for volume access

## Next Steps

1. Customize system prompt in `agent/agent.py` for your use case
2. Add more tools as needed
3. Expand evaluation dataset in notebook 03
4. Customize Streamlit UI in `app/app.py`

## References

- [Databricks Mosaic AI Agent Framework](https://docs.databricks.com/en/generative-ai/tutorials/agent-framework-notebook)
- [Vector Search Documentation](https://docs.databricks.com/en/vector-search/index.html)
- [Model Serving Documentation](https://docs.databricks.com/en/machine-learning/model-serving/index.html)
- [Databricks Apps Documentation](https://docs.databricks.com/en/dev-tools/databricks-apps/index.html)

## License

This project is for demonstration purposes.

