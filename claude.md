battery-trading-agent/
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
└── README.md                           # Setup instructions

# Battery Trading AI Assistant - Mosaic AI Agent Framework POC

**Project:** Hybrid RAG + Genie Demo for Energy Australia Trading Team  
**Framework:** Databricks Mosaic AI Agent Framework  
**Timeline:** 3 days to November 11 demo  
**Demo Goal:** Show unified agent that combines structured Delta Lake queries with unstructured PDF documentation retrieval

---

## Project Overview

Build a production-ready agentic AI assistant using Mosaic AI Agent Framework that:
1. **Retrieves unstructured data** from battery integration PDF via Vector Search
2. **Queries structured data** from synthetic Delta Lake tables via SQL tools
3. **Orchestrates multi-tool reasoning** to answer complex battery trading questions
4. **Deploys as Databricks App** with Streamlit chat interface
5. **Evaluates with Agent Evaluation** to measure retrieval quality

---

## Project Structure

```
battery-trading-agent/
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
└── README.md                           # Setup instructions
```

***

## Phase 1: Data Preparation (Day 1 Morning)

### Notebook: `01_data_preparation.py`

**Objectives:**
1. Create synthetic Delta tables for battery trading
2. Ingest and chunk battery.pdf
3. Create Vector Search index
4. Validate data access

**Implementation:**

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # Phase 1: Battery Trading Data Preparation
# MAGIC 
# MAGIC This notebook prepares:
# MAGIC 1. Synthetic Delta Lake tables (telemetry, availability, dispatch)
# MAGIC 2. Vector Search index on battery.pdf
# MAGIC 3. Unity Catalog governance setup

# COMMAND ----------
# MAGIC %pip install databricks-vectorsearch pypdf langchain-text-splitters databricks-agents mlflow

# COMMAND ----------
dbutils.library.restartPython()

# COMMAND ----------
# MAGIC %md
# MAGIC ## 1.1 Create Delta Tables for Structured Data

# COMMAND ----------
from pyspark.sql.types import *
from pyspark.sql.functions import *
from datetime import datetime, timedelta
import random

# Set catalog and schema
catalog = "ea_trading"
schema = "battery_trading"

spark.sql(f"CREATE CATALOG IF NOT EXISTS {catalog}")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")
spark.sql(f"USE CATALOG {catalog}")
spark.sql(f"USE SCHEMA {schema}")

# COMMAND ----------
# MAGIC %md
# MAGIC ### Battery Assets Table

# COMMAND ----------
battery_assets_data = [
    ("RESS2", "Riverina Energy Storage System 2", "Darlington Point", 50.0, 75.0, 7.5, "Wartsila", "2023-06-15", True),
    ("DPNTBESS", "Darlington Point BESS", "Darlington Point", 25.0, 50.0, 5.0, "Wartsila", "2022-11-20", True),
    ("GANNBG1", "Wooreen BESS Generator", "Jeeralang", 150.0, 300.0, 30.0, "Wartsila", "2024-03-10", True),
    ("GANNBL1", "Wooreen BESS Load", "Jeeralang", 150.0, 300.0, 30.0, "Wartsila", "2024-03-10", True),
]

battery_assets_schema = StructType([
    StructField("battery_id", StringType(), False),
    StructField("site_name", StringType(), False),
    StructField("location", StringType(), True),
    StructField("nameplate_capacity_mw", DoubleType(), True),
    StructField("max_soc_mwh", DoubleType(), True),
    StructField("min_soc_mwh", DoubleType(), True),
    StructField("partner", StringType(), True),
    StructField("commissioning_date", StringType(), True),
    StructField("aemo_registered", BooleanType(), True),
])

battery_assets_df = spark.createDataFrame(battery_assets_data, battery_assets_schema)
battery_assets_df.write.mode("overwrite").saveAsTable("battery_assets")

# Add column comments
spark.sql("""
ALTER TABLE battery_assets 
ALTER COLUMN battery_id COMMENT 'AEMO Dispatchable Unit ID (DUID)';
""")
spark.sql("""
ALTER TABLE battery_assets 
ALTER COLUMN nameplate_capacity_mw COMMENT 'Maximum charge/discharge capacity in MW';
""")
spark.sql("""
ALTER TABLE battery_assets 
ALTER COLUMN max_soc_mwh COMMENT 'Maximum state of charge in MWh - battery fully charged';
""")

print("✅ Created battery_assets table")

# COMMAND ----------
# MAGIC %md
# MAGIC ### Battery Telemetry Table (Time Series)

# COMMAND ----------
# Generate synthetic telemetry data for last 24 hours
from datetime import datetime, timedelta
import random

batteries = ["RESS2", "DPNTBESS", "GANNBG1", "GANNBL1"]
battery_capacities = {"RESS2": 75.0, "DPNTBESS": 50.0, "GANNBG1": 300.0, "GANNBL1": 300.0}

telemetry_data = []
base_time = datetime.now() - timedelta(hours=24)

