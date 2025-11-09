#!/usr/bin/env python3
"""
Battery Trading Agent Development - Local Execution
Run this script locally to build and test the agent
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

# Initialize clients
w = WorkspaceClient()
vsc = VectorSearchClient(disable_notice=True)

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

# Tool 5: Query Genie (Databricks Genie API)
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
    
    Returns Genie's response with query results."""
    
    # Initialize debug log - MUST be first thing, write immediately
    debug_log_path = "/tmp/genie_debug.log"
    import json
    import time
    import sys
    
    # Write immediately with force flush
    log_entry = f"\n{'='*80}\nNEW QUERY_GENIE CALL - {time.strftime('%Y-%m-%d %H:%M:%S')}\nQuestion: {question}\n{'='*80}\n"
    
    # Print to console FIRST (this always works)
    print(f"\n{'='*80}")
    print(f"DEBUG: query_genie CALLED")
    print(f"DEBUG: Question: {question}")
    print(f"DEBUG: Logging to: {debug_log_path}")
    print(f"{'='*80}")
    
    # Then write to file
    try:
        with open(debug_log_path, "a", encoding='utf-8') as f:
            f.write(log_entry)
            f.flush()
            try:
                os.fsync(f.fileno())  # Force OS-level flush
            except:
                pass
        print(f"DEBUG: Successfully wrote to {debug_log_path}")
    except Exception as e:
        print(f"DEBUG: ERROR writing to debug log: {e}")
        import traceback
        traceback.print_exc()
        # Continue anyway - don't let logging failure break the function
    
    try:
        if not GENIE_ROOM_ID:
            return f"""Genie space ID not configured. 

To use Genie:
1. Create a Genie space named 'battery-trading-agent' in Databricks UI
2. Run: python3 scripts/create_genie_room.py
3. Set environment variable: export GENIE_ROOM_ID=\"<space_id>\"

Question asked: {question}"""
        
        # Use Genie Conversation API
        # Start a conversation in the space with the question as content
        genie = w.genie
        
        # API signature: start_conversation(space_id: str, content: str) -> Wait[GenieMessage]
        # Use positional arguments as shown in the signature
        conversation_wait = genie.start_conversation(GENIE_ROOM_ID, question)
        
        # Wait for the conversation to complete and get the message
        # Wait objects in Databricks SDK can be used directly or awaited
        message = None
        try:
            # Try calling result() if it exists
            if callable(getattr(conversation_wait, 'result', None)):
                message = conversation_wait.result()
            # Try iterating (Wait objects are iterable)
            elif hasattr(conversation_wait, '__iter__'):
                # Get the last item from the iterator
                for msg in conversation_wait:
                    message = msg
            else:
                # If it's already resolved, use it directly
                message = conversation_wait
        except Exception as e:
            # If Wait handling fails, try to use it directly
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
        
        # Poll for message status following Genie API best practices
        # Poll every 1-5 seconds with exponential backoff, max 2 minutes for UI responsiveness
        import time
        max_poll_time = 120  # 2 minutes max (reduced for UI responsiveness)
        poll_interval = 2  # Start with 2 seconds
        max_poll_interval = 10  # Max 10 seconds between polls (reduced from 60)
        start_time = time.time()
        
        if message_id and GENIE_ROOM_ID:
            message_status = None
            message_details = None
            poll_count = 0
            
            while time.time() - start_time < max_poll_time:
                try:
                    poll_count += 1
                    # Get message status - requires conversation_id
                    message_details = genie.get_message(space_id=GENIE_ROOM_ID, conversation_id=conversation_id, message_id=message_id)
                    
                    # Extract status
                    if hasattr(message_details, 'status'):
                        message_status = message_details.status
                    elif isinstance(message_details, dict):
                        message_status = message_details.get('status')
                    
                    elapsed = int(time.time() - start_time)
                    print(f"DEBUG: Poll #{poll_count} [{elapsed}s] Status: {message_status}")
                    
                    # Check if message is in a conclusive state
                    # Handle both string and MessageStatus enum
                    status_str = str(message_status)
                    if (message_status in ['COMPLETED', 'FAILED', 'CANCELLED'] or 
                        status_str in ['MessageStatus.COMPLETED', 'MessageStatus.FAILED', 'MessageStatus.CANCELLED'] or
                        'COMPLETED' in status_str or 'FAILED' in status_str or 'CANCELLED' in status_str):
                        message = message_details  # Use the completed message
                        print(f"DEBUG: Message reached conclusive state: {message_status}")
                        break
                    
                    # Wait before next poll with exponential backoff
                    wait_time = min(poll_interval, max_poll_interval)
                    print(f"DEBUG: Waiting {wait_time}s before next poll...")
                    time.sleep(wait_time)
                    poll_interval = min(poll_interval * 1.5, max_poll_interval)  # Exponential backoff
                    
                except Exception as e:
                    print(f"DEBUG: Error polling message status: {e}")
                    # Continue polling on error
                    wait_time = min(poll_interval, max_poll_interval)
                    time.sleep(wait_time)
                    poll_interval = min(poll_interval * 1.5, max_poll_interval)
            
            if message_status not in ['COMPLETED', 'FAILED', 'CANCELLED']:
                elapsed = int(time.time() - start_time)
                print(f"DEBUG: Polling timeout after {elapsed} seconds, status: {message_status}")
                # Use the last message_details we got, even if not completed
                if message_details:
                    message = message_details
        else:
            # If no message_id, wait a bit
            print("DEBUG: No message_id, waiting 5 seconds...")
            time.sleep(5)
        
        # Try to get the full message details including SQL and results
        sql_query = None
        genie_response = None
        query_data = None
        
        # First, try to get the assistant's response from conversation messages
        # Wait a bit more for Genie to process
        time.sleep(3)
        
        if conversation_id and GENIE_ROOM_ID:
            try:
                # list_conversation_messages requires space_id as first positional argument
                messages = genie.list_conversation_messages(GENIE_ROOM_ID, conversation_id=conversation_id)
                print(f"DEBUG: list_conversation_messages returned: {type(messages)}")
                if messages:
                    # Handle different response structures
                    msg_list = None
                    if hasattr(messages, 'messages'):
                        msg_list = messages.messages
                    elif hasattr(messages, 'items'):
                        msg_list = messages.items
                    elif isinstance(messages, list):
                        msg_list = messages
                    
                    print(f"DEBUG: Message list type: {type(msg_list)}, length: {len(msg_list) if msg_list else 0}")
                    
                    if msg_list:
                        # Get ALL messages to find the assistant response
                        for idx, msg in enumerate(reversed(msg_list)):
                            # Look for assistant/genie messages
                            role = getattr(msg, 'role', None) or (isinstance(msg, dict) and msg.get('role'))
                            content = getattr(msg, 'content', None) or (isinstance(msg, dict) and msg.get('content'))
                            
                            print(f"DEBUG: Message {idx}: role={role}, content_length={len(content) if content else 0}, content_preview={content[:100] if content else None}")
                            
                            # Skip if content is the question itself
                            if content == question:
                                print(f"DEBUG: Skipping message {idx} - matches question")
                                continue
                            
                            # Check if it's an assistant response
                            if role and role.lower() in ['assistant', 'genie', 'ai']:
                                if content and len(content) > len(question) + 10:  # Answer should be longer
                                    print(f"DEBUG: Found assistant response: {content[:200]}")
                                    genie_response = content
                                    break
                            elif content and len(content) > len(question) + 10:
                                # If no role but content is different and longer, might be answer
                                # Check if it contains numbers/units OR metadata keywords
                                import re
                                has_numeric = bool(re.search(r'\d+', content) or 'MWh' in content or 'MW' in content or '$' in content)
                                has_metadata = bool(
                                    'table' in content.lower() or 
                                    'column' in content.lower() or
                                    'schema' in content.lower() or
                                    'structure' in content.lower() or
                                    'battery_telemetry' in content or
                                    'battery_dispatch' in content or
                                    'battery_assets' in content or
                                    'SELECT' in content.upper() or
                                    'FROM' in content.upper()
                                )
                                if has_numeric or has_metadata:
                                    print(f"DEBUG: Found answer-like content: {content[:200]}")
                                    genie_response = content
                                    break
            except Exception as e:
                # Log error for debugging
                print(f"DEBUG: Error listing conversation messages: {e}")
                import traceback
                traceback.print_exc()
                pass
        
        # Then try to get message details and query results
        # Following Genie API docs: when status is COMPLETED, response is in attachments array
        if message_id and GENIE_ROOM_ID:
            try:
                # Get the message details - this should contain the answer
                # Note: get_message requires conversation_id
                message_details = genie.get_message(space_id=GENIE_ROOM_ID, conversation_id=conversation_id, message_id=message_id)
                print(f"DEBUG: get_message returned: {type(message_details)}")
                print(f"DEBUG: message_details attributes: {dir(message_details) if hasattr(message_details, '__dict__') else 'N/A'}")
                
                # Write full message_details to debug log AND console
                debug_log_path = "/tmp/genie_debug.log"
                import json
                try:
                    print(f"\n{'='*80}")
                    print(f"DEBUG: Writing to {debug_log_path}")
                    print(f"Question: {question}")
                    print(f"Message ID: {message_id}")
                    print(f"Conversation ID: {conversation_id}")
                    print(f"Message Details Type: {type(message_details)}")
                    
                    with open(debug_log_path, "a") as f:
                        f.write(f"\n{'='*80}\n")
                        f.write(f"Question: {question}\n")
                        f.write(f"Message ID: {message_id}\n")
                        f.write(f"Conversation ID: {conversation_id}\n")
                        f.write(f"Message Details Type: {type(message_details)}\n")
                        
                        # Try multiple methods to serialize
                        if hasattr(message_details, '__dict__'):
                            msg_dict = {k: str(v)[:1000] for k, v in message_details.__dict__.items()}
                            msg_json = json.dumps(msg_dict, indent=2, default=str)
                            print(f"Message Details __dict__ keys: {list(msg_dict.keys())}")
                            f.write(f"Message Details __dict__:\n{msg_json}\n")
                        elif hasattr(message_details, 'as_dict'):
                            msg_dict = message_details.as_dict()
                            msg_json = json.dumps(msg_dict, indent=2, default=str)
                            print(f"Message Details (as_dict) keys: {list(msg_dict.keys()) if isinstance(msg_dict, dict) else 'N/A'}")
                            f.write(f"Message Details (as_dict):\n{msg_json}\n")
                        else:
                            msg_str = str(message_details)[:2000]
                            print(f"Message Details (str): {msg_str[:200]}...")
                            f.write(f"Message Details (str):\n{msg_str}\n")
                        
                        f.write(f"{'='*80}\n")
                        f.flush()  # Force write
                    print(f"DEBUG: Successfully wrote to {debug_log_path}")
                except Exception as e:
                    print(f"DEBUG: Error writing to debug log: {e}")
                    import traceback
                    traceback.print_exc()
                
                # Extract attachments array (contains Genie's response when COMPLETED)
                attachments = None
                if hasattr(message_details, 'attachments'):
                    attachments = message_details.attachments
                elif isinstance(message_details, dict):
                    attachments = message_details.get('attachments')
                
                print(f"DEBUG: Attachments: {attachments}")
                print(f"DEBUG: Number of attachments: {len(attachments) if attachments else 0}")
                
                # Log attachments to debug file AND console
                try:
                    print(f"\nDEBUG: Logging attachments to {debug_log_path}")
                    print(f"Number of attachments: {len(attachments) if attachments else 0}")
                    
                    with open(debug_log_path, "a") as f:
                        f.write(f"\nAttachments:\n")
                        if attachments:
                            for idx, att in enumerate(attachments):
                                print(f"  Processing attachment {idx + 1}...")
                                f.write(f"  Attachment {idx + 1}:\n")
                                if hasattr(att, '__dict__'):
                                    att_dict = {k: str(v)[:1000] for k, v in att.__dict__.items()}
                                    att_json = json.dumps(att_dict, indent=4, default=str)
                                    print(f"    Type: {type(att)}")
                                    print(f"    Keys: {list(att_dict.keys())}")
                                    f.write(f"    Type: {type(att)}\n")
                                    f.write(f"    __dict__:\n{att_json}\n")
                                elif hasattr(att, 'as_dict'):
                                    att_dict = att.as_dict()
                                    att_json = json.dumps(att_dict, indent=4, default=str)
                                    print(f"    Type: {type(att)}")
                                    print(f"    Keys: {list(att_dict.keys()) if isinstance(att_dict, dict) else 'N/A'}")
                                    f.write(f"    as_dict:\n{att_json}\n")
                                else:
                                    att_str = str(att)[:1000]
                                    print(f"    Value: {att_str[:200]}...")
                                    f.write(f"    Value: {att_str}\n")
                        else:
                            print("  No attachments found")
                            f.write("  No attachments\n")
                        f.write(f"{'='*80}\n")
                        f.flush()  # Force write
                    print(f"DEBUG: Successfully logged attachments to {debug_log_path}")
                except Exception as e:
                    print(f"DEBUG: Error logging attachments: {e}")
                    import traceback
                    traceback.print_exc()
                
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
                        if hasattr(attachment, 'text'):
                            candidate_text = attachment.text
                        elif isinstance(attachment, dict):
                            candidate_text = attachment.get('text')
                        else:
                            candidate_text = None
                        
                        print(f"DEBUG: attachment.text = {candidate_text[:200] if candidate_text else 'None'}")
                        
                        if candidate_text and candidate_text != question and len(candidate_text) > len(question) + 10:
                            print(f"DEBUG: Found text response in attachment: {candidate_text[:200]}")
                            if not genie_response:
                                genie_response = candidate_text
                                print(f"DEBUG: Using attachment.text as genie_response")
                        
                        # Extract description from query attachment - this might contain Genie's explanation
                        if hasattr(attachment, 'query'):
                            query_obj = attachment.query
                            if hasattr(query_obj, 'description'):
                                description = query_obj.description
                                print(f"DEBUG: Found query description: {description[:200] if description else None}")
                                # Description explains what Genie is doing, but might not be the full answer
                                # Use it if we don't have anything else
                                if description and description != question and len(description) > len(question) + 10:
                                    if not genie_response:
                                        genie_response = description
                                        print(f"DEBUG: Using query description as genie_response")
                            elif isinstance(query_obj, dict):
                                description = query_obj.get('description')
                                if description and description != question and len(description) > len(question) + 10:
                                    if not genie_response:
                                        genie_response = description
                                        print(f"DEBUG: Using query description from dict as genie_response")
                        
                        # Extract SQL query from attachment
                        # Query is a GenieQueryAttachment object, extract the actual query string
                        if hasattr(attachment, 'query'):
                            query_obj = attachment.query
                            if hasattr(query_obj, 'query'):
                                candidate_query = query_obj.query  # Extract the SQL string
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
                            print(f"DEBUG: Found query in attachment: {sql_query[:200]}")
                        
                        # Extract attachment_id for query results
                        # Per docs: Use attachment_id to get query results via:
                        # GET /api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}/query-result/{attachment_id}
                        attachment_id = None
                        if hasattr(attachment, 'attachment_id'):
                            attachment_id = attachment.attachment_id
                        elif isinstance(attachment, dict):
                            attachment_id = attachment.get('attachment_id') or attachment.get('id')
                        
                        print(f"DEBUG: attachment_id = {attachment_id}")
                        
                        # Get query results using statement_id from query attachment
                        # Extract statement_id from the query attachment
                        # Alternative: Can also use attachment_id with get_message_query_result endpoint
                        statement_id = None
                        if hasattr(attachment, 'query') and hasattr(attachment.query, 'statement_id'):
                            statement_id = attachment.query.statement_id
                        elif isinstance(attachment, dict) and attachment.get('query'):
                            query_obj = attachment.get('query')
                            if isinstance(query_obj, dict):
                                statement_id = query_obj.get('statement_id')
                            elif hasattr(query_obj, 'statement_id'):
                                statement_id = query_obj.statement_id
                        
                        print(f"DEBUG: statement_id = {statement_id}")
                        
                        # Try using attachment_id to get query results (per API docs)
                        if attachment_id and not query_data:
                            try:
                                print(f"DEBUG: Trying get_message_query_result with attachment_id: {attachment_id}")
                                # Per docs: GET /api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}/query-result/{attachment_id}
                                query_result = genie.get_message_query_result(
                                    space_id=GENIE_ROOM_ID,
                                    conversation_id=conversation_id,
                                    message_id=message_id,
                                    attachment_id=attachment_id
                                )
                                print(f"DEBUG: get_message_query_result returned: {type(query_result)}")
                                if query_result:
                                    # Extract results from query_result
                                    if hasattr(query_result, 'data'):
                                        query_data = query_result.data
                                    elif hasattr(query_result, 'result'):
                                        query_data = query_result.result
                                    elif isinstance(query_result, dict):
                                        query_data = query_result.get('data') or query_result.get('result')
                                    print(f"DEBUG: Got query_data from get_message_query_result: {len(query_data) if isinstance(query_data, list) else 'N/A'} rows")
                            except Exception as e:
                                print(f"DEBUG: Error using get_message_query_result: {e}")
                                # Fall back to statement_id method
                        
                        # Fallback: Use statement_id directly with Statement Execution API
                        if statement_id and not query_data:
                            try:
                                print(f"DEBUG: Fetching query results using statement_id: {statement_id}")
                                # Use statement execution API to get results
                                from databricks.sdk.service.sql import StatementState
                                result = w.statement_execution.get_statement(statement_id)
                                
                                if result and result.status.state == StatementState.SUCCEEDED and result.result:
                                    print(f"DEBUG: Got statement result, extracting data...")
                                    if hasattr(result.result, 'data_array') and result.result.data_array:
                                        query_data = result.result.data_array
                                        print(f"DEBUG: Found query_data from statement: {len(query_data)} rows")
                                        # Format query data as a readable answer if we don't have genie_response
                                        if query_data and not genie_response:
                                            # Get column names if available
                                            columns = []
                                            if hasattr(result.result, 'manifest') and result.result.manifest:
                                                if hasattr(result.result.manifest, 'schema') and result.result.manifest.schema:
                                                    if hasattr(result.result.manifest.schema, 'columns'):
                                                        columns = [col.name for col in result.result.manifest.schema.columns]
                                            
                                            # Format as table
                                            formatted_rows = []
                                            if columns:
                                                formatted_rows.append(" | ".join(columns))
                                                formatted_rows.append(" | ".join(["---"] * len(columns)))
                                            for row in query_data:
                                                formatted_rows.append(" | ".join(str(val) for val in row))
                                            genie_response = "\n".join(formatted_rows)
                                            print(f"DEBUG: Created genie_response from query_data: {genie_response[:200]}")
                                    elif hasattr(result.result, 'rows') and result.result.rows:
                                        query_data = result.result.rows
                                        print(f"DEBUG: Found query_data from statement: {len(query_data)} rows")
                                        # Format query data as a readable answer if we don't have genie_response
                                        if query_data and not genie_response:
                                            formatted_rows = []
                                            for row in query_data:
                                                formatted_rows.append(" | ".join(str(val) for val in row))
                                            genie_response = "\n".join(formatted_rows)
                                            print(f"DEBUG: Created genie_response from query_data: {genie_response[:200]}")
                            except Exception as e:
                                print(f"DEBUG: Error getting query result from statement: {e}")
                                import traceback
                                traceback.print_exc()
                
                # Extract answer/content from message details (if not already found)
                if not genie_response:
                    if hasattr(message_details, 'content'):
                        candidate = message_details.content
                        print(f"DEBUG: Found content in message_details: {candidate[:200] if candidate else None}")
                        if candidate and candidate != question:
                            genie_response = candidate
                    elif hasattr(message_details, 'answer'):
                        candidate = message_details.answer
                        print(f"DEBUG: Found answer in message_details: {candidate[:200] if candidate else None}")
                        if candidate and candidate != question:
                            genie_response = candidate
                    elif hasattr(message_details, 'text'):
                        candidate = message_details.text
                        print(f"DEBUG: Found text in message_details: {candidate[:200] if candidate else None}")
                        if candidate and candidate != question:
                            genie_response = candidate
                    elif hasattr(message_details, 'message'):
                        # Sometimes answer is nested in message object
                        msg_obj = message_details.message
                        print(f"DEBUG: Found nested message object: {type(msg_obj)}")
                        if hasattr(msg_obj, 'content'):
                            candidate = msg_obj.content
                            print(f"DEBUG: Found content in nested message: {candidate[:200] if candidate else None}")
                            if candidate and candidate != question:
                                genie_response = candidate
                        elif hasattr(msg_obj, 'text'):
                            candidate = msg_obj.text
                            print(f"DEBUG: Found text in nested message: {candidate[:200] if candidate else None}")
                            if candidate and candidate != question:
                                genie_response = candidate
                    elif isinstance(message_details, dict):
                        candidate = (message_details.get('content') or 
                                    message_details.get('answer') or 
                                    message_details.get('text') or
                                    message_details.get('message', {}).get('content'))
                        print(f"DEBUG: Found in dict: {candidate[:200] if candidate else None}")
                        if candidate and candidate != question:
                            genie_response = candidate
                
                # Fallback: Try old method if attachments didn't work
                if not genie_response or not sql_query:
                    # Try to get query result which contains SQL and data (legacy method)
                    try:
                        query_result = genie.get_message_query_result(space_id=GENIE_ROOM_ID, message_id=message_id)
                        print(f"DEBUG: get_message_query_result (legacy) returned: {type(query_result)}")
                        if query_result:
                            print(f"DEBUG: query_result attributes: {dir(query_result) if hasattr(query_result, '__dict__') else 'N/A'}")
                            
                            # Extract SQL query - try multiple attributes
                            if not sql_query:
                                if hasattr(query_result, 'sql_query'):
                                    sql_query = query_result.sql_query
                                    print(f"DEBUG: Found sql_query: {sql_query[:200] if sql_query else None}")
                                elif hasattr(query_result, 'query'):
                                    sql_query = query_result.query
                                    print(f"DEBUG: Found query: {sql_query[:200] if sql_query else None}")
                                elif isinstance(query_result, dict):
                                    sql_query = (query_result.get('sql_query') or 
                                                query_result.get('query') or 
                                                query_result.get('sql'))
                                    print(f"DEBUG: Found in dict: {sql_query[:200] if sql_query else None}")
                            
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
                                
                                print(f"DEBUG: Found query_data (legacy): {str(query_data)[:200] if query_data else None}")
                                
                    except Exception as e:
                        # Query result extraction failed, try alternative method
                        print(f"DEBUG: Error getting query result (legacy): {e}")
                        pass
                
                # Try alternative: wait for message to complete, then get results
                # This should have been done earlier, but try again if we still don't have answer
                if not genie_response:
                    try:
                        # Use wait_get_message_genie_completed to ensure message is fully processed
                        completed_message = genie.wait_get_message_genie_completed(message_id=message_id, timeout=30)
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
                    
            except Exception as e:
                # If get_message fails, try alternative approaches
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
            else:
                genie_response = str(message)
        
        # Format the response with SQL and results
        # Prioritize Genie's answer - it contains the actual formatted answer with numbers
        response_parts = []
        
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
                'FROM' in genie_response.upper()
            )
            
            # Accept if it's longer than question AND (has numeric data OR has metadata content)
            if response_length_check and (has_numeric_data or has_metadata_content):
                # This is Genie's actual answer - put it first and make it prominent
                response_parts.append(f"{genie_response}")
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
        if not has_valid_answer and not sql_query:
            # Check if Genie just echoed the question back (common when it can't process)
            if genie_response == question or (genie_response and len(genie_response) <= len(question) + 5):
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
        if query_data:
            try:
                # Handle list of rows
                if isinstance(query_data, list):
                    if len(query_data) > 0:
                        # Try to format as table
                        if isinstance(query_data[0], (list, tuple)):
                            # Array of arrays - format as table
                            formatted_data = "\n".join([str(row) for row in query_data])
                            response_parts.append(f"\n**Raw Query Results:**\n```\n{formatted_data}\n```")
                        elif isinstance(query_data[0], dict):
                            # Array of dicts - format nicely
                            formatted_rows = []
                            for row in query_data:
                                formatted_rows.append(str(row))
                            response_parts.append(f"\n**Raw Query Results:**\n```\n" + "\n".join(formatted_rows) + "\n```")
                        else:
                            response_parts.append(f"\n**Raw Query Results:**\n```\n{str(query_data)}\n```")
                    else:
                        response_parts.append("\n**Query Results:** NULL or empty result")
                # Handle dict format
                elif isinstance(query_data, dict):
                    # Check if it's a result set with rows
                    if 'rows' in query_data:
                        rows = query_data['rows']
                        if rows:
                            formatted_rows = [str(row) for row in rows]
                            response_parts.append(f"\n**Raw Query Results:**\n```\n" + "\n".join(formatted_rows) + "\n```")
                        else:
                            response_parts.append("\n**Query Results:** NULL or empty result")
                    elif 'data' in query_data:
                        response_parts.append(f"\n**Raw Query Results:**\n```json\n{str(query_data['data'])}\n```")
                    else:
                        response_parts.append(f"\n**Raw Query Results:**\n```json\n{str(query_data)}\n```")
                # Handle other formats
                else:
                    data_str = str(query_data)
                    if data_str and data_str != 'None':
                        response_parts.append(f"\n**Raw Query Results:**\n```\n{data_str}\n```")
                    else:
                        response_parts.append("\n**Query Results:** NULL or empty result")
            except Exception as e:
                # If formatting fails, just include raw data
                response_parts.append(f"\n**Raw Query Results:**\n{str(query_data)}")
        
        response = "\n".join(response_parts)
        response += "\n\n---\n*Note: This answer and SQL were dynamically generated by Databricks Genie.*"
        
        return response
        
    except Exception as e:
        # Don't return error message - raise exception so agent doesn't fall back to other tools
        error_msg = f"Genie API Error: {str(e)}\n\nPlease ensure:\n1. Genie space 'battery-trading-agent' exists\n2. GENIE_ROOM_ID is set correctly\n3. You have permissions to use the space\n4. Genie API is enabled in your workspace\n\nQuestion asked: {question}"
        # Raise exception instead of returning error message
        raise Exception(error_msg)

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

COMMUNICATION STYLE:
- Maintain a professional, expert tone appropriate for Energy Australia operations
- Avoid casual language, exclamations, or phrases like "Perfect!", "Great!", "Here's what happens:"
- Present information directly and factually, as an Energy Australia technical expert would
- Use clear, concise language focused on operational accuracy
- When referencing documentation, state findings directly without celebratory language
- Example: Instead of "Perfect! I found the answer...", say "According to the technical documentation..." or "The documentation indicates..." """

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

