#!/usr/bin/env python3
"""
Battery Trading Agent Development - MCP Integration Version
Uses Genie MCP server instead of direct API calls
"""

import warnings
import os

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
os.environ["PYTHONWARNINGS"] = "ignore"

import mlflow
import threading
from databricks.sdk import WorkspaceClient

# Try to import MCP client - fallback if not available
try:
    from databricks.langchain.mcp import DatabricksMCPClient
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("⚠️  databricks-langchain not installed. Install with: pip install databricks-langchain")
    print("   Falling back to direct Genie API calls")

try:
    from databricks_langchain import ChatDatabricks
except ImportError:
    from langchain_community.chat_models import ChatDatabricks
from databricks.vector_search.client import VectorSearchClient
try:
    from langchain.agents import create_react_agent
except ImportError:
    from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from typing import Annotated
import os

# Configuration
CATALOG = "ea_trading"
SCHEMA = "battery_trading"
ENDPOINT_NAME = "one-env-shared-endpoint-10"
INDEX_NAME = f"{CATALOG}.{SCHEMA}.battery_docs_index"
LLM_ENDPOINT = "databricks-claude-sonnet-4-5"

# MCP Configuration
USE_MCP = os.environ.get("USE_GENIE_MCP", "false").lower() == "true"
GENIE_MCP_SERVER_URL = os.environ.get("GENIE_MCP_SERVER_URL", None)

# Initialize clients
w = WorkspaceClient()
vsc = VectorSearchClient(disable_notice=True)

# Get warehouse ID for SQL execution
warehouses = list(w.warehouses.list())
if not warehouses:
    raise ValueError("No SQL warehouses found. Please create one in Databricks.")
warehouse_id = warehouses[0].id
print(f"✅ Using SQL warehouse: {warehouses[0].name} (ID: {warehouse_id})")

# Initialize MCP client if available and enabled
_mcp_client = None
if MCP_AVAILABLE and USE_MCP:
    try:
        # For managed MCP servers, connection is handled automatically
        # Server URL may be workspace-specific or use default managed server
        if GENIE_MCP_SERVER_URL:
            _mcp_client = DatabricksMCPClient(server_url=GENIE_MCP_SERVER_URL)
        else:
            # Try to use default managed Genie MCP server
            # Note: Exact initialization depends on databricks-langchain implementation
            # This may need adjustment based on actual API
            _mcp_client = DatabricksMCPClient()
        print("✅ Genie MCP client initialized")
    except Exception as e:
        print(f"⚠️  Failed to initialize MCP client: {e}")
        print("   Falling back to direct Genie API calls")
        _mcp_client = None
        USE_MCP = False
elif USE_MCP and not MCP_AVAILABLE:
    print("⚠️  USE_GENIE_MCP=true but databricks-langchain not installed")
    print("   Install with: pip install databricks-langchain")
    print("   Falling back to direct Genie API calls")
    USE_MCP = False

# Lazy MLflow setup - only when needed, non-blocking
_mlflow_initialized = False
_mlflow_lock = threading.Lock()

def init_mlflow_lazy():
    """Initialize MLflow lazily and non-blocking"""
    global _mlflow_initialized
    if _mlflow_initialized:
        return
    
    with _mlflow_lock:
        if _mlflow_initialized:
            return
        try:
            mlflow.set_registry_uri("databricks-uc")
            current_user = os.environ.get("USER", "unknown")
            mlflow.set_experiment(f"/Users/{current_user}/battery_agent_dev")
            _mlflow_initialized = True
        except Exception:
            # Silently fail - MLflow is optional
            pass

print("=" * 80)
print("Battery Trading Agent Development - MCP Integration")
print(f"MCP Mode: {'ENABLED' if USE_MCP else 'DISABLED' (fallback to direct API)}")
print("=" * 80)

# ... rest of the file will be updated to use MCP when available ...

