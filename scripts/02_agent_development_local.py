#!/usr/bin/env python3
"""
Battery Trading Agent Development - Local Execution
Run this script locally to build and test the agent
Supports both MCP server and direct Genie API approaches
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
# Based on: https://docs.databricks.com/aws/en/generative-ai/mcp/managed-mcp
try:
    from databricks_mcp import DatabricksMCPClient
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("⚠️  databricks-mcp not installed. Install with: pip install databricks-mcp")

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
import json
from json import JSONDecodeError

# Configuration
CATALOG = "ea_trading"
SCHEMA = "battery_trading"
ENDPOINT_NAME = "one-env-shared-endpoint-10"
INDEX_NAME = f"{CATALOG}.{SCHEMA}.battery_docs_index"
LLM_ENDPOINT = "databricks-claude-sonnet-4-5"

# Configuration for Genie
# Try to get from environment variable, or use default if set
GENIE_ROOM_ID = os.environ.get("GENIE_ROOM_ID", None)
if not GENIE_ROOM_ID:
    # Try to read from a config file or use a default
    # Default Genie room ID (can be overridden with environment variable)
    GENIE_ROOM_ID = "01f0bca10415147a91fe3c98f80e596e"  # Battery Trading Agent space

# MCP Configuration
USE_MCP = os.environ.get("USE_GENIE_MCP", "false").lower() == "true"
GENIE_MCP_SERVER_URL = os.environ.get("GENIE_MCP_SERVER_URL", None)

# Initialize clients
w = WorkspaceClient()
vsc = VectorSearchClient(disable_notice=True)

# Initialize MCP client if available and enabled
# Based on: https://docs.databricks.com/aws/en/generative-ai/mcp/managed-mcp
# Genie MCP server URL pattern: https://<workspace-hostname>/api/2.0/mcp/genie/{genie_space_id}
_mcp_client = None
_mcp_server_url = None

if MCP_AVAILABLE and USE_MCP:
    try:
        # Get workspace hostname for MCP server URL
        workspace_hostname = w.config.host
        
        # Build Genie MCP server URL
        # Pattern: https://<workspace-hostname>/api/2.0/mcp/genie/{genie_space_id}
        if GENIE_MCP_SERVER_URL:
            _mcp_server_url = GENIE_MCP_SERVER_URL
        else:
            # Use default managed Genie MCP server URL pattern
            _mcp_server_url = f"{workspace_hostname}/api/2.0/mcp/genie/{GENIE_ROOM_ID}"
        
        # Initialize MCP client with workspace_client for authentication
        # Based on docs: DatabricksMCPClient(server_url=..., workspace_client=...)
        _mcp_client = DatabricksMCPClient(server_url=_mcp_server_url, workspace_client=w)
        print(f"✅ Genie MCP client initialized")
        print(f"   MCP Server URL: {_mcp_server_url}")
        
        # Try to discover available tools
        try:
            tools = _mcp_client.list_tools()
            print(f"   Discovered {len(tools)} tools: {[t.name for t in tools]}")
        except Exception as e:
            print(f"   ⚠️  Could not list tools: {e}")
            
    except Exception as e:
        print(f"❌ Failed to initialize MCP client: {e}")
        print("   Pure MCP mode requires successful MCP client initialization")
        raise Exception(
            f"Failed to initialize Genie MCP client: {e}\n\n"
            f"Please ensure:\n"
            f"1. MCP server is enabled in workspace (Agents → MCP Servers)\n"
            f"2. Genie MCP server is available\n"
            f"3. Genie space ID is correct: {GENIE_ROOM_ID}\n"
            f"4. You have permissions to use the MCP server\n"
            f"5. Workspace hostname: {workspace_hostname}\n"
            f"6. MCP Server URL: {_mcp_server_url if '_mcp_server_url' in locals() else 'N/A'}\n\n"
            f"If you want to use direct Genie API instead, set USE_GENIE_MCP=false"
        )
elif USE_MCP and not MCP_AVAILABLE:
    print("❌ USE_GENIE_MCP=true but databricks-mcp not installed")
    print("   Install with: pip install databricks-mcp")
    print("   Pure MCP mode requires databricks-mcp - cannot fall back to direct API")
    raise ImportError(
        "databricks-mcp is required for MCP mode. "
        "Install with: pip install databricks-mcp\n"
        "Or disable MCP mode by setting USE_GENIE_MCP=false"
    )

if USE_MCP:
    print("🔌 Using Genie MCP server for queries")
else:
    print("🔌 Using direct Genie API for queries")

# Get warehouse ID for SQL execution
warehouses = list(w.warehouses.list())
if not warehouses:
    raise ValueError("No SQL warehouses found. Please create one in Databricks.")
warehouse_id = warehouses[0].id
print(f"✅ Using SQL warehouse: {warehouses[0].name} (ID: {warehouse_id})")

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
print("Battery Trading Agent Development")
print("=" * 80)

def format_response_text(text):
    """Clean and format response text to ensure proper spacing around numbers and currency"""
    if not text:
        return text
    
    import re
    # Fix spacing around currency symbols and numbers
    # Add space before $ if it's attached to a word: "revenue$100" -> "revenue $100"
    text = re.sub(r'([a-zA-Z])(\$)', r'\1 \2', text)
    # Add space after $number before letter: "$100revenue" -> "$100 revenue"
    text = re.sub(r'(\$[\d,]+\.?\d*)([a-zA-Z])', r'\1 \2', text)
    
    # Fix spacing around negative numbers: "-700to" -> "-700 to"
    text = re.sub(r'(-[\d,]+\.?\d*)([a-zA-Z])', r'\1 \2', text)
    # Fix spacing before negative numbers: "exceeding-" -> "exceeding -"
    text = re.sub(r'([a-zA-Z])(-[\d,]+\.?\d*)', r'\1 \2', text)
    
    # Fix spacing around numbers: "700to" -> "700 to", "650exceeding" -> "650 exceeding"
    text = re.sub(r'(\d+)([a-zA-Z])', r'\1 \2', text)  # Number followed by letter
    text = re.sub(r'([a-zA-Z])(\d+)', r'\1 \2', text)  # Letter followed by number
    
    # Fix specific patterns like "700togainsexceeding650" -> "700 to gains exceeding 650"
    text = re.sub(r'(\d+)(to)([a-zA-Z]+)', r'\1 \2 \3', text, flags=re.IGNORECASE)
    text = re.sub(r'([a-zA-Z]+)(exceeding)(\d+)', r'\1 \2 \3', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)(exceeding)(\d+)', r'\1 \2 \3', text, flags=re.IGNORECASE)
    
    # Fix multiple spaces
    text = re.sub(r' +', ' ', text)
    
    # Fix spacing around common patterns
    text = re.sub(r'(\d+)\s*(to|and|or)\s*([a-zA-Z])', r'\1 \2 \3', text)
    text = re.sub(r'([a-zA-Z])\s*(to|and|or)\s*(\d+)', r'\1 \2 \3', text)
    
    return text.strip()

# Helper function to create Plotly charts from query data
def create_plotly_chart(query_data, columns, question):
    """Create a Plotly chart from query results based on the question context"""
    try:
        import plotly.graph_objects as go
        import plotly.express as px
        import pandas as pd
        import json
        
        if not query_data or len(query_data) == 0:
            return None
        
        # Convert to DataFrame
        df = None
        if isinstance(query_data, list):
            if isinstance(query_data[0], (list, tuple)):
                # Array of arrays
                # CRITICAL: Use provided columns, or generate better defaults
                if columns and len(columns) > 0:
                    df = pd.DataFrame(query_data, columns=columns)
                else:
                    # Generate better default column names based on data
                    num_cols = len(query_data[0])
                    default_cols = []
                    for i in range(num_cols):
                        # Try to infer column type from first few values
                        sample_vals = [row[i] for row in query_data[:5] if i < len(row)]
                        if any('date' in str(v).lower() or 'time' in str(v).lower() for v in sample_vals if v):
                            default_cols.append('date' if i == 0 else f'value_{i}')
                        elif any(isinstance(v, (int, float)) or (isinstance(v, str) and v.replace('.', '').replace('-', '').isdigit()) for v in sample_vals if v):
                            default_cols.append(f'value_{i}' if i > 0 else 'index')
                        else:
                            default_cols.append(f'column_{i}')
                    df = pd.DataFrame(query_data, columns=default_cols)
                    print(f"DEBUG: Using default columns: {default_cols}")
            elif isinstance(query_data[0], dict):
                # Array of dicts
                df = pd.DataFrame(query_data)
            else:
                return None
        elif isinstance(query_data, dict):
            if 'rows' in query_data:
                df = pd.DataFrame(query_data['rows'], columns=columns if columns else None)
            elif 'data' in query_data:
                df = pd.DataFrame(query_data['data'])
            else:
                return None
        
        if df is None or df.empty:
            return None
        
        # Debug: Print column names
        print(f"DEBUG: DataFrame columns: {list(df.columns)}")
        
        # Convert string numeric columns to actual numbers
        # BUT preserve date/timestamp columns - don't convert them to numeric
        # This is important because SQL results often come as strings
        date_cols = [col for col in df.columns if any(term in col.lower() for term in ['date', 'time', 'timestamp', 'interval'])]
        for col in df.columns:
            # Skip date columns - keep them as strings/datetime
            if col in date_cols:
                # Try to convert to datetime if it's a string
                if df[col].dtype == 'object':
                    try:
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                    except:
                        pass  # Keep as string if conversion fails
                continue
            
            # Try to convert to numeric, keeping original if it fails
            numeric_series = pd.to_numeric(df[col], errors='coerce')
            # If conversion succeeded for at least some values, use it
            if not numeric_series.isna().all():
                df[col] = numeric_series
        
        # Determine chart type based on question and data
        question_lower = question.lower()
        chart_type = None
        
        # Time series chart
        # Check for time-related keywords OR if we have date/time columns
        has_time_keywords = any(word in question_lower for word in ['over time', 'trend', 'history', 'last', 'hour', 'day', 'week', 'by day', 'by hour'])
        time_cols = [col for col in df.columns if any(term in col.lower() for term in ['time', 'date', 'timestamp', 'interval'])]
        
        if has_time_keywords or time_cols:
            # Look for timestamp/date column
            if time_cols:
                chart_type = 'line'
                x_col = time_cols[0]
                # Find numeric columns for y-axis
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                if numeric_cols:
                    y_col = numeric_cols[0]
                    # Generate better title from question or column names
                    title = f"{y_col.replace('_', ' ').title()} Over Time"
                    if 'revenue' in question_lower and 'hourly' in question_lower:
                        title = "Maximum Hourly Revenue by Day"
                    elif 'revenue' in question_lower:
                        title = "Revenue Over Time"
                    elif 'soc' in question_lower or 'state of charge' in question_lower:
                        title = "State of Charge Over Time"
                    
                    # Create line chart with proper line rendering, colors, and axis labels
                    x_label = x_col.replace('_', ' ').title()
                    y_label = y_col.replace('_', ' ').title()
                    fig = px.line(df, x=x_col, y=y_col, 
                                 title=title,
                                 labels={x_col: x_label, y_col: y_label},
                                 color_discrete_sequence=px.colors.qualitative.Set1)
                    # Ensure lines are visible, not just markers
                    fig.update_traces(mode='lines+markers', line=dict(width=2))
                    # Explicitly set axis titles to ensure they're preserved
                    fig.update_xaxes(title_text=x_label)
                    fig.update_yaxes(title_text=y_label)
                else:
                    return None
            else:
                # No time column found, but question suggests time series
                # Use first column as x-axis and first numeric as y-axis
                if len(df.columns) >= 2:
                    x_col = df.columns[0]
                    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                    if numeric_cols:
                        y_col = numeric_cols[0]
                        chart_type = 'line'
                        # Generate better title from question or column names
                        title = f"{y_col.replace('_', ' ').title()} by {x_col.replace('_', ' ').title()}"
                        if 'revenue' in question_lower and 'hourly' in question_lower:
                            title = "Maximum Hourly Revenue by Day"
                        elif 'revenue' in question_lower:
                            title = "Revenue Over Time"
                        elif 'soc' in question_lower or 'state of charge' in question_lower:
                            title = "State of Charge Over Time"
                        
                        x_label = x_col.replace('_', ' ').title()
                        y_label = y_col.replace('_', ' ').title()
                        fig = px.line(df, x=x_col, y=y_col, 
                                     title=title,
                                     labels={x_col: x_label, y_col: y_label},
                                     color_discrete_sequence=px.colors.qualitative.Set1)
                        # Ensure lines are visible
                        fig.update_traces(mode='lines+markers', line=dict(width=2))
                        # Explicitly set axis titles
                        fig.update_xaxes(title_text=x_label)
                        fig.update_yaxes(title_text=y_label)
                    else:
                        return None
                else:
                    # Single column - use index as x-axis (shouldn't happen for time series)
                    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                    if len(numeric_cols) >= 1:
                        chart_type = 'line'
                        y_col = numeric_cols[0]
                        # Generate better title
                        title = f"{y_col.replace('_', ' ').title()} Over Time"
                        if 'revenue' in question_lower and 'hourly' in question_lower:
                            title = "Maximum Hourly Revenue by Day"
                        elif 'revenue' in question_lower:
                            title = "Revenue Over Time"
                        
                        # Use first non-numeric column as x-axis if available, otherwise use index
                        non_numeric_cols = [col for col in df.columns if col not in numeric_cols]
                        if non_numeric_cols:
                            x_col = non_numeric_cols[0]
                            x_label = x_col.replace('_', ' ').title()
                            fig = px.line(df, x=x_col, y=y_col, 
                                         title=title,
                                         labels={x_col: x_label, y_col: y_col.replace('_', ' ').title()},
                                         color_discrete_sequence=px.colors.qualitative.Set1)
                        else:
                            x_label = 'Day' if 'day' in question_lower else 'Index'
                            y_label = y_col.replace('_', ' ').title()
                            fig = px.line(df, y=y_col, 
                                         title=title,
                                         labels={'index': x_label, y_col: y_label},
                                         color_discrete_sequence=px.colors.qualitative.Set1)
                        # Ensure lines are visible
                        fig.update_traces(mode='lines+markers', line=dict(width=2))
                        # Explicitly set axis titles
                        fig.update_xaxes(title_text=x_label)
                        fig.update_yaxes(title_text=y_label)
                    else:
                        return None
        
        # Bar chart for comparisons
        elif any(word in question_lower for word in ['compare', 'comparison', 'by battery', 'each battery', 'across', 'revenue']):
            # Look for categorical column (battery_id, etc.)
            cat_cols = [col for col in df.columns if any(term in col.lower() for term in ['battery', 'id', 'name', 'site'])]
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            
            if cat_cols and numeric_cols:
                chart_type = 'bar'
                x_col = cat_cols[0]
                y_col = numeric_cols[0]
                # Create bar chart with colors
                fig = px.bar(df, x=x_col, y=y_col, 
                            title=f"{y_col.replace('_', ' ').title()} by {x_col.replace('_', ' ').title()}",
                            color=x_col,
                            color_discrete_sequence=px.colors.qualitative.Set2)
            elif len(df.columns) >= 2:
                chart_type = 'bar'
                # Try to identify which column is numeric
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                if numeric_cols:
                    y_col = numeric_cols[0]
                    x_col = [col for col in df.columns if col != y_col][0]
                else:
                    x_col = df.columns[0]
                    y_col = df.columns[1]
                    # Force convert y to numeric
                    df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
                # Create bar chart with colors
                fig = px.bar(df, x=x_col, y=y_col, 
                            title=f"{y_col.replace('_', ' ').title()} by {x_col.replace('_', ' ').title()}",
                            color=x_col,
                            color_discrete_sequence=px.colors.qualitative.Set2)
            else:
                return None
        
        # Pie chart for distribution
        elif any(word in question_lower for word in ['distribution', 'proportion', 'percentage', 'share']):
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            cat_cols = [col for col in df.columns if col not in numeric_cols]
            
            if cat_cols and numeric_cols:
                chart_type = 'pie'
                fig = px.pie(df, names=cat_cols[0], values=numeric_cols[0], 
                            title=f"Distribution of {numeric_cols[0].replace('_', ' ').title()}",
                            color_discrete_sequence=px.colors.qualitative.Set3)
            else:
                return None
        
        # Default: bar chart for first two columns (most common case)
        else:
            if len(df.columns) >= 2:
                chart_type = 'bar'
                # Try to identify which column is numeric
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                if numeric_cols:
                    y_col = numeric_cols[0]
                    x_col = [col for col in df.columns if col != y_col][0]
                else:
                    x_col = df.columns[0]
                    y_col = df.columns[1]
                    # Force convert y to numeric
                    df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
                # Create bar chart with colors
                fig = px.bar(df, x=x_col, y=y_col, 
                            title=f"{y_col.replace('_', ' ').title()} by {x_col.replace('_', ' ').title()}",
                            color=x_col,
                            color_discrete_sequence=px.colors.qualitative.Set2)
            elif len(df.columns) == 1 and len(df) > 1:
                # Single column with multiple rows - create simple bar chart
                chart_type = 'bar'
                col = df.columns[0]
                # Convert to numeric if possible
                df[col] = pd.to_numeric(df[col], errors='coerce')
                fig = px.bar(df, y=col, 
                            title=f"{col.replace('_', ' ').title()}",
                            color_discrete_sequence=px.colors.qualitative.Set2)
            else:
                return None
        
        # Convert to JSON for embedding in response
        # Extract only essential, JSON-serializable attributes from traces
        import numpy as np
        
        def convert_to_json_serializable(obj):
            """Convert numpy arrays and other non-serializable objects to JSON-compatible types"""
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, (np.integer, np.floating)):
                return float(obj)
            elif isinstance(obj, pd.Timestamp):
                return str(obj)
            elif isinstance(obj, dict):
                return {k: convert_to_json_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_json_serializable(item) for item in obj]
            elif isinstance(obj, tuple):
                return [convert_to_json_serializable(item) for item in obj]
            # Skip Plotly-specific objects that aren't serializable
            elif hasattr(obj, '__class__') and 'plotly' in str(type(obj)).lower():
                return None
            return obj
        
        # Build chart data structure manually - only include essential attributes
        chart_data = {
            'data': [],
            'layout': {}
        }
        
        # Essential trace attributes to extract
        essential_trace_attrs = ['x', 'y', 'type', 'mode', 'name', 'marker', 'line', 
                                'hovertemplate', 'showlegend', 'legendgroup', 'orientation']
        
        # Extract data from each trace - only essential attributes
        for trace in fig.data:
            trace_dict = {}
            for attr in essential_trace_attrs:
                try:
                    value = getattr(trace, attr, None)
                    if value is not None:
                        converted = convert_to_json_serializable(value)
                        if converted is not None:
                            trace_dict[attr] = converted
                except:
                    pass
            
            chart_data['data'].append(trace_dict)
        
        # Essential layout attributes
        essential_layout_attrs = ['title', 'xaxis', 'yaxis', 'legend', 'template', 
                                 'colorway', 'colorscale', 'hovermode']
        
        # Extract layout data - only essential attributes
        layout_dict = {}
        for attr in essential_layout_attrs:
            try:
                value = getattr(fig.layout, attr, None)
                if value is not None:
                    converted = convert_to_json_serializable(value)
                    if converted is not None:
                        layout_dict[attr] = converted
            except:
                pass
        
        # Handle title specially (it's a Title object)
        if hasattr(fig.layout, 'title') and fig.layout.title:
            if hasattr(fig.layout.title, 'text'):
                layout_dict['title'] = {'text': str(fig.layout.title.text)}
        
        # Ensure xaxis and yaxis have proper titles
        # Plotly Express sets these in labels, but we need to preserve them in layout
        if hasattr(fig.layout, 'xaxis') and fig.layout.xaxis:
            xaxis_dict = {}
            if hasattr(fig.layout.xaxis, 'title') and fig.layout.xaxis.title:
                if hasattr(fig.layout.xaxis.title, 'text'):
                    xaxis_dict['title'] = {'text': str(fig.layout.xaxis.title.text)}
            if not xaxis_dict.get('title'):
                # Try to get from labels if title wasn't set
                if hasattr(fig, 'data') and len(fig.data) > 0:
                    # Get x-axis label from first trace if available
                    pass  # Will use default from column name
            if xaxis_dict:
                layout_dict['xaxis'] = xaxis_dict
        
        if hasattr(fig.layout, 'yaxis') and fig.layout.yaxis:
            yaxis_dict = {}
            if hasattr(fig.layout.yaxis, 'title') and fig.layout.yaxis.title:
                if hasattr(fig.layout.yaxis.title, 'text'):
                    yaxis_dict['title'] = {'text': str(fig.layout.yaxis.title.text)}
            if yaxis_dict:
                layout_dict['yaxis'] = yaxis_dict
        
        chart_data['layout'] = layout_dict
        
        # Return chart_data dict directly - don't serialize it yet
        # Serialization will happen when embedding in the response
        return {
            'type': chart_type,
            'json': chart_data,  # Return the dict with 'data' and 'layout', not a JSON string
            'title': fig.layout.title.text if hasattr(fig.layout, 'title') and fig.layout.title and hasattr(fig.layout.title, 'text') else 'Chart'
        }
        
    except Exception as e:
        print(f"DEBUG: Error creating Plotly chart: {e}")
        import traceback
        traceback.print_exc()
        return None

# Helper function to execute SQL
def execute_sql(query: str) -> list:
    """Execute SQL query and return results as list of dicts"""
    from databricks.sdk.service.sql import StatementState
    
    result = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=query,
        wait_timeout="30s"
    )
    
    if result.status.state != StatementState.SUCCEEDED:
        error_msg = str(result.status)
        raise Exception(f"SQL execution failed: {error_msg}")
    
    # Convert result to list of dicts
    if result.result and result.result.data_array:
        # Get column names from result structure
        columns = []
        if hasattr(result.result, 'manifest') and result.result.manifest:
            if hasattr(result.result.manifest, 'schema') and result.result.manifest.schema:
                if hasattr(result.result.manifest.schema, 'columns'):
                    columns = [col.name for col in result.result.manifest.schema.columns]
        
        # If no columns found, try alternative approach
        if not columns:
            # Check if result has column info directly
            if hasattr(result, 'manifest') and result.manifest:
                if hasattr(result.manifest, 'schema') and result.manifest.schema:
                    if hasattr(result.manifest.schema, 'columns'):
                        columns = [col.name for col in result.manifest.schema.columns]
        
        # Last resort: use column indices
        if not columns and result.result.data_array:
            columns = [f"col_{i}" for i in range(len(result.result.data_array[0]))]
        
        rows = []
        for row_data in result.result.data_array:
            row_dict = {col: val for col, val in zip(columns, row_data)}
            rows.append(row_dict)
        return rows
    return []

# Tool 1: Vector Search for Technical Documentation
@tool
def search_battery_docs(
    query: Annotated[str, "The search query about battery technical specifications, processes, or architecture"]
) -> str:
    """Search battery integration documentation for technical information about 
    Wartsila BESS systems, PI integration, throughput calculations, SoC limits, 
    and AEMO bidding processes."""
    
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

# Tool 2: Query Current Battery Status
@tool
def get_battery_status(
    battery_id: Annotated[str, "Battery ID (RESS2, DPNTBESS, GANNBG1, GANNBL1) or 'all' for all batteries"] = "all"
) -> str:
    """Get current state of charge (SoC), capabilities, and telemetry for batteries.
    Returns latest reading with SoC in MWh and %, charge/discharge capabilities."""
    
    if battery_id.lower() == "all":
        query = f"""
            SELECT battery_id, 
                   ROUND(soc_mwh, 2) as soc_mwh,
                   ROUND(soc_percent, 1) as soc_percent,
                   ROUND(capability_charge_mw, 1) as charge_cap_mw,
                   ROUND(capability_discharge_mw, 1) as discharge_cap_mw,
                   reading_age_minutes,
                   timestamp
            FROM {CATALOG}.{SCHEMA}.battery_telemetry
            WHERE timestamp = (SELECT MAX(timestamp) FROM {CATALOG}.{SCHEMA}.battery_telemetry)
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
            FROM {CATALOG}.{SCHEMA}.battery_telemetry
            WHERE battery_id = '{battery_id.upper()}'
              AND timestamp = (SELECT MAX(timestamp) FROM {CATALOG}.{SCHEMA}.battery_telemetry)
        """
    
    result = execute_sql(query)
    
    if not result:
        return f"No telemetry data found for battery: {battery_id}"
    
    output = []
    for row in result:
        output.append(
            f"{row['battery_id']}: {row['soc_mwh']} MWh ({row['soc_percent']}% SoC), "
            f"Charge: {row['charge_cap_mw']} MW, Discharge: {row['discharge_cap_mw']} MW, "
            f"Reading age: {row['reading_age_minutes']} min (as of {row['timestamp']})"
        )
    
    return "\n".join(output)

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
        FROM {CATALOG}.{SCHEMA}.battery_dispatch
        WHERE battery_id = '{battery_id.upper()}'
          AND dispatch_interval >= current_timestamp() - INTERVAL {hours} HOURS
        GROUP BY battery_id
    """
    
    result = execute_sql(query)
    
    if not result:
        return f"No dispatch data found for {battery_id} in last {hours} hours"
    
    row = result[0]
    # Convert to float if string
    revenue = float(row['total_revenue_dollar']) if isinstance(row['total_revenue_dollar'], str) else row['total_revenue_dollar']
    avg_price = float(row['avg_spot_price']) if isinstance(row['avg_spot_price'], str) else row['avg_spot_price']
    discharge = float(row['total_discharge_mwh']) if isinstance(row['total_discharge_mwh'], str) else row['total_discharge_mwh']
    charge = float(row['total_charge_mwh']) if isinstance(row['total_charge_mwh'], str) else row['total_charge_mwh']
    
    return (f"{row['battery_id']} performance (last {hours}h):\n"
            f"  Revenue: ${revenue:,.2f}\n"
            f"  Avg spot price: ${avg_price}/MWh\n"
            f"  Energy discharged: {discharge} MWh\n"
            f"  Energy charged: {charge} MWh\n"
            f"  Trading intervals: {row['num_intervals']}")

