# Battery Trading Agent Implementation
# This module creates the LangGraph agent with tools

from langchain_community.chat_models import ChatDatabricks
from langgraph.prebuilt import create_react_agent
from agent.tools import create_tools
from agent.config import LLM_ENDPOINT

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


def create_agent(spark, vsc=None, temperature=0.1):
    """
    Create the battery trading agent.
    
    Args:
        spark: SparkSession instance
        vsc: VectorSearchClient instance (optional)
        temperature: LLM temperature (default 0.1)
    
    Returns:
        LangGraph agent instance
    """
    # Initialize LLM
    llm = ChatDatabricks(endpoint=LLM_ENDPOINT, temperature=temperature)
    
    # Create tools
    tools = create_tools(spark, vsc)
    
    # Create LangGraph agent
    agent = create_react_agent(
        model=llm,
        tools=tools,
        state_modifier=SYSTEM_PROMPT
    )
    
    return agent