for battery in batteries:
    max_soc = battery_capacities[battery]
    current_soc = max_soc * random.uniform(0.4, 0.8)  # Start at 40-80% SoC
    
    for i in range(288):  # 5-minute intervals for 24 hours
        timestamp = base_time + timedelta(minutes=5*i)
        
        # Simulate charging/discharging patterns
        soc_change = random.uniform(-2, 2)  # MWh change per interval
        current_soc = max(max_soc * 0.1, min(max_soc * 0.9, current_soc + soc_change))
        
        soc_percent = (current_soc / max_soc) * 100
        
        # Capability depends on SoC
        capability_charge = max_soc * 0.67 if soc_percent < 85 else max_soc * 0.3
        capability_discharge = max_soc * 0.67 if soc_percent > 15 else max_soc * 0.3
        
        telemetry_data.append((
            timestamp,
            battery,
            battery,  # DUID same as battery_id for simplicity
            current_soc,
            soc_percent,
            capability_charge,
            capability_discharge,
            random.uniform(100, 500),  # cum_energy_exported
            random.uniform(100, 500),  # cum_energy_imported
            random.uniform(50, 150),  # throughput last 7.5hrs
            max_soc,  # fullpackenergy
            random.randint(0, 15)  # reading_age_minutes
        ))

telemetry_schema = StructType([
    StructField("timestamp", TimestampType(), False),
    StructField("battery_id", StringType(), False),
    StructField("duid", StringType(), False),
    StructField("soc_mwh", DoubleType(), True),
    StructField("soc_percent", DoubleType(), True),
    StructField("capability_charge_mw", DoubleType(), True),
    StructField("capability_discharge_mw", DoubleType(), True),
    StructField("cum_energy_exported_mwh", DoubleType(), True),
    StructField("cum_energy_imported_mwh", DoubleType(), True),
    StructField("throughput_mwh", DoubleType(), True),
    StructField("fullpackenergy_mwh", DoubleType(), True),
    StructField("reading_age_minutes", IntegerType(), True),
])

telemetry_df = spark.createDataFrame(telemetry_data, telemetry_schema)
telemetry_df.write.mode("overwrite").saveAsTable("battery_telemetry")

# Add column comments
spark.sql("""
ALTER TABLE battery_telemetry 
ALTER COLUMN soc_mwh COMMENT 'Current state of charge in MWh - from PI system integration';
""")
spark.sql("""
ALTER TABLE battery_telemetry 
ALTER COLUMN throughput_mwh COMMENT 'Total energy throughput over previous 7.5 hours - used for availability restrictions per Wartsila contractual limits';
""")

print(f"✅ Created battery_telemetry table with {telemetry_df.count()} rows")

# COMMAND ----------
# MAGIC %md
# MAGIC ### Battery Dispatch Table (Simplified)

# COMMAND ----------
dispatch_data = []
base_time = datetime.now() - timedelta(hours=24)

for battery in batteries:
    for i in range(288):
        timestamp = base_time + timedelta(minutes=5*i)
        
        # Simulate dispatch (positive = discharge, negative = charge)
        dispatch_mw = random.uniform(-30, 30)
        spot_price = random.uniform(50, 300)  # $/MWh
        revenue = (dispatch_mw * spot_price * (5/60))  # 5-minute settlement
        
        dispatch_data.append((
            timestamp,
            battery,
            battery,
            dispatch_mw,
            spot_price,
            revenue,
            random.choice(["RAISE_REG", "LOWER_REG", None]),
            random.uniform(0, 5) if random.random() > 0.7 else 0,
            random.uniform(0, 20) if random.random() > 0.7 else 0
        ))

dispatch_schema = StructType([
    StructField("dispatch_interval", TimestampType(), False),
    StructField("battery_id", StringType(), False),
    StructField("duid", StringType(), False),
    StructField("dispatch_mw", DoubleType(), True),
    StructField("spot_price_dollar_per_mwh", DoubleType(), True),
    StructField("revenue_dollar", DoubleType(), True),
    StructField("fcas_service", StringType(), True),
    StructField("fcas_mw", DoubleType(), True),
    StructField("fcas_price_dollar_per_mwh", DoubleType(), True),
])

dispatch_df = spark.createDataFrame(dispatch_data, dispatch_schema)
dispatch_df.write.mode("overwrite").saveAsTable("battery_dispatch")

print(f"✅ Created battery_dispatch table with {dispatch_df.count()} rows")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 1.2 Create Vector Search Index on Battery PDF

# COMMAND ----------
from databricks.vector_search.client import VectorSearchClient
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import pandas as pd

# COMMAND ----------
# Upload battery.pdf to Volumes first
# Path: /Volumes/ea_trading/battery_trading/pdfs/battery.pdf

# Read and chunk PDF
pdf_path = "/Volumes/ea_trading/battery_trading/pdfs/battery.pdf"
reader = PdfReader(pdf_path)

chunks_data = []
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=50,
    separators=["\n\n", "\n", ". ", " ", ""]
)