# Tool 4: Get Battery Asset Information
@tool
def get_battery_info(
    battery_id: Annotated[str, "Battery ID or 'all' for all batteries"] = "all"
) -> str:
    """Get battery asset information including capacity, location, partner, and commissioning details."""
    
    if battery_id.lower() == "all":
        query = f"SELECT * FROM {CATALOG}.{SCHEMA}.battery_assets ORDER BY battery_id"
    else:
        query = f"SELECT * FROM {CATALOG}.{SCHEMA}.battery_assets WHERE battery_id = '{battery_id.upper()}'"
    
    result = execute_sql(query)
    
    if not result:
        return f"No asset information found for: {battery_id}"
    
    output = []
    for row in result:
        output.append(
            f"{row['battery_id']} ({row['site_name']}):\n"
            f"  Location: {row['location']}\n"
            f"  Capacity: {row['nameplate_capacity_mw']} MW\n"
            f"  Storage: {row['max_soc_mwh']} MWh max, {row['min_soc_mwh']} MWh min\n"
            f"  Partner: {row['partner']}\n"
            f"  Commissioned: {row['commissioning_date']}"
        )
    
    return "\n\n".join(output)

# Global variable to store execution logs for UI display
_genie_execution_logs = []

def get_genie_logs():
    """Get and clear execution logs"""
    global _genie_execution_logs
    logs = _genie_execution_logs.copy()
    _genie_execution_logs = []  # Clear after reading
    return logs

