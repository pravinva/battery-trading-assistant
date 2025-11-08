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