for page_num, page in enumerate(reader.pages):
    text = page.extract_text()
    if text.strip():  # Only process non-empty pages
        page_chunks = text_splitter.split_text(text)
        
        for idx, chunk in enumerate(page_chunks):
            chunks_data.append({
                'doc_id': 'battery_integration_wartsila_v1',
                'chunk_id': f'bat_int_p{page_num:03d}_c{idx:03d}',
                'content': chunk,
                'doc_title': 'Battery Trading Integration Architecture - Wartsila BESS',
                'doc_type': 'technical_specification',
                'page_number': page_num + 1,
                'chunk_index': idx,
                'created_timestamp': datetime.now()
            })

print(f"✅ Extracted {len(chunks_data)} chunks from {len(reader.pages)} pages")

# COMMAND ----------
# Save chunks to Delta table
chunks_df = spark.createDataFrame(pd.DataFrame(chunks_data))
chunks_df.write.mode("overwrite").saveAsTable("battery_documents")

spark.sql("""
ALTER TABLE battery_documents 
ALTER COLUMN content COMMENT 'Chunked text content from battery integration documentation - used for RAG retrieval';
""")

print("✅ Created battery_documents table")

# COMMAND ----------
# Create Vector Search endpoint and index
vsc = VectorSearchClient(disable_notice=True)

# Create endpoint (only once per workspace)
endpoint_name = "ea_trading_endpoint"

try:
    vsc.create_endpoint(name=endpoint_name, endpoint_type="STANDARD")
    print(f"✅ Created Vector Search endpoint: {endpoint_name}")
except Exception as e:
    if "RESOURCE_ALREADY_EXISTS" in str(e):
        print(f"✅ Vector Search endpoint already exists: {endpoint_name}")
    else:
        raise e

# COMMAND ----------
# Create Vector Search Index
index_name = f"{catalog}.{schema}.battery_docs_index"

index = vsc.create_delta_sync_index(
    endpoint_name=endpoint_name,
    index_name=index_name,
    source_table_name=f"{catalog}.{schema}.battery_documents",
    pipeline_type="TRIGGERED",
    primary_key="chunk_id",
    embedding_source_column="content",
    embedding_model_endpoint_name="databricks-gte-large-en"
)

print(f"✅ Created Vector Search index: {index_name}")

# COMMAND ----------
# Sync the index
index.sync()
print("✅ Vector Search index sync triggered")

# COMMAND ----------
# Test vector search
results = index.similarity_search(
    query_text="How is throughput calculated for batteries?",
    columns=["content", "doc_title", "page_number"],
    num_results=3
)

print("\n🔍 Test Vector Search Results:")
for i, hit in enumerate(results.get('result', {}).get('data_array', []), 1):
    print(f"\nResult {i}:")
    print(f"Page: {hit[2]}")
    print(f"Content: {hit[0][:200]}...")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 1.3 Validation Summary

# COMMAND ----------
print("=" * 80)
print("DATA PREPARATION COMPLETE")
print("=" * 80)
print(f"\n📊 Delta Tables Created:")
print(f"   ✅ {catalog}.{schema}.battery_assets: {spark.table('battery_assets').count()} rows")
print(f"   ✅ {catalog}.{schema}.battery_telemetry: {spark.table('battery_telemetry').count()} rows")
print(f"   ✅ {catalog}.{schema}.battery_dispatch: {spark.table('battery_dispatch').count()} rows")
print(f"   ✅ {catalog}.{schema}.battery_documents: {spark.table('battery_documents').count()} chunks")

print(f"\n🔍 Vector Search:")
print(f"   ✅ Endpoint: {endpoint_name}")
print(f"   ✅ Index: {index_name}")