def add_genie_log(entry):
    """Add a log entry"""
    global _genie_execution_logs
    import time
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    _genie_execution_logs.append(f"[{timestamp}] {entry}")

# Tool 5: Query Genie (MCP Server or Direct API)
@tool
def query_genie(
    question: Annotated[str, "A natural language question about battery data. Genie will generate and execute SQL automatically."]
) -> str:
    """Query Databricks Genie to answer questions using natural language.
    
    Use this tool for ALL SQL and data queries. Genie will automatically:
    - Understand your question
    - Generate appropriate SQL queries
    - Execute them against the battery trading database
    - Return formatted results
    
    Examples:
    - "Compare average SoC across all batteries in the last hour"
    - "Show me batteries with SoC below 50%"
    - "What's the total revenue across all batteries today?"
    - "Find batteries with the oldest telemetry readings"
    - "Which battery has the highest discharge capability?"
    
    Genie has access to all tables in {CATALOG}.{SCHEMA}:
    - battery_telemetry: Current SoC and capabilities
    - battery_dispatch: Dispatch history and revenue
    - battery_assets: Asset specifications
    - battery_documents: Document metadata
    
    Returns Genie's response with query results.
    
    Pure MCP implementation when USE_GENIE_MCP=true (no fallback to direct API).
    Uses direct Genie API when USE_GENIE_MCP=false."""
    
    # Check if this query should have a visualization - ONLY if explicitly requested
    import re
    # Explicit visualization keywords only
    explicit_viz_keywords = ['plot', 'chart', 'graph', 'visualize', 'visualization', 'show me a', 'display a', 'create a']
    is_visualization_request = any(keyword in question.lower() for keyword in explicit_viz_keywords)
    
    # Initialize chart_data and result storage at function level to avoid scoping issues
    chart_data = None
    result_obj = None  # Store result object for column extraction
    
    # Initialize debug log - OPTIMIZED: Only write if DEBUG env var is set
    debug_log_path = "/tmp/genie_debug.log"
    import time
    import sys
    
    # Only do extensive debug logging if DEBUG environment variable is set
    DEBUG_MODE = os.environ.get("DEBUG", "false").lower() == "true"
    
    if DEBUG_MODE:
        log_entry = f"\n{'='*80}\nNEW QUERY_GENIE CALL - {time.strftime('%Y-%m-%d %H:%M:%S')}\nQuestion: {question}\nMode: {'MCP' if USE_MCP else 'Direct API'}\nGENIE_ROOM_ID: {GENIE_ROOM_ID if 'GENIE_ROOM_ID' in globals() else 'NOT SET'}\n{'='*80}\n"
        print(f"DEBUG: query_genie CALLED - Mode: {'MCP' if USE_MCP else 'Direct API'}", flush=True)
        print(f"DEBUG: Question: {question}", flush=True)
    else:
        print(f"DEBUG: query_genie ({'MCP' if USE_MCP else 'Direct API'}) - {question[:50]}...", flush=True)
    
    try:
        if not GENIE_ROOM_ID:
            return f"""Genie space ID not configured. 

To use Genie:
1. Create a Genie space named 'battery-trading-agent' in Databricks UI
2. Run: python3 scripts/create_genie_room.py
3. Set environment variable: export GENIE_ROOM_ID=\"<space_id>\"

Question asked: {question}"""
        
        # Pure MCP implementation - no fallback
        if USE_MCP:
            if not _mcp_client:
                raise Exception(
                    f"MCP client not initialized. Please ensure:\n"
                    f"1. databricks-mcp is installed: pip install databricks-mcp\n"
                    f"2. MCP server is enabled in workspace (Agents → MCP Servers)\n"
                    f"3. Genie space ID is correct: {GENIE_ROOM_ID}\n"
                    f"4. You have permissions to use the MCP server"
                )
            return query_genie_via_mcp(question, is_visualization_request)
        else:
            # Direct Genie API (when MCP is not enabled)
            return query_genie_via_direct_api(question, is_visualization_request)
    
    except Exception as e:
        error_msg = f"Genie API Error: {str(e)}\n\nPlease ensure:\n1. Genie space 'battery-trading-agent' exists\n2. GENIE_ROOM_ID is set correctly\n3. You have permissions to use the space\n4. Genie API is enabled in your workspace\n\nQuestion asked: {question}"
        raise Exception(error_msg)

