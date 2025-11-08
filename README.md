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
- Creates evaluation dataset
- Runs MLflow evaluation
- Measures retrieval quality and response accuracy

**Expected Output:**
- Evaluation metrics (precision, relevance, groundedness)
- Evaluation results table

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
5. **Streamlit UI**: User-friendly chat interface
6. **Databricks Genie Integration**: Dynamic SQL generation via Genie Conversational API

## Genie Conversational API Integration

The agent uses the **Databricks Genie Conversational API** to dynamically generate and execute SQL queries. This section explains how the API response decoding works.

### Architecture Overview

```
User Question → Agent → query_genie Tool → Genie API → SQL Generation → Query Execution → Results
```

### API Flow

#### Step 1: Start Conversation

```python
conversation_wait = genie.start_conversation(GENIE_ROOM_ID, question)
```

- Sends natural language question to Genie space
- Returns a `Wait[GenieMessage]` object
- Extracts `message_id` and `conversation_id` from response

#### Step 2: Poll for Status

Following [Genie API best practices](https://docs.databricks.com/aws/en/genie/conversation-api#-best-practices-for-using-the-genie-api):

```python
# Poll every 2-10 seconds with exponential backoff
# Max polling time: 2 minutes (for UI responsiveness)
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
- Polls every 2 seconds initially, up to 10 seconds max interval
- Exponential backoff: `poll_interval = min(poll_interval * 1.5, 10)`
- Breaks immediately when status is `COMPLETED`
- Maximum polling time: 2 minutes (reduced from 10 minutes for UI responsiveness)

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

