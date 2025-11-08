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