def query_genie_via_mcp(question: str, is_visualization_request: bool) -> str:
    """Query Genie via MCP server
    
    Based on: https://docs.databricks.com/aws/en/generative-ai/mcp/managed-mcp
    Genie MCP server exposes tools that can be discovered via list_tools()
    """
    DEBUG_MODE = os.environ.get("DEBUG", "false").lower() == "true"
    
    # Initialize variables
    chart_data = None
    genie_response = None
    sql_query = None
    query_data = None
    
    try:
        if DEBUG_MODE:
            print(f"DEBUG: Using MCP server to query Genie")
            print(f"DEBUG: MCP Server URL: {_mcp_server_url}")
        
        # Discover available tools from MCP server
        add_genie_log(f"🔍 Discovering MCP tools from server...")
        tools = _mcp_client.list_tools()
        tool_names = [t.name for t in tools]
        add_genie_log(f"✅ Found {len(tools)} MCP tools: {', '.join(tool_names)}")
        
        if DEBUG_MODE:
            print(f"DEBUG: Using MCP server to query Genie")
            print(f"DEBUG: MCP Server URL: {_mcp_server_url}")
            print(f"DEBUG: Available MCP tools: {tool_names}")
        
        # Find the Genie query tool
        # Tool name pattern: query_space_{genie_space_id}
        genie_tool = None
        expected_tool_name = f"query_space_{GENIE_ROOM_ID}"
        
        for tool in tools:
            if tool.name == expected_tool_name or tool.name.startswith("query_space_"):
                genie_tool = tool
                break
        
        if not genie_tool:
            # Fallback: look for any tool with "query" in the name
            for tool in tools:
                if "query" in tool.name.lower():
                    genie_tool = tool
                    break
        
        if not genie_tool:
            raise Exception(f"No Genie query tool found. Available tools: {[t.name for t in tools]}")
        
        if DEBUG_MODE:
            print(f"DEBUG: Using tool: {genie_tool.name}")
            print(f"DEBUG: Tool description: {genie_tool.description}")
            print(f"DEBUG: Tool input schema: {genie_tool.inputSchema}")
        
        # Call the Genie tool via MCP
        # Based on discovery, the tool expects: {"query": "..."} and optionally {"conversation_id": "..."}
        tool_args = {"query": question}
        
        if DEBUG_MODE:
            print(f"DEBUG: Calling tool with args: {tool_args}")
        
        # Call the tool
        add_genie_log(f"📞 Calling MCP tool: {genie_tool.name}")
        add_genie_log(f"📋 Tool arguments: {str(tool_args)}")
        result = _mcp_client.call_tool(genie_tool.name, tool_args)
        add_genie_log(f"✅ MCP tool call successful")
        
        if DEBUG_MODE:
            print(f"DEBUG: MCP tool result type: {type(result)}")
            print(f"DEBUG: MCP tool result: {str(result)[:500]}")
        
        # Extract response from MCP result
        # MCP tools return CallToolResult with .content attribute (list of TextContent)
        conversation_id = None
        message_id = None
        columns = None  # Initialize columns at function level
        
        if hasattr(result, 'content'):
            # CallToolResult object with content list
            content_list = result.content
            if content_list and len(content_list) > 0:
                # Get first text content
                first_content = content_list[0]
                if hasattr(first_content, 'text'):
                    content_text = first_content.text
                    if DEBUG_MODE:
                        print(f"DEBUG: Content text type: {type(content_text)}")
                        print(f"DEBUG: Content text preview: {content_text[:200]}")
                    
                    # Parse JSON response from Genie MCP server
                    try:
                        parsed = json.loads(content_text)
                        if DEBUG_MODE:
                            print(f"DEBUG: Parsed JSON keys: {list(parsed.keys()) if isinstance(parsed, dict) else 'Not a dict'}")
                        
                        if isinstance(parsed, dict):
                            # Extract conversation metadata first
                            conversation_id = parsed.get("conversationId") or parsed.get("conversation_id")
                            message_id = parsed.get("messageId") or parsed.get("message_id")
                            
                            # The "content" field is a JSON string that needs to be parsed again
                            content_json_str = parsed.get("content")
                            if content_json_str and isinstance(content_json_str, str):
                                try:
                                    # Parse the nested JSON content
                                    content_parsed = json.loads(content_json_str)
                                    if isinstance(content_parsed, dict):
                                        # Extract SQL query
                                        sql_query = content_parsed.get("query") or content_parsed.get("sql")
                                        
                                        # Extract query results from statement_response
                                        statement_response = content_parsed.get("statement_response")
                                        if statement_response and isinstance(statement_response, dict):
                                            # Get SQL query if not already extracted
                                            if not sql_query:
                                                sql_query = statement_response.get("query")
                                            
                                            # Extract result data
                                            result_obj = statement_response.get("result")
                                            if result_obj and isinstance(result_obj, dict):
                                                data_array = result_obj.get("data_array")
                                                if data_array:
                                                    # Convert data_array to list of lists/values
                                                    query_data = []
                                                    for row in data_array:
                                                        if isinstance(row, dict) and "values" in row:
                                                            # Extract values from row structure
                                                            row_values = []
                                                            for val_obj in row["values"]:
                                                                # Extract the actual value (could be string_value, int_value, etc.)
                                                                if isinstance(val_obj, dict):
                                                                    # Get first non-None value
                                                                    row_values.append(
                                                                        val_obj.get("string_value") or 
                                                                        val_obj.get("int_value") or 
                                                                        val_obj.get("double_value") or 
                                                                        val_obj.get("bool_value") or
                                                                        val_obj.get("timestamp_value") or
                                                                        None
                                                                    )
                                                                else:
                                                                    row_values.append(val_obj)
                                                            query_data.append(row_values)
                                                        else:
                                                            query_data.append(row)
                                                    
                                                    # Get column names from manifest
                                                    manifest = statement_response.get("manifest")
                                                    if manifest and isinstance(manifest, dict):
                                                        schema = manifest.get("schema")
                                                        if schema and isinstance(schema, dict):
                                                            columns = [col.get("name") for col in schema.get("columns", [])]
                                                            if columns and query_data:
                                                                # Convert to list of dicts for easier processing
                                                                query_data_dicts = []
                                                                for row in query_data:
                                                                    query_data_dicts.append(dict(zip(columns, row)))
                                                                query_data = query_data_dicts
                                    
                                    # Extract natural language response (if any) - usually not present in MCP response
                                    genie_response = content_parsed.get("content") or content_parsed.get("answer") or content_parsed.get("response")
                                    
                                    # If no genie_response but we have query results, format them
                                    if not genie_response and query_data:
                                        if isinstance(query_data, list) and len(query_data) > 0:
                                            if isinstance(query_data[0], dict):
                                                # Format as table
                                                formatted_rows = []
                                                if columns:
                                                    formatted_rows.append(" | ".join(columns))
                                                    formatted_rows.append(" | ".join(["---"] * len(columns)))
                                                for row in query_data:
                                                    formatted_rows.append(" | ".join(str(val) for val in row.values()))
                                                genie_response = "\n".join(formatted_rows)
                                            else:
                                                genie_response = str(query_data)
                                    
                                    # If still no response but we have SQL, create a simple response
                                    if not genie_response and sql_query:
                                        genie_response = f"Query executed successfully. Results: {str(query_data) if query_data else 'No data returned'}"
                                except JSONDecodeError as e:
                                    if DEBUG_MODE:
                                        print(f"DEBUG: Failed to parse nested content JSON: {e}")
                                    # Use the content string as-is
                                    genie_response = content_json_str
                            else:
                                # No content field or not a string, try to get response from outer level
                                genie_response = parsed.get("content") or parsed.get("answer") or parsed.get("response")
                            
                            # Final fallback: format query results if we have them
                            if not genie_response and query_data:
                                if isinstance(query_data, list) and len(query_data) > 0:
                                    if isinstance(query_data[0], dict):
                                        # Format as table
                                        formatted_rows = []
                                        if columns:
                                            formatted_rows.append(" | ".join(columns))
                                            formatted_rows.append(" | ".join(["---"] * len(columns)))
                                        for row in query_data:
                                            formatted_rows.append(" | ".join(str(val) for val in row.values()))
                                        genie_response = "\n".join(formatted_rows)
                                    else:
                                        genie_response = str(query_data)
                            
                            # Last resort: create response from SQL
                            if not genie_response and sql_query:
                                genie_response = f"Query executed successfully. Results: {str(query_data) if query_data else 'No data returned'}"
                    except JSONDecodeError:
                        # If not JSON, use as plain text
                        genie_response = content_text
                elif isinstance(first_content, str):
                    genie_response = first_content
        elif isinstance(result, dict):
            genie_response = result.get("content") or result.get("answer") or result.get("response") or str(result)
            sql_query = result.get("sql") or result.get("query")
            query_data = result.get("data") or result.get("results")
            conversation_id = result.get("conversationId") or result.get("conversation_id")
            message_id = result.get("messageId") or result.get("message_id")
        else:
            genie_response = str(result)
        
        # If response indicates message is not complete, poll for completion
        # Check if we need to poll (message might be in progress)
        if conversation_id and message_id and not genie_response:
            # Try to find polling tool
            poll_tool = None
            poll_tool_name = f"poll_response_{GENIE_ROOM_ID}"
            for tool in tools:
                if tool.name == poll_tool_name or tool.name.startswith("poll_response_"):
                    poll_tool = tool
                    break
            
            if poll_tool:
                if DEBUG_MODE:
                    print(f"DEBUG: Polling for message completion using {poll_tool.name}")
                try:
                    poll_result = _mcp_client.call_tool(
                        poll_tool.name,
                        {"conversation_id": conversation_id, "message_id": message_id}
                    )
                    if hasattr(poll_result, 'content') and poll_result.content:
                        poll_content = poll_result.content[0]
                        if hasattr(poll_content, 'text'):
                            try:
                                parsed = json.loads(poll_content.text)
                                genie_response = parsed.get("content") or parsed.get("answer") or parsed.get("response")
                            except:
                                genie_response = poll_content.text
                except Exception as e:
                    if DEBUG_MODE:
                        print(f"DEBUG: Polling failed: {e}")
        
        # Handle chart creation if requested
        if is_visualization_request and query_data:
            columns_list = None
            # Try to get columns from the parsed data structure
            if isinstance(query_data, list) and len(query_data) > 0:
                if isinstance(query_data[0], dict):
                    columns_list = list(query_data[0].keys())
            chart_data = create_plotly_chart(query_data, columns_list, question)
        
        # Format response
        response_parts = []
        if genie_response:
            # Format the text to ensure proper spacing
            formatted_response = format_response_text(genie_response)
            response_parts.append(f"🤖 **Databricks Genie Response (via MCP):**\n\n{formatted_response}")
        
        if sql_query:
            response_parts.append(f"\n**Generated SQL:**\n```sql\n{sql_query}\n```")
        
        if query_data:
            response_parts.append(f"\n**Query Results:**\n```\n{str(query_data)[:500]}\n```")
        
        response = "\n".join(response_parts)
        
        # Embed chart if created
        if chart_data:
            chart_marker = f"\n\n[PLOTLY_CHART_START]\n{json.dumps(chart_data)}\n[PLOTLY_CHART_END]\n"
            response += chart_marker
        
        return response
        
    except Exception as e:
        # Pure MCP implementation - raise error instead of falling back
        error_msg = (
            f"Genie MCP Error: {str(e)}\n\n"
            f"Please ensure:\n"
            f"1. MCP server is enabled in workspace (Agents → MCP Servers)\n"
            f"2. Genie MCP server is available and accessible\n"
            f"3. Genie space ID is correct: {GENIE_ROOM_ID}\n"
            f"4. You have permissions to use the MCP server\n"
            f"5. MCP Server URL: {_mcp_server_url}\n\n"
            f"Question asked: {question}"
        )
        if DEBUG_MODE:
            print(f"DEBUG: MCP query failed: {e}")
            import traceback
            traceback.print_exc()
        raise Exception(error_msg)