print(f"\n➡️  Next Step: Run notebook 02_agent_development.py")
```

***

## Phase 2: Agent Development (Day 1 Afternoon)

### Notebook: `02_agent_development.py`

**Objectives:**
1. Create Unity Catalog functions as agent tools
2. Build Mosaic AI Agent with LangGraph
3. Test multi-tool reasoning
4. Log agent to MLflow

**Implementation:**

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # Phase 2: Battery Trading Agent Development
# MAGIC 
# MAGIC Build Mosaic AI Agent with tools:
# MAGIC 1. Vector Search tool (RAG on PDF)
# MAGIC 2. SQL query tool (Delta tables)
# MAGIC 3. LangGraph orchestration

# COMMAND ----------
# MAGIC %pip install databricks-agents mlflow langgraph langchain-community databricks-vectorsearch

# COMMAND ----------
dbutils.library.restartPython()

# COMMAND ----------
import mlflow
from databricks import agents
from databricks.sdk import WorkspaceClient
from langchain_community.chat_models import ChatDatabricks
from langchain_community.vectorstores import DatabricksVectorSearch
from databricks.vector_search.client import VectorSearchClient
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from typing import Annotated

# COMMAND ----------
# Configuration
CATALOG = "ea_trading"
SCHEMA = "battery_trading"
ENDPOINT_NAME = "ea_trading_endpoint"
INDEX_NAME = f"{CATALOG}.{SCHEMA}.battery_docs_index"
LLM_ENDPOINT = "databricks-meta-llama-3-1-70b-instruct"

mlflow.set_registry_uri("databricks-uc")
mlflow.set_experiment(f"/Users/{spark.sql('SELECT current_user()').collect()[0][0]}/battery_agent_dev")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 2.1 Create Agent Tools

# COMMAND ----------
# Tool 1: Vector Search for Technical Documentation
@tool
def search_battery_docs(
    query: Annotated[str, "The search query about battery technical specifications, processes, or architecture"]
) -> str:
    """Search battery integration documentation for technical information about 
    Wartsila BESS systems, PI integration, throughput calculations, SoC limits, 
    and AEMO bidding processes."""
    
    vsc = VectorSearchClient(disable_notice=True)
    index = vsc.get_index(endpoint_name=ENDPOINT_NAME, index_name=INDEX_NAME)
    
    results = index.similarity_search(
        query_text=query,
        columns=["content", "doc_title", "page_number"],
        num_results=3
    )
    
    context_parts = []
    for hit in results.get('result', {}).get('data_array', []):
        content, title, page = hit[0], hit[1], hit[2]
        context_parts.append(f"[Page {page}] {content}")
    
    return "\n\n".join(context_parts) if context_parts else "No relevant documentation found."

# COMMAND ----------
# Tool 2: Query Current Battery Status
@tool
def get_battery_status(
    battery_id: Annotated[str, "Battery ID (RESS2, DPNTBESS, GANNBG1, GANNBL1) or 'all' for all batteries"] = "all"
) -> str:
    """Get current state of charge (SoC), capabilities, and telemetry for batteries.
    Returns latest reading with SoC in MWh and %, charge/discharge capabilities."""
    
    if battery_id.lower() == "all":
        query = """
            SELECT battery_id, 
                   ROUND(soc_mwh, 2) as soc_mwh,
                   ROUND(soc_percent, 1) as soc_percent,
                   ROUND(capability_charge_mw, 1) as charge_cap_mw,
                   ROUND(capability_discharge_mw, 1) as discharge_cap_mw,
                   reading_age_minutes,
                   timestamp
            FROM ea_trading.battery_trading.battery_telemetry
            WHERE timestamp = (SELECT MAX(timestamp) FROM ea_trading.battery_trading.battery_telemetry)
            ORDER BY battery_id
        """
    else:
        query = f"""
            SELECT battery_id, 
                   ROUND(soc_mwh, 2) as soc_mwh,
                   ROUND(soc_percent, 1) as soc_percent,
                   ROUND(capability_charge_mw, 1) as charge_cap_mw,
                   ROUND(capability_discharge_mw, 1) as discharge_cap_mw,
                   reading_age_minutes,
                   timestamp
            FROM ea_trading.battery_trading.battery_telemetry
            WHERE battery_id = '{battery_id.upper()}'
              AND timestamp = (SELECT MAX(timestamp) FROM ea_trading.battery_trading.battery_telemetry)
        """
    
    result = spark.sql(query).collect()
    
    if not result:
        return f"No telemetry data found for battery: {battery_id}"
    
    output = []
    for row in result:
        output.append(
            f"{row.battery_id}: {row.soc_mwh} MWh ({row.soc_percent}% SoC), "
            f"Charge: {row.charge_cap_mw} MW, Discharge: {row.discharge_cap_mw} MW, "
            f"Reading age: {row.reading_age_minutes} min (as of {row.timestamp})"
        )
    
    return "\n".join(output)

# COMMAND ----------
# Tool 3: Query Battery Dispatch Revenue
@tool
def get_battery_revenue(
    battery_id: Annotated[str, "Battery ID (RESS2, DPNTBESS, GANNBG1, GANNBL1)"],
    hours: Annotated[int, "Number of hours to look back (default 24)"] = 24
) -> str:
    """Calculate total revenue/cost for a battery over specified time period.
    Positive revenue = earning from discharge, negative = cost of charging."""
    
    query = f"""
        SELECT battery_id,
               COUNT(*) as num_intervals,
               ROUND(SUM(revenue_dollar), 2) as total_revenue_dollar,
               ROUND(AVG(spot_price_dollar_per_mwh), 2) as avg_spot_price,
               ROUND(SUM(CASE WHEN dispatch_mw > 0 THEN dispatch_mw ELSE 0 END) * 5/60, 2) as total_discharge_mwh,
               ROUND(SUM(CASE WHEN dispatch_mw < 0 THEN ABS(dispatch_mw) ELSE 0 END) * 5/60, 2) as total_charge_mwh
        FROM ea_trading.battery_trading.battery_dispatch
        WHERE battery_id = '{battery_id.upper()}'
          AND dispatch_interval >= current_timestamp() - INTERVAL {hours} HOURS
        GROUP BY battery_id
    """
    
    result = spark.sql(query).collect()
    
    if not result:
        return f"No dispatch data found for {battery_id} in last {hours} hours"
    
    row = result[0]
    return (f"{row.battery_id} performance (last {hours}h):\n"
            f"  Revenue: ${row.total_revenue_dollar:,.2f}\n"
            f"  Avg spot price: ${row.avg_spot_price}/MWh\n"
            f"  Energy discharged: {row.total_discharge_mwh} MWh\n"
            f"  Energy charged: {row.total_charge_mwh} MWh\n"
            f"  Trading intervals: {row.num_intervals}")

# COMMAND ----------
# Tool 4: Get Battery Asset Information
@tool
def get_battery_info(
    battery_id: Annotated[str, "Battery ID or 'all' for all batteries"] = "all"
) -> str:
    """Get battery asset information including capacity, location, partner, and commissioning details."""
    
    if battery_id.lower() == "all":
        query = "SELECT * FROM ea_trading.battery_trading.battery_assets ORDER BY battery_id"
    else:
        query = f"SELECT * FROM ea_trading.battery_trading.battery_assets WHERE battery_id = '{battery_id.upper()}'"
    
    result = spark.sql(query).collect()
    
    if not result:
        return f"No asset information found for: {battery_id}"
    
    output = []
    for row in result:
        output.append(
            f"{row.battery_id} ({row.site_name}):\n"
            f"  Location: {row.location}\n"
            f"  Capacity: {row.nameplate_capacity_mw} MW\n"
            f"  Storage: {row.max_soc_mwh} MWh max, {row.min_soc_mwh} MWh min\n"
            f"  Partner: {row.partner}\n"
            f"  Commissioned: {row.commissioning_date}"
        )
    
    return "\n\n".join(output)

# COMMAND ----------
# Combine all tools
tools = [search_battery_docs, get_battery_status, get_battery_revenue, get_battery_info]

print("✅ Created 4 agent tools:")
for tool in tools:
    print(f"   - {tool.name}: {tool.description[:80]}...")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 2.2 Create Agent with LangGraph

# COMMAND ----------
# Initialize LLM
llm = ChatDatabricks(endpoint=LLM_ENDPOINT, temperature=0.1)

# System prompt
SYSTEM_PROMPT = """You are an expert battery trading assistant for Energy Australia.

You help traders and operators by:
1. Providing real-time battery status (SoC, capabilities, telemetry)
2. Analyzing dispatch performance and revenue
3. Explaining technical specifications and processes from documentation
4. Answering questions about Wartsila BESS integration, AEMO bidding, and operational limits

Important context:
- RESS2 and DPNTBESS are at Darlington Point (Riverina)
- GANNBG1 and GANNBL1 are at Wooreen (Jeeralang) - new Wartsila site
- SoC readings older than 10 minutes may trigger availability restrictions
- Throughput limits over 7.5 hour windows affect bidding

Available tools:
- search_battery_docs: For technical/process questions (how, why, explain)
- get_battery_status: For current SoC and capabilities
- get_battery_revenue: For financial performance analysis
- get_battery_info: For asset specifications

When answering:
- Always use specific data from tools
- Cite sources (e.g., "According to telemetry..." or "From technical docs page X...")
- For technical questions, search docs first
- For operational questions, query live data
- Combine both when needed for comprehensive answers"""

# COMMAND ----------
# Create LangGraph agent
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(
    model=llm,
    tools=tools,
    state_modifier=SYSTEM_PROMPT
)

print("✅ Created LangGraph ReAct agent")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 2.3 Test Agent

# COMMAND ----------
# Test 1: Structured data query
test_query_1 = "What is the current SoC for RESS2?"

print(f"Query: {test_query_1}")
print("=" * 80)

response = agent.invoke({"messages": [{"role": "user", "content": test_query_1}]})
print(response["messages"][-1].content)

# COMMAND ----------
# Test 2: Unstructured documentation query
test_query_2 = "How is throughput calculated for batteries and why does it matter?"

print(f"\nQuery: {test_query_2}")
print("=" * 80)

response = agent.invoke({"messages": [{"role": "user", "content": test_query_2}]})
print(response["messages"][-1].content)

# COMMAND ----------
# Test 3: Hybrid query requiring both tools
test_query_3 = "What's DPNTBESS current SoC and what are the SoC limits for availability?"

print(f"\nQuery: {test_query_3}")
print("=" * 80)

response = agent.invoke({"messages": [{"role": "user", "content": test_query_3}]})
print(response["messages"][-1].content)

# COMMAND ----------
# Test 4: Revenue analysis
test_query_4 = "Show me the revenue performance for all batteries in the last 24 hours"

print(f"\nQuery: {test_query_4}")
print("=" * 80)

response = agent.invoke({"messages": [{"role": "user", "content": test_query_4}]})
print(response["messages"][-1].content)

# COMMAND ----------
# MAGIC %md
# MAGIC ## 2.4 Log Agent to MLflow

# COMMAND ----------
import mlflow
from mlflow.models.resources import (
    DatabricksVectorSearchIndex,
    DatabricksServingEndpoint,
)

# Set model signature
input_example = {"messages": [{"role": "user", "content": "What is RESS2 current SoC?"}]}

# Log the agent
with mlflow.start_run(run_name="battery_agent_v1"):
    logged_agent = mlflow.langchain.log_model(
        lc_model=agent,
        artifact_path="agent",
        input_example=input_example,
        resources=[
            DatabricksVectorSearchIndex(index_name=INDEX_NAME),
            DatabricksServingEndpoint(endpoint_name=LLM_ENDPOINT),
        ],
    )
    
    run_id = mlflow.active_run().info.run_id
    
    print(f"✅ Logged agent to MLflow")
    print(f"   Run ID: {run_id}")
    print(f"   Model URI: runs:/{run_id}/agent")

# COMMAND ----------
# Test logged model
predictions = mlflow.langchain.load_model(f"runs:/{run_id}/agent").invoke(input_example)
print(f"\n✅ Logged model test successful:")
print(predictions["messages"][-1].content[:200])

# COMMAND ----------
print("=" * 80)
print("AGENT DEVELOPMENT COMPLETE")
print("=" * 80)
print(f"\n✅ Agent logged to MLflow: runs:/{run_id}/agent")
print(f"\n➡️  Next Step: Run notebook 03_agent_evaluation.py")
```

***

## Phase 3: Agent Evaluation (Day 2 Morning)

### Notebook: `03_agent_evaluation.py`

**Objectives:**
1. Create evaluation dataset
2. Run Agent Evaluation with mlflow
3. Measure retrieval quality and response accuracy
4. Generate evaluation report

**Implementation:**

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # Phase 3: Battery Agent Evaluation
# MAGIC 
# MAGIC Evaluate agent performance using Mosaic AI Agent Evaluation

# COMMAND ----------
# MAGIC %pip install databricks-agents mlflow pandas

# COMMAND ----------
dbutils.library.restartPython()

# COMMAND ----------
import mlflow
import pandas as pd
from databricks import agents

# COMMAND ----------
# Set your logged agent run ID from previous notebook
AGENT_RUN_ID = "<paste_run_id_from_notebook_02>"  # Update this!
AGENT_MODEL_URI = f"runs:/{AGENT_RUN_ID}/agent"

# COMMAND ----------
# MAGIC %md
# MAGIC ## 3.1 Create Evaluation Dataset

# COMMAND ----------
# Evaluation questions covering different query types
eval_data = [
    {
        "request": "What is the current SoC for RESS2?",
        "expected_response": "Should query battery_telemetry and provide current SoC in MWh and percentage",
        "query_type": "structured"
    },
    {
        "request": "How is throughput calculated for Darlington Point batteries?",
        "expected_response": "Should search documentation and explain the 7.5 hour window calculation formula",
        "query_type": "unstructured"
    },
    {
        "request": "What's the revenue for GANNBG1 in the last 24 hours?",
        "expected_response": "Should query battery_dispatch and calculate total revenue with breakdown",
        "query_type": "structured"
    },
    {
        "request": "Explain the PI system integration architecture",
        "expected_response": "Should retrieve documentation about PI integration and data flow",
        "query_type": "unstructured"
    },
    {
        "request": "What are the SoC limits for DPNTBESS and how do they affect availability?",
        "expected_response": "Should combine asset info query with documentation search about restrictions",
        "query_type": "hybrid"
    },
    {
        "request": "Show me the current status of all Wooreen batteries",
        "expected_response": "Should query GANNBG1 and GANNBL1 telemetry with current SoC and capabilities",
        "query_type": "structured"
    },
    {
        "request": "What happens when battery telemetry reading is older than 10 minutes?",
        "expected_response": "Should search docs about data age restrictions on availability",
        "query_type": "unstructured"
    },
    {
        "request": "Compare revenue performance of RESS2 vs DPNTBESS over last 24 hours",
        "expected_response": "Should query revenue for both batteries and provide comparison",
        "query_type": "structured"
    },
]