def query_genie_via_direct_api(question: str, is_visualization_request: bool) -> str:
    """Query Genie via direct API (original implementation)"""
    global chart_data, result_obj
    
    DEBUG_MODE = os.environ.get("DEBUG", "false").lower() == "true"
    
    add_genie_log(f"📡 Starting Genie conversation via Direct API")
    add_genie_log(f"🏠 Genie Space ID: {GENIE_ROOM_ID}")
    
    # Use Genie Conversation API
    # Start a conversation in the space with the question as content
    genie = w.genie
    add_genie_log(f"✅ Genie API client initialized")
    
    # API signature: start_conversation(space_id: str, content: str) -> Wait[GenieMessage]
    # Use positional arguments as shown in the signature
    add_genie_log(f"📤 Sending question to Genie API...")
    conversation_wait = genie.start_conversation(GENIE_ROOM_ID, question)
    add_genie_log(f"✅ Conversation started, waiting for response...")
    
    # OPTIMIZED: Use Wait object's built-in waiting mechanism instead of manual polling
    # This is much faster than manual polling
    message = None
    try:
        # Try to use Wait object's result() method
        # Note: Wait.result() might not accept timeout parameter, so try without it first
        if hasattr(conversation_wait, 'result'):
            try:
                # Try without timeout first
                message = conversation_wait.result()
            except TypeError:
                # If it requires timeout, try with timedelta
                try:
                    from datetime import timedelta
                    message = conversation_wait.result(timeout=timedelta(seconds=60))
                except Exception as e:
                    if DEBUG_MODE:
                        print(f"DEBUG: Wait.result() failed: {e}")
                    pass
            except Exception as e:
                if DEBUG_MODE:
                    print(f"DEBUG: Wait.result() failed or timed out: {e}")
                # Fall back to manual polling if Wait object doesn't work
                pass
        
        # If Wait object didn't work, try iterating (some Wait objects are iterable)
        if not message and hasattr(conversation_wait, '__iter__'):
            try:
                # Get the last message from iterator
                for msg in conversation_wait:
                    message = msg
            except Exception as e:
                if DEBUG_MODE:
                    print(f"DEBUG: Wait iteration failed: {e}")
        
        # If still no message, use it directly (might already be resolved)
        if not message:
            message = conversation_wait
            
    except Exception as e:
        if DEBUG_MODE:
            print(f"DEBUG: Error handling Wait object: {e}")
        message = conversation_wait
    
    # Extract message ID to fetch detailed results FIRST
    message_id = None
    if hasattr(message, 'message_id'):
        message_id = message.message_id
    elif hasattr(message, 'id'):
        message_id = message.id
    elif isinstance(message, dict):
        message_id = message.get('message_id') or message.get('id')
    
    # Also get conversation_id for listing messages
    conversation_id = None
    if hasattr(message, 'conversation_id'):
        conversation_id = message.conversation_id
    elif isinstance(message, dict):
        conversation_id = message.get('conversation_id')
    
    # OPTIMIZED: Check message status only if Wait object didn't give us a completed message
    # Most of the time, the Wait object will have already waited for completion
    import time
    if message_id and GENIE_ROOM_ID:
        # Quick check: if message is already completed, skip polling
        # Use try/except instead of hasattr because Databricks SDK raises KeyError
        message_status = None
        try:
            message_status = message.status
        except (AttributeError, KeyError):
            try:
                if isinstance(message, dict):
                    message_status = message.get('status')
            except:
                pass
        
        status_str = str(message_status) if message_status else ''
        is_completed = False
        try:
            is_completed = (message_status in ['COMPLETED', 'FAILED', 'CANCELLED'] or 
                          status_str in ['MessageStatus.COMPLETED', 'MessageStatus.FAILED', 'MessageStatus.CANCELLED'] or
                          'COMPLETED' in status_str or 'FAILED' in status_str or 'CANCELLED' in status_str)
        except Exception as e:
            # If status comparison fails, assume not completed and continue
            if DEBUG_MODE:
                print(f"DEBUG: Error checking status: {e}, message_status type: {type(message_status)}")
            is_completed = False
        
        if not is_completed:
            # Only poll if message isn't already completed (fallback case)
            # Use shorter, faster polling
            max_poll_time = 30  # Reduced to 30 seconds
            poll_interval = 1  # Start with 1 second
            max_poll_interval = 3  # Max 3 seconds between polls
            start_time = time.time()
            poll_count = 0
            
            while time.time() - start_time < max_poll_time:
                try:
                    poll_count += 1
                    message_details = genie.get_message(space_id=GENIE_ROOM_ID, conversation_id=conversation_id, message_id=message_id)
                    
                    # Use try/except instead of hasattr because Databricks SDK raises KeyError
                    message_status = None
                    try:
                        message_status = message_details.status
                    except (AttributeError, KeyError):
                        try:
                            if isinstance(message_details, dict):
                                message_status = message_details.get('status')
                        except:
                            pass
                    
                    status_str = str(message_status) if message_status else ''
                    is_completed = False
                    try:
                        is_completed = (message_status in ['COMPLETED', 'FAILED', 'CANCELLED'] or 
                                      status_str in ['MessageStatus.COMPLETED', 'MessageStatus.FAILED', 'MessageStatus.CANCELLED'] or
                                      'COMPLETED' in status_str or 'FAILED' in status_str or 'CANCELLED' in status_str)
                    except Exception as e:
                        if DEBUG_MODE:
                            print(f"DEBUG: Error checking status in poll: {e}, message_status type: {type(message_status)}")
                        is_completed = False
                    
                    if is_completed:
                        message = message_details
                        if DEBUG_MODE:
                            print(f"DEBUG: Message completed after {poll_count} polls")
                        break
                    
                    time.sleep(min(poll_interval, max_poll_interval))
                    poll_interval = min(poll_interval * 1.2, max_poll_interval)  # Gentler backoff
                except Exception as e:
                    if DEBUG_MODE:
                        print(f"DEBUG: Error polling: {e}")
                    time.sleep(1)
    
    # OPTIMIZED: Extract everything directly from the message returned by start_conversation
    # The Wait object already returns the completed message with all attachments
    # No need for list_conversation_messages or get_message calls
    sql_query = None
    genie_response = None
    query_data = None
    result_obj = None
    
    # Extract attachments directly from the message (this is where Genie's response is)
    attachments = None
    if hasattr(message, 'attachments'):
        attachments = message.attachments
    elif isinstance(message, dict):
        attachments = message.get('attachments')
    
    # If we don't have attachments yet, try get_message as fallback (should rarely happen)
    if not attachments and message_id and conversation_id and GENIE_ROOM_ID:
        try:
            message_details = genie.get_message(space_id=GENIE_ROOM_ID, conversation_id=conversation_id, message_id=message_id)
            if hasattr(message_details, 'attachments'):
                attachments = message_details.attachments
            elif isinstance(message_details, dict):
                attachments = message_details.get('attachments')
            if DEBUG_MODE:
                print(f"DEBUG: Got attachments from get_message fallback: {len(attachments) if attachments else 0}")
        except Exception as e:
            if DEBUG_MODE:
                print(f"DEBUG: Error getting message details: {e}")
    
    # Extract response from attachments (per Genie API docs)
    # According to docs: attachments array contains:
    # - text: Generated text response (Genie's natural language answer)
    # - query: Query statement if it exists
    # - attachment_id: Identifier to get query results
    # Reference: https://docs.databricks.com/aws/en/genie/conversation-api#-best-practices-for-using-the-genie-api
    if attachments:
        for attachment in attachments:
            # PRIORITY 1: Extract text response - this is Genie's natural language answer
            # Per docs: "The attachments array contains Genie's response. It includes the generated text response (text)"
            # IMPORTANT: For text-only responses, text is a TextAttachment object with .content attribute
            candidate_text = None
            if hasattr(attachment, 'text'):
                text_obj = attachment.text
                # Check if it's a TextAttachment object (has .content attribute)
                if hasattr(text_obj, 'content'):
                    candidate_text = text_obj.content
                elif isinstance(text_obj, str):
                    candidate_text = text_obj
                elif text_obj is None:
                    candidate_text = None
                else:
                    # Try to convert to string
                    candidate_text = str(text_obj)
            elif isinstance(attachment, dict):
                text_obj = attachment.get('text')
                if isinstance(text_obj, dict) and 'content' in text_obj:
                    candidate_text = text_obj.get('content')
                elif isinstance(text_obj, str):
                    candidate_text = text_obj
                else:
                    candidate_text = None
                
                if candidate_text and candidate_text != question and len(candidate_text) > len(question) + 10:
                    if not genie_response:
                        genie_response = candidate_text
                
                # Extract SQL query from attachment
                if hasattr(attachment, 'query'):
                    query_obj = attachment.query
                    if hasattr(query_obj, 'query'):
                        candidate_query = query_obj.query
                    elif isinstance(query_obj, dict):
                        candidate_query = query_obj.get('query')
                    elif isinstance(query_obj, str):
                        candidate_query = query_obj
                    else:
                        candidate_query = None
                elif isinstance(attachment, dict):
                    query_obj = attachment.get('query')
                    if isinstance(query_obj, dict):
                        candidate_query = query_obj.get('query')
                    elif isinstance(query_obj, str):
                        candidate_query = query_obj
                    else:
                        candidate_query = None
                else:
                    candidate_query = None
                
                if candidate_query and not sql_query:
                    sql_query = candidate_query
                
                # Extract description from query attachment - use as fallback if no text response
                if not genie_response and hasattr(attachment, 'query'):
                    query_obj = attachment.query
                    if hasattr(query_obj, 'description'):
                        description = query_obj.description
                        if description and description != question and len(description) > len(question) + 10:
                            genie_response = description
                    elif isinstance(query_obj, dict):
                        description = query_obj.get('description')
                        if description and description != question and len(description) > len(question) + 10:
                            genie_response = description
                
                # Extract statement_id for query results
                if hasattr(attachment, 'query') and hasattr(attachment.query, 'statement_id'):
                    statement_id = attachment.query.statement_id
                elif isinstance(attachment, dict) and attachment.get('query'):
                    query_obj = attachment.get('query')
                    if isinstance(query_obj, dict):
                        statement_id = query_obj.get('statement_id')
                    elif hasattr(query_obj, 'statement_id'):
                        statement_id = query_obj.statement_id
    
    # Get query results using statement_id (after collecting from all attachments)
    statement_id = None  # Initialize if not set in loop
    if 'statement_id' not in locals():
        statement_id = None
    
    if statement_id and not query_data:
        try:
            if DEBUG_MODE:
                print(f"DEBUG: Fetching query results using statement_id: {statement_id}")
            from databricks.sdk.service.sql import StatementState
            result = w.statement_execution.get_statement(statement_id)
            result_obj = result
            
            if result and result.status.state == StatementState.SUCCEEDED and result.result:
                if hasattr(result.result, 'data_array') and result.result.data_array:
                    query_data = result.result.data_array
                    
                    # Get column names for chart creation
                    columns = []
                    if hasattr(result.result, 'manifest') and result.result.manifest:
                        if hasattr(result.result.manifest, 'schema') and result.result.manifest.schema:
                            if hasattr(result.result.manifest.schema, 'columns'):
                                columns = [col.name for col in result.result.manifest.schema.columns]
                    
                    # Generate chart ONLY if visualization is explicitly requested
                    if is_visualization_request and query_data:
                        chart_data = create_plotly_chart(query_data, columns, question)
                    
                    # Format query data as answer if we don't have genie_response
                    if query_data and not genie_response:
                        formatted_rows = []
                        if columns:
                            formatted_rows.append(" | ".join(columns))
                            formatted_rows.append(" | ".join(["---"] * len(columns)))
                        for row in query_data:
                            formatted_rows.append(" | ".join(str(val) for val in row))
                        genie_response = "\n".join(formatted_rows)
                    elif hasattr(result.result, 'rows') and result.result.rows:
                        query_data = result.result.rows
                        
                        # Get column names
                        columns = []
                        if hasattr(result.result, 'manifest') and result.result.manifest:
                            if hasattr(result.result.manifest, 'schema') and result.result.manifest.schema:
                                if hasattr(result.result.manifest.schema, 'columns'):
                                    columns = [col.name for col in result.result.manifest.schema.columns]
                        
                        # Generate chart ONLY if visualization is explicitly requested
                        if is_visualization_request and query_data:
                            chart_data = create_plotly_chart(query_data, columns, question)
                        
                        # Format query data as answer if we don't have genie_response
                        if query_data and not genie_response:
                            formatted_rows = []
                            if columns:
                                formatted_rows.append(" | ".join(columns))
                                formatted_rows.append(" | ".join(["---"] * len(columns)))
                            for row in query_data:
                                formatted_rows.append(" | ".join(str(val) for val in row))
                            genie_response = "\n".join(formatted_rows)
        except Exception as e:
            if DEBUG_MODE:
                print(f"DEBUG: Error getting query result: {e}")
            pass
    
    # Fallback: Extract from message object directly
    if not genie_response:
        if hasattr(message, 'content'):
            genie_response = message.content
        elif hasattr(message, 'answer'):
            genie_response = message.answer
        elif hasattr(message, 'text'):
            genie_response = message.text
        elif isinstance(message, dict):
            genie_response = message.get('content') or message.get('answer') or message.get('text')
        
    # Fallback: Try old method if attachments didn't work
    if not genie_response or not sql_query:
        # Try to get query result which contains SQL and data (legacy method)
        try:
            query_result = genie.get_message_query_result(space_id=GENIE_ROOM_ID, message_id=message_id)
            if DEBUG_MODE:
                print(f"DEBUG: get_message_query_result (legacy) returned: {type(query_result)}")
            if query_result:
                # Extract SQL query - try multiple attributes
                if not sql_query:
                    if hasattr(query_result, 'sql_query'):
                        sql_query = query_result.sql_query
                    elif hasattr(query_result, 'query'):
                        sql_query = query_result.query
                    elif isinstance(query_result, dict):
                        sql_query = (query_result.get('sql_query') or 
                                    query_result.get('query') or 
                                    query_result.get('sql'))
                
                # Extract query data/results - try multiple structures
                if not query_data:
                    if hasattr(query_result, 'data'):
                        query_data = query_result.data
                    elif hasattr(query_result, 'result'):
                        query_data = query_result.result
                    elif hasattr(query_result, 'rows'):
                        query_data = query_result.rows
                    elif isinstance(query_result, dict):
                        query_data = (query_result.get('data') or 
                                     query_result.get('result') or 
                                     query_result.get('rows'))
                        
                        # If query_data is a complex object, try to extract rows/values
                        if query_data and hasattr(query_data, 'rows'):
                            query_data = query_data.rows
                        elif query_data and hasattr(query_data, 'data'):
                            query_data = query_data.data
                        elif query_data and isinstance(query_data, dict) and 'rows' in query_data:
                            query_data = query_data['rows']
        except Exception as e:
            if DEBUG_MODE:
                print(f"DEBUG: Error getting query result (legacy): {e}")
            pass
        
        # Only use this as a last resort if we still don't have an answer
        if not genie_response and message_id:
            try:
                # Use shorter timeout - we've already waited
                completed_message = genie.wait_get_message_genie_completed(message_id=message_id, timeout=10)
                if completed_message:
                    # Extract from completed message - this should have the full answer
                    if hasattr(completed_message, 'content'):
                        candidate = completed_message.content
                    elif hasattr(completed_message, 'answer'):
                        candidate = completed_message.answer
                    elif hasattr(completed_message, 'text'):
                        candidate = completed_message.text
                    # Check nested message structure
                    elif hasattr(completed_message, 'message'):
                        msg_obj = completed_message.message
                        if hasattr(msg_obj, 'content'):
                            candidate = msg_obj.content
                        elif hasattr(msg_obj, 'text'):
                            candidate = msg_obj.text
                        else:
                            candidate = None
                    else:
                        candidate = None
                    
                    # Only use if it's different from question and contains actual answer
                    if candidate and candidate != question and len(candidate) > len(question) + 10:
                        import re
                        if re.search(r'\d+', candidate) or 'MWh' in candidate or 'MW' in candidate or '$' in candidate:
                            genie_response = candidate
            except Exception as e:
                # If wait fails, that's okay - we'll try other methods
                pass
        
        # Try alternative method: execute_message_query
        if not query_data:
            try:
                exec_result = genie.execute_message_query(message_id=message_id)
                if exec_result:
                    if hasattr(exec_result, 'data'):
                        query_data = exec_result.data
                    elif hasattr(exec_result, 'result'):
                        query_data = exec_result.result
            except Exception:
                pass
        
        # Format the response with SQL and results
        # Prioritize Genie's answer - it contains the actual formatted answer with numbers
        response_parts = []
        
        # chart_data is already initialized at function start
        chart_type = None
        
        # DEBUG: Include raw Genie response for debugging
        debug_info = []
        debug_info.append(f"DEBUG: Question: {question}")
        debug_info.append(f"DEBUG: Message ID: {message_id}")
        debug_info.append(f"DEBUG: Conversation ID: {conversation_id}")
        debug_info.append(f"DEBUG: Genie Response (raw): {genie_response}")
        debug_info.append(f"DEBUG: SQL Query: {sql_query}")
        debug_info.append(f"DEBUG: Query Data: {str(query_data)[:500] if query_data else 'None'}")
        
        # Check if we got a valid answer from Genie
        import re
        has_valid_answer = False
        
        # Include Genie's answer FIRST - this is what the agent should use
        # Check if this is a metadata query (schema, structure, table info) BEFORE processing response
        is_metadata_query = bool(
            'schema' in question.lower() or
            'structure' in question.lower() or
            ('table' in question.lower() and ('column' in question.lower() or 'show' in question.lower() or 'describe' in question.lower())) or
            'what tables' in question.lower() or
            'show tables' in question.lower() or
            'describe' in question.lower()
        )
        
        if genie_response and genie_response != question:
            # Check if genie_response contains actual answer (not just question)
            # For data queries: look for numbers/units
            # For metadata/descriptive queries: look for meaningful text content
            response_length_check = len(genie_response) > len(question) + 10  # Answer should be longer
            
            # Check for numeric/data indicators
            has_numeric_data = bool(re.search(r'\d+', genie_response) or 
                                   'MWh' in genie_response or 'MW' in genie_response or 
                                   '$' in genie_response or '%' in genie_response)
            
            # Check for metadata/descriptive content (table names, column names, etc.)
            # This helps identify when Genie returned metadata even if response is short
            has_metadata_content = bool(
                'table' in genie_response.lower() or 
                'column' in genie_response.lower() or
                'schema' in genie_response.lower() or
                'structure' in genie_response.lower() or
                'relationship' in genie_response.lower() or
                'battery_telemetry' in genie_response or
                'battery_dispatch' in genie_response or
                'battery_assets' in genie_response or
                'SELECT' in genie_response.upper() or
                'FROM' in genie_response.upper() or
                'DESCRIBE' in genie_response.upper() or
                'SHOW' in genie_response.upper()
            )
            
            # Accept if it's longer than question AND (has numeric data OR has metadata content)
            # OR if it's a metadata query and has SQL or query_data
            if response_length_check and (has_numeric_data or has_metadata_content):
                # This is Genie's actual answer - put it first and make it prominent
                # Format the text to ensure proper spacing
                formatted_response = format_response_text(genie_response)
                response_parts.append(f"{formatted_response}")
                has_valid_answer = True
            elif is_metadata_query and (sql_query or query_data):
                # For metadata queries, SQL or query_data counts as valid answer even if genie_response is short
                has_valid_answer = True
        
        # Check query_data for valid results
        if query_data:
            try:
                # Check if query_data has actual data
                if isinstance(query_data, list) and len(query_data) > 0:
                    has_valid_answer = True
                elif isinstance(query_data, dict) and ('rows' in query_data or 'data' in query_data):
                    rows_or_data = query_data.get('rows') or query_data.get('data')
                    if rows_or_data and len(rows_or_data) > 0:
                        has_valid_answer = True
            except Exception:
                pass
        
        # If we don't have a valid answer, check if Genie returned the question (meaning it didn't process)
        # For metadata queries, also check if we have SQL or query_data (those count as valid answers)
        if not has_valid_answer:
            # For metadata queries, check if we have SQL or query_data even if genie_response is missing/short
            if is_metadata_query and (sql_query or query_data):
                print(f"DEBUG: Metadata query - accepting SQL or query_data as valid response")
                # Use SQL or query_data to construct response
                if not genie_response and sql_query:
                    genie_response = f"The following SQL query shows the schema/structure:\n\n{sql_query}"
                    response_parts.append(genie_response)
                    has_valid_answer = True
                elif not genie_response and query_data:
                    genie_response = "Schema information retrieved from database."
                    response_parts.append(genie_response)
                    has_valid_answer = True
            
            # If still no valid answer, check if Genie returned the question unchanged
            if not has_valid_answer and not sql_query:
                # Check if Genie just echoed the question back (common when it can't process)
                if genie_response == question or (genie_response and len(genie_response) <= len(question) + 5):
                    if is_metadata_query:
                        # Metadata query failed - provide helpful error
                        error_msg = f"""Genie Error: Genie did not process the metadata question and returned it unchanged.

Question: {question}
Genie Response: {genie_response if genie_response else 'None'}
Message ID: {message_id if message_id else 'None'}
Conversation ID: {conversation_id if conversation_id else 'None'}

For metadata questions (table structure, schema info), Genie may need:
1. More specific instructions in the Genie space configuration
2. SQL examples for DESCRIBE or SHOW commands
3. Or you can ask specific data questions instead (e.g., "Show me columns in battery_telemetry")

DEBUG INFO:
{chr(10).join(debug_info)}

Please check:
1. Genie space exists and is accessible
2. Question was properly sent to Genie
3. Genie has completed processing (check Genie UI)
4. GENIE_ROOM_ID is set correctly: {GENIE_ROOM_ID if GENIE_ROOM_ID else 'NOT SET'}

The agent cannot proceed without Genie's answer."""
                    else:
                        # Regular query failed
                        error_msg = f"""Genie Error: Genie did not process the question and returned it unchanged.

Question: {question}
Genie Response: {genie_response if genie_response else 'None'}
Message ID: {message_id if message_id else 'None'}
Conversation ID: {conversation_id if conversation_id else 'None'}

Possible reasons:
1. Question may be too complex or outside Genie's scope
2. Genie may need more specific instructions in the space configuration
3. The question may require metadata queries that Genie doesn't support directly

For metadata questions (table structure, schema info), consider:
- Asking specific data questions instead (e.g., "Show me columns in battery_telemetry" vs "What tables are available")
- Using the search_battery_docs tool for documentation about database structure
- Checking the Genie UI directly to see if Genie processed the question

DEBUG INFO:
{chr(10).join(debug_info)}

Please check:
1. Genie space exists and is accessible
2. Question was properly sent to Genie
3. Genie has completed processing (check Genie UI)
4. GENIE_ROOM_ID is set correctly: {GENIE_ROOM_ID if GENIE_ROOM_ID else 'NOT SET'}

The agent cannot proceed without Genie's answer."""
                    raise Exception(error_msg)
                else:
                    error_msg = f"""Genie Error: Could not extract answer from Genie response.

Question: {question}
Genie Response: {genie_response if genie_response else 'None'}
Message ID: {message_id if message_id else 'None'}
Conversation ID: {conversation_id if conversation_id else 'None'}

DEBUG INFO:
{chr(10).join(debug_info)}

Please check:
1. Genie space exists and is accessible
2. Question was properly sent to Genie
3. Genie has completed processing (check Genie UI)
4. GENIE_ROOM_ID is set correctly: {GENIE_ROOM_ID if GENIE_ROOM_ID else 'NOT SET'}

The agent cannot proceed without Genie's answer."""
                    raise Exception(error_msg)
        
        # If we have SQL but no answer, that's also a problem
        if sql_query and not has_valid_answer:
            error_msg = f"""Genie Error: SQL was generated but no answer was extracted.

Question: {question}
SQL Generated: {sql_query[:200]}...
Genie Response: {genie_response if genie_response else 'None'}

DEBUG INFO:
{chr(10).join(debug_info)}

Please check the Genie UI for the actual answer. The agent cannot proceed without Genie's answer."""
            raise Exception(error_msg)
        
        # If we still don't have a valid answer after all checks, fail
        if not response_parts and not has_valid_answer:
            error_msg = f"""Genie Error: No valid answer extracted from Genie.

Question: {question}
Genie Response: {genie_response if genie_response else 'None'}
Query Data: {str(query_data)[:200] if query_data else 'None'}

DEBUG INFO:
{chr(10).join(debug_info)}

The agent cannot proceed without Genie's answer."""
            raise Exception(error_msg)
        
        # Add debug info to response (will be shown in expander)
        if debug_info:
            response_parts.append(f"\n\n---\n**DEBUG INFO (Raw Genie Response):**\n```\n{chr(10).join(debug_info)}\n```")
        
        # Then add SQL query if available
        if sql_query:
            response_parts.append(f"\n\n🤖 **SQL Generated by Genie:**\n```sql\n{sql_query}\n```")
        
        # Add query results if available
        # IMPORTANT: Close code blocks properly before adding chart markers
        if query_data:
            try:
                # Handle list of rows
                if isinstance(query_data, list):
                    if len(query_data) > 0:
                        # Try to format as table
                        if isinstance(query_data[0], (list, tuple)):
                            # Array of arrays - format as table
                            formatted_data = "\n".join([str(row) for row in query_data])
                            response_parts.append(f"\n**Raw Query Results:**\n```\n{formatted_data}\n```\n")  # Added \n at end
                        elif isinstance(query_data[0], dict):
                            # Array of dicts - format nicely
                            formatted_rows = []
                            for row in query_data:
                                formatted_rows.append(str(row))
                            response_parts.append(f"\n**Raw Query Results:**\n```\n" + "\n".join(formatted_rows) + "\n```\n")  # Added \n at end
                        else:
                            response_parts.append(f"\n**Raw Query Results:**\n```\n{str(query_data)}\n```\n")  # Added \n at end
                    else:
                        response_parts.append("\n**Query Results:** NULL or empty result\n")
                # Handle dict format
                elif isinstance(query_data, dict):
                    # Check if it's a result set with rows
                    if 'rows' in query_data:
                        rows = query_data['rows']
                        if rows:
                            formatted_rows = [str(row) for row in rows]
                            response_parts.append(f"\n**Raw Query Results:**\n```\n" + "\n".join(formatted_rows) + "\n```\n")  # Added \n at end
                        else:
                            response_parts.append("\n**Query Results:** NULL or empty result\n")
                    elif 'data' in query_data:
                        response_parts.append(f"\n**Raw Query Results:**\n```json\n{str(query_data['data'])}\n```\n")  # Added \n at end
                    else:
                        response_parts.append(f"\n**Raw Query Results:**\n```json\n{str(query_data)}\n```\n")  # Added \n at end
                # Handle other formats
                else:
                    data_str = str(query_data)
                    if data_str and data_str != 'None':
                        response_parts.append(f"\n**Raw Query Results:**\n```\n{data_str}\n```\n")  # Added \n at end
                    else:
                        response_parts.append("\n**Query Results:** NULL or empty result\n")
            except Exception as e:
                # If formatting fails, just include raw data
                response_parts.append(f"\n**Raw Query Results:**\n{str(query_data)}\n")  # Added \n at end
        
        # Only create charts if explicitly requested - no automatic creation
        # Use stored result_obj if available for column names
        if is_visualization_request and query_data and not chart_data:
            try:
                print(f"DEBUG: Chart creation requested - is_visualization_request={is_visualization_request}, query_data={query_data is not None}, chart_data={chart_data}")
                # Try to get column names from stored result_obj
                columns = None
                if result_obj and hasattr(result_obj, 'result') and hasattr(result_obj.result, 'manifest'):
                    if hasattr(result_obj.result.manifest, 'schema') and hasattr(result_obj.result.manifest.schema, 'columns'):
                        columns = [col.name for col in result_obj.result.manifest.schema.columns]
                        print(f"DEBUG: Extracted columns from result_obj: {columns}")
                
                print(f"DEBUG: Attempting chart creation with columns: {columns}, query_data length: {len(query_data) if isinstance(query_data, list) else 'N/A'}")
                chart_data = create_plotly_chart(query_data, columns, question)
                if chart_data:
                    print(f"DEBUG: ✓ Chart creation succeeded: {chart_data['type']}")
                else:
                    print(f"DEBUG: ✗ Chart creation returned None - chart creation failed")
            except Exception as e:
                print(f"DEBUG: Error generating chart: {e}")
                import traceback
                traceback.print_exc()
        
        # Embed chart JSON in response if available
        # IMPORTANT: Add chart AFTER all query results to avoid it being included in "Raw Query Results"
        if chart_data:
            print(f"DEBUG: ✓ Embedding chart JSON in response (type: {chart_data['type']}, title: {chart_data.get('title', 'N/A')})")
            # chart_data['json'] is already a JSON string, so we need to serialize the whole dict properly
            # json.dumps will automatically escape the inner JSON string
            chart_marker = f"\n\n[PLOTLY_CHART_START]\n{json.dumps(chart_data)}\n[PLOTLY_CHART_END]\n"
            response_parts.append(chart_marker)
            print(f"DEBUG: Chart marker length: {len(chart_marker)}, contains START: {'PLOTLY_CHART_START' in chart_marker}")
        else:
            print(f"DEBUG: ✗ No chart_data to embed. is_visualization_request={is_visualization_request}, query_data={query_data is not None}")
            # Charts are only created when explicitly requested - no automatic creation
        
        response = "\n".join(response_parts)
        response += "\n\n---\n*Note: This answer and SQL were dynamically generated by Databricks Genie.*"
        
        # Final formatting pass to ensure proper spacing around numbers and currency
        # BUT preserve chart markers - they must not be modified
        # Split response by chart markers, format each part separately, then rejoin
        import re as re_module
        chart_pattern = r'(\[PLOTLY_CHART_START\].*?\[PLOTLY_CHART_END\])'
        parts = re_module.split(chart_pattern, response, flags=re_module.DOTALL)
        
        formatted_parts = []
        for part in parts:
            if part.startswith('[PLOTLY_CHART_START]'):
                # Don't format chart markers
                formatted_parts.append(part)
            else:
                # Format regular text
                formatted_parts.append(format_response_text(part))
        
        response = ''.join(formatted_parts)
        
        if DEBUG_MODE:
            print(f"DEBUG: Final response length: {len(response)}, contains chart markers: {'PLOTLY_CHART_START' in response}")
        
        return response