eval_df = pd.DataFrame(eval_data)
print(f"✅ Created evaluation dataset with {len(eval_df)} questions")
print(f"\nQuery type distribution:")
print(eval_df['query_type'].value_counts())

# COMMAND ----------
# MAGIC %md
# MAGIC ## 3.2 Run Agent Evaluation

# COMMAND ----------
# Run evaluation
with mlflow.start_run(run_name="battery_agent_evaluation"):
    
    # Evaluate agent
    eval_results = mlflow.evaluate(
        model=AGENT_MODEL_URI,
        data=eval_df,
        model_type="databricks-agent",
    )
    
    print("✅ Evaluation complete!")
    print(f"\nEvaluation Results:")
    print(f"  - Retrieval precision: {eval_results.metrics.get('retrieval/llm_judged/chunk_relevance/precision', 'N/A')}")
    print(f"  - Response quality: {eval_results.metrics.get('response/llm_judged/relevance_to_input/rating', 'N/A')}")
    print(f"  - Groundedness: {eval_results.metrics.get('response/llm_judged/groundedness/rating', 'N/A')}")

# COMMAND ----------
# View detailed results
eval_results_df = eval_results.tables["eval_results"]
display(eval_results_df)

# COMMAND ----------
print("=" * 80)
print("AGENT EVALUATION COMPLETE")
print("=" * 80)
print(f"\n✅ View evaluation results in MLflow UI")
print(f"\n➡️  Next Step: Run notebook 04_deployment.py")
```

***

## Phase 4: Deployment (Day 2 Afternoon)

### Notebook: `04_deployment.py`

**Objectives:**
1. Register agent to Unity Catalog
2. Deploy to Model Serving endpoint
3. Create Streamlit Databricks App
4. Test end-to-end

**Implementation:**

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # Phase 4: Deploy Battery Agent
# MAGIC 
# MAGIC 1. Register to Unity Catalog
# MAGIC 2. Deploy to Model Serving
# MAGIC 3. Create Databricks App

# COMMAND ----------
import mlflow
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ServedEntityInput, EndpointCoreConfigInput

w = WorkspaceClient()
mlflow.set_registry_uri("databricks-uc")

# COMMAND ----------
# Set your agent run ID
AGENT_RUN_ID = "<paste_run_id_from_notebook_02>"  # Update this!
AGENT_MODEL_URI = f"runs:/{AGENT_RUN_ID}/agent"

CATALOG = "ea_trading"
SCHEMA = "battery_trading"
MODEL_NAME = "battery_trading_agent"

# COMMAND ----------
# MAGIC %md
# MAGIC ## 4.1 Register Agent to Unity Catalog

# COMMAND ----------
# Register model
registered_model = mlflow.register_model(
    model_uri=AGENT_MODEL_URI,
    name=f"{CATALOG}.{SCHEMA}.{MODEL_NAME}",
    tags={"use_case": "battery_trading", "version": "v1"}
)

print(f"✅ Registered model: {CATALOG}.{SCHEMA}.{MODEL_NAME}")
print(f"   Version: {registered_model.version}")

# COMMAND ----------
# Add model alias for production
client = mlflow.MlflowClient()
client.set_registered_model_alias(
    name=f"{CATALOG}.{SCHEMA}.{MODEL_NAME}",
    alias="prod",
    version=registered_model.version
)

print(f"✅ Set alias 'prod' to version {registered_model.version}")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 4.2 Deploy to Model Serving

# COMMAND ----------
ENDPOINT_NAME = "battery-trading-agent"

# Deploy agent endpoint
deployment_config = EndpointCoreConfigInput(
    served_entities=[
        ServedEntityInput(
            entity_name=f"{CATALOG}.{SCHEMA}.{MODEL_NAME}",
            entity_version=registered_model.version,
            workload_size="Small",
            scale_to_zero_enabled=True,
        )
    ]
)

try:
    endpoint = w.serving_endpoints.create(
        name=ENDPOINT_NAME,
        config=deployment_config
    )
    print(f"✅ Created serving endpoint: {ENDPOINT_NAME}")
except Exception as e:
    if "already exists" in str(e):
        w.serving_endpoints.update_config(
            name=ENDPOINT_NAME,
            served_entities=deployment_config.served_entities
        )
        print(f"✅ Updated existing endpoint: {ENDPOINT_NAME}")
    else:
        raise e

# COMMAND ----------
# Wait for endpoint to be ready
import time

print("⏳ Waiting for endpoint to be ready...")
for i in range(60):
    endpoint_status = w.serving_endpoints.get(ENDPOINT_NAME)
    if endpoint_status.state.ready == "READY":
        print(f"✅ Endpoint is ready!")
        break
    time.sleep(10)
    if i % 3 == 0:
        print(f"   Still deploying... ({i*10}s elapsed)")

# COMMAND ----------
# Test endpoint
test_payload = {
    "messages": [
        {"role": "user", "content": "What is the current SoC for all batteries?"}
    ]
}

response = w.serving_endpoints.query(ENDPOINT_NAME, dataframe_records=[test_payload])
print(f"✅ Endpoint test successful!")
print(f"\nResponse preview:")
print(response.predictions[0]["content"][:300])

# COMMAND ----------
# MAGIC %md
# MAGIC ## 4.3 Create Databricks App

# COMMAND ----------
# Create app directory structure
dbutils.fs.mkdirs("/Workspace/Users/<your_email>/battery-trading-app")  # Update with your email!

# COMMAND ----------
# Write app.py
app_code = '''
import streamlit as st
from databricks.sdk import WorkspaceClient
import time

st.set_page_config(page_title="Battery Trading Assistant", page_icon="⚡", layout="wide")

# Initialize Databricks client
@st.cache_resource
def get_client():
    return WorkspaceClient()

w = get_client()
ENDPOINT_NAME = "battery-trading-agent"

# Title and description
st.title("⚡ Energy Australia Battery Trading Assistant")
st.caption("Ask questions about battery operations, revenue, or technical specifications")

# Sidebar
with st.sidebar:
    st.header("🔋 System Status")
    
    try:
        endpoint = w.serving_endpoints.get(ENDPOINT_NAME)
        if endpoint.state.ready == "READY":
            st.success("✅ Agent Endpoint: Online")
        else:
            st.warning("⏳ Agent Endpoint: Starting...")
    except:
        st.error("❌ Agent Endpoint: Offline")
    
    st.success("✅ Vector Search: Connected")
    st.success("✅ Delta Lake: Connected")
    
    st.divider()
    
    st.subheader("💡 Example Questions")
    st.markdown("""
    **Current Operations:**
    - What's the SoC for RESS2?
    - Show revenue for all batteries
    
    **Technical Info:**
    - How is throughput calculated?
    - Explain PI integration
    
    **Analysis:**
    - Compare RESS2 vs DPNTBESS revenue
    """)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask about battery trading..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get agent response
    with st.chat_message("assistant"):
        with st.spinner("🤔 Thinking..."):
            try:
                response = w.serving_endpoints.query(
                    name=ENDPOINT_NAME,
                    dataframe_records=[{
                        "messages": st.session_state.messages
                    }]
                )
                
                assistant_message = response.predictions[0]["content"]
                st.markdown(assistant_message)
                
                # Add to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_message
                })
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.info("Make sure the agent endpoint is ready and deployed.")

# Clear chat button
if st.sidebar.button("🗑️ Clear Chat"):
    st.session_state.messages = []
    st.rerun()
'''

# Write to file
with open("/Workspace/Users/<your_email>/battery-trading-app/app.py", "w") as f:
    f.write(app_code)

print("✅ Created app.py")

# COMMAND ----------
# Create app.yaml
app_yaml = '''
command: ["streamlit", "run", "app.py", "--server.port", "8080"]
'''

with open("/Workspace/Users/<your_email>/battery-trading-app/app.yaml", "w") as f:
    f.write(app_yaml)

print("✅ Created app.yaml")

# COMMAND ----------
print("=" * 80)
print("DEPLOYMENT COMPLETE!")
print("=" * 80)
print(f"\n✅ Model Registered: {CATALOG}.{SCHEMA}.{MODEL_NAME} (version {registered_model.version})")
print(f"✅ Endpoint Deployed: {ENDPOINT_NAME}")
print(f"✅ Databricks App Created: /Workspace/Users/<your_email>/battery-trading-app")
print(f"\n📋 NEXT STEPS:")
print(f"1. Go to Databricks Apps in your workspace")
print(f"2. Click 'Create App'")
print(f"3. Select source: /Workspace/Users/<your_email>/battery-trading-app")
print(f"4. Launch and share with EA trading team!")
```

***

## Success Criteria & Demo Script

### Demo Flow (November 11)

**1. Introduction (2 min)**
- Show architecture diagram: PDF → Vector Search + Delta Tables → Agent → Streamlit UI
- Explain Mosaic AI Agent Framework orchestration

**2. Live Demo (5 min)**

Query sequence:
```
User: "What is the current SoC for RESS2?"
→ Agent uses get_battery_status tool → Shows live telemetry

User: "How is throughput calculated and why does it matter?"
→ Agent uses search_battery_docs tool → Explains from PDF

User: "What's the throughput limit for DPNTBESS and what's its current SoC?"
→ Agent uses BOTH tools → Combines technical spec with live data

User: "Show me revenue performance for all batteries in last 24 hours"
→ Agent uses get_battery_revenue tool → Financial analysis
```

**3. Show Agent Reasoning (2 min)**
- Open MLflow trace to show tool selection logic
- Highlight how agent chooses between RAG vs SQL

**4. Evaluation Results (1 min)**
- Show Agent Evaluation dashboard
- Highlight retrieval precision and response quality scores

***

## Timeline

**Day 1 (Nov 9):**
- Morning: Run notebooks 01 & 02 (data prep + agent development)
- Afternoon: Test agent, iterate on prompts

**Day 2 (Nov 10):**
- Morning: Run notebook 03 (evaluation)
- Afternoon: Run notebook 04 (deployment), create Databricks App