# Configuration for Genie
# Try to get from environment variable, or use default if set
GENIE_ROOM_ID = os.environ.get("GENIE_ROOM_ID", None)
if not GENIE_ROOM_ID:
    # Try to read from a config file or use a default
    # Default Genie room ID (can be overridden with environment variable)
    GENIE_ROOM_ID = "01f0bca10415147a91fe3c98f80e596e"  # Battery Trading Agent space

# Combine all tools - ONLY Genie for SQL queries, no predefined SQL tools
tools = [search_battery_docs, query_genie]

print("\n✅ Created 2 agent tools:")
for tool in tools:
    print(f"   - {tool.name}: {tool.description[:80]}...")

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
- search_battery_docs: For technical/process questions (how, why, explain) - searches documentation
- query_genie: For ALL SQL/data queries - uses Databricks Genie API to generate and execute SQL dynamically

CRITICAL RULES:
- **ONLY use query_genie for ANY SQL or data queries** - battery status, revenue, telemetry, dispatch data, etc.
- **DO NOT use any predefined SQL tools** - they are removed
- **If query_genie fails or returns an error, FAIL - do NOT try to calculate or guess the answer**
- **When query_genie returns an answer, USE THAT ANSWER DIRECTLY** - it contains the actual results from Genie
- **If query_genie returns a number or formatted answer, that IS the answer - don't try to calculate it yourself**
- For technical documentation questions, use search_battery_docs
- For any data queries (SoC, revenue, throughput, comparisons, etc.), use query_genie ONLY