**Day 3 (Nov 11):**
- Morning: Final testing, prepare demo script
- Afternoon: **DEMO TO EA TRADING TEAM**

---

## Key Differentiators to Highlight

1. **Unified Intelligence**: One interface for both structured (Genie/SQL) and unstructured (RAG/docs) data[1][2]
2. **Mosaic AI Agent Framework**: Production-grade orchestration with MLflow tracking[3][2]
3. **Unity Catalog Governance**: All tools governed, lineage tracked[4][3]
4. **Agent Evaluation**: Built-in quality metrics (retrieval, groundedness, relevance)[5][1]
5. **Extends Existing Infrastructure**: Leverages your AEMO metadata automation, complements Genie rooms[6]

This positions EA ahead of the curve on Daniel Morse's Agentic AI roadmap while demonstrating concrete ROI through faster insights and reduced manual documentation lookup.[7][8]

[1](https://docs.databricks.com/aws/en/generative-ai/tutorials/agent-framework-notebook)
[2](https://www.databricks.com/product/machine-learning/retrieval-augmented-generation)
[3](https://docs.databricks.com/aws/en/generative-ai/tutorials/agent-quickstart)
[4](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/agent-tool)
[5](https://arize.com/blog/harnessing-databricks-mosaic-ai-agent-framework-and-arize-for-next-level-genai-applications/)
[6](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/28996964/5c971013-b932-4c10-b72a-03882b0b1b9d/battery.pdf)
[7](https://www.databricks.com/blog/build-autonomous-ai-assistant-mosaic-ai-agent-framework)
[8](https://www.databricks.com/resources/demos/videos/ai-agents-on-mosaic-ai-in-5-minutes)
[9](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/tutorials/agent-quickstart)
[10](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/agent-framework/code-interpreter-tools)
[11](https://www.youtube.com/watch?v=0X6kJzX-CgA)