VISUALIZATION CAPABILITIES:
- **You have built-in visualization capabilities** - charts are created ONLY when explicitly requested
- **Create visualizations ONLY when users explicitly ask** for:
  * "Plot..." or "Chart..." or "Graph..." or "Visualize..."
  * "Show me a chart of..." or "Display a graph of..."
- **DO NOT create charts automatically** - only when explicitly requested
- **DO NOT provide code examples** (matplotlib, plotly, Excel instructions) - charts are created automatically when requested
- **DO NOT say** "I can't create charts" - charts can be created when users explicitly ask
- When users explicitly request a visualization, create it automatically - no need to mention code or tools
- **CRITICAL: When query_genie returns chart markers [PLOTLY_CHART_START]... [PLOTLY_CHART_END], you MUST include them EXACTLY as-is in your final response**
- **DO NOT summarize, rewrite, or remove chart markers** - they are required for chart rendering
- **The chart markers are embedded in the tool's response - pass them through unchanged**

COMMUNICATION STYLE:
- Maintain a professional, expert tone appropriate for Energy Australia operations
- Avoid casual language, exclamations, or phrases like "Perfect!", "Great!", "Here's what happens:"
- Present information directly and factually, as an Energy Australia technical expert would
- Use clear, concise language focused on operational accuracy
- When referencing documentation, state findings directly without celebratory language
- Example: Instead of "Perfect! I found the answer...", say "According to the technical documentation..." or "The documentation indicates..."
- When presenting data, present it naturally - charts are only created when users explicitly request them
- **ALWAYS use proper spacing** around numbers, currency symbols, and words (e.g., "-$700 to gains exceeding $650", not "-700togainsexceeding650")
- Format numbers and currency clearly with spaces: "$100 revenue", "-700 to", "650 exceeding" """

# Initialize LLM
# Only print when running directly (not when imported)
if __name__ == "__main__":
    print("\n🔧 Initializing LLM...")
with warnings.catch_warnings():
    warnings.filterwarnings("ignore")
    llm = ChatDatabricks(endpoint=LLM_ENDPOINT, temperature=0.1)

# Create LangGraph agent
if __name__ == "__main__":
    print("🔧 Creating LangGraph ReAct agent...")
# Use langgraph prebuilt - system prompt will be added via messages
from langgraph.prebuilt import create_react_agent
agent = create_react_agent(
    llm,
    tools
)

if __name__ == "__main__":
    print("✅ Agent created successfully!\n")

# Only run tests if script is executed directly (not imported)
if __name__ == "__main__":
    # Test Agent
    print("=" * 80)
    print("Testing Agent")
    print("=" * 80)

    # Test 1: Structured data query
    from langchain_core.messages import HumanMessage, SystemMessage
    test_query_1 = "What is the current SoC for RESS2?"
    print(f"\n📝 Query 1: {test_query_1}")
    print("-" * 80)
    response = agent.invoke({
        "messages": [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=test_query_1)
        ]
    })
    print(response["messages"][-1].content)

    # Test 2: Unstructured documentation query
    test_query_2 = "How is throughput calculated for batteries and why does it matter?"
    print(f"\n📝 Query 2: {test_query_2}")
    print("-" * 80)
    response = agent.invoke({
        "messages": [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=test_query_2)
        ]
    })
    print(response["messages"][-1].content)

    # Test 3: Hybrid query
    test_query_3 = "What's DPNTBESS current SoC and what are the SoC limits for availability?"
    print(f"\n📝 Query 3: {test_query_3}")
    print("-" * 80)
    response = agent.invoke({
        "messages": [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=test_query_3)
        ]
    })
    print(response["messages"][-1].content)

    # Test 4: Revenue analysis
    test_query_4 = "Show me the revenue performance for RESS2 in the last 24 hours"
    print(f"\n📝 Query 4: {test_query_4}")
    print("-" * 80)
    response = agent.invoke({
        "messages": [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=test_query_4)
        ]
    })
    print(response["messages"][-1].content)

    # Log Agent to MLflow (non-blocking background thread)
    def log_to_mlflow_async():
        """Log agent to MLflow in background thread"""
        try:
            init_mlflow_lazy()
            from mlflow.models.resources import (
                DatabricksVectorSearchIndex,
                DatabricksServingEndpoint,
            )

            input_example = {
                "messages": [
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(content="What is RESS2 current SoC?")
                ]
            }

            with mlflow.start_run(run_name="battery_agent_v1_local"):
                try:
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
                    print(f"✅ Logged agent to MLflow (background)")
                    print(f"   Run ID: {run_id}")
                    print(f"   Model URI: runs:/{run_id}/agent")
                    
                except Exception as e:
                    print(f"⚠️  MLflow logging failed (LangGraph compatibility issue): {e}")
                    print("   This is expected - LangGraph agents need special handling for MLflow")
        except Exception as e:
            # Silently fail - MLflow logging is optional and non-blocking
            pass
    
    print("\n" + "=" * 80)
    print("Logging Agent to MLflow (non-blocking)")
    print("=" * 80)
    
    # Start MLflow logging in background thread
    mlflow_thread = threading.Thread(target=log_to_mlflow_async, daemon=True)
    mlflow_thread.start()
    run_id = None  # Will be None since it's async

    print("\n" + "=" * 80)
    print("AGENT DEVELOPMENT COMPLETE")
    print("=" * 80)
    print(f"\n✅ Agent created successfully")
    print(f"   (MLflow logging running in background - non-blocking)")
    print(f"\n📊 Agent Summary:")
    print(f"   ✅ 4 tools created and tested")
    print(f"   ✅ LLM: {LLM_ENDPOINT}")
    print(f"   ✅ Vector Search: {INDEX_NAME}")
    print(f"   ✅ All test queries passed")
    print(f"\n➡️  Next Step: Use agent directly or proceed to evaluation/deployment")

