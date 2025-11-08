import streamlit as st
import sys
import os
import warnings
from pathlib import Path

# Suppress warnings
warnings.filterwarnings("ignore")
os.environ["PYTHONWARNINGS"] = "ignore"

# Add parent directory to path to import agent
sys.path.append(str(Path(__file__).parent.parent))

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
import importlib.util
from pathlib import Path
import json

# Cache agent initialization to avoid reloading on every page refresh
@st.cache_resource
def load_agent():
    """Load agent lazily - only when needed"""
    AGENT_AVAILABLE = False
    AGENT_ERROR = None
    agent = None
    SYSTEM_PROMPT = None
    
    try:
        agent_script_path = Path(__file__).parent.parent / "scripts" / "02_agent_development_local.py"
        if agent_script_path.exists():
            spec = importlib.util.spec_from_file_location("agent_module", agent_script_path)
            agent_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(agent_module)
            agent = agent_module.agent
            SYSTEM_PROMPT = agent_module.SYSTEM_PROMPT
            AGENT_AVAILABLE = True
        else:
            AGENT_ERROR = f"Agent script not found at {agent_script_path}"
    except Exception as e:
        AGENT_AVAILABLE = False
        AGENT_ERROR = str(e)
    
    return AGENT_AVAILABLE, agent, SYSTEM_PROMPT, AGENT_ERROR

# Load agent (cached)
AGENT_AVAILABLE, agent, SYSTEM_PROMPT, AGENT_ERROR = load_agent()

# Page config
st.set_page_config(
    page_title="Energy Australia - Battery Trading Assistant",
    page_icon="🔋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Energy Australia branding
st.markdown("""
<style>
    /* Energy Australia Brand Colors */
    :root {
        --ea-blue: #003366;
        --ea-light-blue: #0066CC;
        --ea-green: #00A651;
        --ea-dark-green: #00843D;
        --ea-gray: #666666;
        --ea-light-gray: #F5F5F5;
    }
    
    /* Main container */
    .main {
        background-color: #FFFFFF;
    }
    
    /* Header */
    .header-container {
        background: linear-gradient(135deg, #003366 0%, #0066CC 100%);
        padding: 1.5rem 2rem;
        border-radius: 8px;
        margin-bottom: 2rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .header-title {
        color: #FFFFFF;
        font-size: 2rem;
        font-weight: 600;
        margin: 0;
    }
    
    .header-subtitle {
        color: #E0E0E0;
        font-size: 1rem;
        margin-top: 0.5rem;
    }
    
    /* Chat container */
    .chat-container {
        background-color: #FFFFFF;
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    /* User message */
    .user-message {
        background-color: #0066CC;
        color: #FFFFFF;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        margin-left: 20%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Assistant message */
    .assistant-message {
        background-color: #F5F5F5;
        color: #333333;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        margin-right: 20%;
        border-left: 4px solid #00A651;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Input area */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #E0E0E0;
        padding: 0.75rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #0066CC;
        box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.1);
    }
    
    /* Button styling */
    .stButton > button {
        background-color: #00A651;
        color: #FFFFFF;
        border-radius: 8px;
        border: none;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: background-color 0.3s;
        width: 100%;
    }
    
    .stButton > button:hover {
        background-color: #00843D;
    }
    
    /* Status indicator */
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-online {
        background-color: #00A651;
    }
    
    .status-offline {
        background-color: #CCCCCC;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 1rem;
        color: #666666;
        font-size: 0.875rem;
        margin-top: 2rem;
        border-top: 1px solid #E0E0E0;
    }
    
    /* Markdown styling */
    .stMarkdown {
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Header with logo
col1, col2 = st.columns([1, 4])
with col1:
    logo_path = Path(__file__).parent.parent / "logo.png"
    try:
        if logo_path.exists():
            st.image(str(logo_path), width=120)
        else:
            st.markdown("### 🔋")
    except Exception as e:
        # If image loading fails (e.g., PIL not installed), show icon
        st.markdown("### 🔋")

with col2:
    st.markdown("""
    <div class="header-container">
        <h1 class="header-title">Battery Trading Assistant</h1>
        <p class="header-subtitle">AI-powered insights for battery operations and trading</p>
    </div>
    """, unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### ⚡ Quick Actions")
    
    # Status indicator
    if AGENT_AVAILABLE:
        st.markdown("""
        <div style="margin-bottom: 1rem;">
            <span class="status-indicator status-online"></span>
            <strong>System Online</strong>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="margin-bottom: 1rem;">
            <span class="status-indicator status-offline"></span>
            <strong>System Offline</strong>
        </div>
        """, unsafe_allow_html=True)
        st.error(f"Agent not available: {AGENT_ERROR}")
    
    st.markdown("---")
    
    st.markdown("### 📊 Quick Queries")
    
    quick_queries = [
        "What is the current SoC for RESS2?",
        "Show me revenue for all batteries",
        "How is throughput calculated?",
        "What are the SoC limits?",
        "Get battery asset information"
    ]
    
    # Quick query buttons - just set the query, processing happens in main area
    for query in quick_queries:
        if st.button(f"💬 {query[:40]}...", key=f"quick_{hash(query)}"):
            if AGENT_AVAILABLE:
                # Set query to be processed in main area
                st.session_state.pending_query = query
            else:
                st.error("Agent not available")
    
    st.markdown("---")
    
    st.markdown("### ℹ️ About")
    st.markdown("""
    This assistant helps you:
    - Monitor battery status
    - Analyze trading performance
    - Access technical documentation
    - Get asset information
    """)
    
    st.markdown("---")
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []

# Main chat interface
st.markdown("### 💬 Chat with Assistant")

def extract_sources(response_messages):
    """Extract tool calls and results from agent response"""
    sources = {
        "vector_search": [],
        "sql_queries": [],
        "tools_used": []
    }
    
    # Track tool calls and their results
    tool_calls_map = {}
    
    for msg in response_messages:
        # Check for tool calls (AIMessage with tool_calls)
        if isinstance(msg, AIMessage):
            # Try different ways to access tool_calls
            tool_calls = None
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                tool_calls = msg.tool_calls
            elif hasattr(msg, 'tool_calls') and isinstance(msg.tool_calls, list):
                tool_calls = msg.tool_calls
            
            if tool_calls:
                for tool_call in tool_calls:
                    # Handle both dict and object tool_calls
                    if isinstance(tool_call, dict):
                        tool_call_id = tool_call.get('id') or tool_call.get('name')
                        tool_name = tool_call.get('name', '')
                        tool_args = tool_call.get('args', {})
                    else:
                        tool_call_id = getattr(tool_call, 'id', None) or getattr(tool_call, 'name', None)
                        tool_name = getattr(tool_call, 'name', '')
                        tool_args = getattr(tool_call, 'args', {})
                    
                    if tool_call_id:
                        tool_calls_map[tool_call_id] = {
                            'name': tool_name,
                            'args': tool_args if isinstance(tool_args, dict) else {}
                        }
        
        # Check for tool results (ToolMessage)
        if isinstance(msg, ToolMessage):
            # Try multiple ways to get tool_call_id
            tool_call_id = (
                getattr(msg, 'tool_call_id', None) or 
                getattr(msg, 'name', None) or
                (hasattr(msg, 'id') and msg.id) or
                None
            )
            
            # Get tool name from message
            tool_name = getattr(msg, 'name', None)
            
            if tool_call_id and tool_call_id in tool_calls_map:
                tool_info = tool_calls_map[tool_call_id]
                tool_name = tool_info['name']
                
                # Categorize tools
                if tool_name == 'search_battery_docs':
                    sources["tools_used"].append("Vector Search")
                    sources["vector_search"].append({
                        "query": tool_info['args'].get('query', ''),
                        "result": msg.content
                    })
                elif tool_name in ['get_battery_status', 'get_battery_revenue', 'get_battery_info']:
                    sources["tools_used"].append("SQL Query")
                    sources["sql_queries"].append({
                        "tool": tool_name,
                        "args": tool_info['args'],
                        "result": msg.content
                    })
            # Fallback: try to match by tool name
            elif tool_name:
                if tool_name == 'search_battery_docs':
                    sources["tools_used"].append("Vector Search")
                    sources["vector_search"].append({
                        "query": "Query from tool",
                        "result": msg.content
                    })
                elif tool_name in ['get_battery_status', 'get_battery_revenue', 'get_battery_info']:
                    sources["tools_used"].append("SQL Query")
                    sources["sql_queries"].append({
                        "tool": tool_name,
                        "args": {},
                        "result": msg.content
                    })
    
    return sources

# Display chat history using Streamlit's chat components
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Display sources if available
        if message["role"] == "assistant" and "sources" in message:
            sources = message["sources"]
            if sources["tools_used"]:
                st.markdown("---")
                tools_used_str = ", ".join(set(sources["tools_used"]))
                st.caption(f"📊 **Sources:** {tools_used_str}")
                
                # Show expanders for detailed results
                if sources["vector_search"]:
                    with st.expander("🔍 Vector Search Results", expanded=False):
                        for vs_idx, vs_result in enumerate(sources["vector_search"], 1):
                            st.markdown(f"**Query {vs_idx}:** {vs_result['query']}")
                            st.text_area("Result:", vs_result['result'], height=150, key=f"hist_vs_{idx}_{vs_idx}", label_visibility="collapsed")
                
                if sources["sql_queries"]:
                    with st.expander("💾 SQL Query Results", expanded=False):
                        for sql_idx, sql_result in enumerate(sources["sql_queries"], 1):
                            st.markdown(f"**Tool:** `{sql_result['tool']}`")
                            st.markdown(f"**Arguments:** `{json.dumps(sql_result['args'], indent=2)}`")
                            st.text_area("Result:", sql_result['result'], height=150, key=f"hist_sql_{idx}_{sql_idx}", label_visibility="collapsed")

# Process pending query from sidebar (non-blocking)
if "pending_query" in st.session_state and st.session_state.pending_query:
    prompt = st.session_state.pending_query
    st.session_state.pending_query = None  # Clear it
    
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get agent response
    with st.chat_message("assistant"):
        with st.spinner("🤔 Thinking..."):
            try:
                # Invoke agent
                response = agent.invoke({
                    "messages": [
                        SystemMessage(content=SYSTEM_PROMPT),
                        HumanMessage(content=prompt)
                    ]
                })
                
                # Extract sources
                sources = extract_sources(response["messages"])
                
                # Get assistant response
                assistant_response = response["messages"][-1].content
                st.markdown(assistant_response)
                
                # Display sources
                if sources["tools_used"]:
                    st.markdown("---")
                    tools_used_str = ", ".join(set(sources["tools_used"]))
                    st.caption(f"📊 **Sources:** {tools_used_str}")
                    
                    # Show expanders for detailed results
                    if sources["vector_search"]:
                        with st.expander("🔍 Vector Search Results", expanded=False):
                            for idx, vs_result in enumerate(sources["vector_search"], 1):
                                st.markdown(f"**Query {idx}:** {vs_result['query']}")
                                st.text_area("Result:", vs_result['result'], height=150, key=f"vs_{idx}", label_visibility="collapsed")
                    
                    if sources["sql_queries"]:
                        with st.expander("💾 SQL Query Results", expanded=False):
                            for idx, sql_result in enumerate(sources["sql_queries"], 1):
                                st.markdown(f"**Tool:** `{sql_result['tool']}`")
                                st.markdown(f"**Arguments:** `{json.dumps(sql_result['args'], indent=2)}`")
                                st.text_area("Result:", sql_result['result'], height=150, key=f"sql_{idx}", label_visibility="collapsed")
                
                # Add to session state with sources
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_response,
                    "sources": sources
                })
                
            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })

# Chat input - process immediately
if AGENT_AVAILABLE:
    if prompt := st.chat_input("Ask a question about battery operations, trading, or technical documentation..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get agent response
        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking..."):
                try:
                    # Invoke agent
                    response = agent.invoke({
                        "messages": [
                            SystemMessage(content=SYSTEM_PROMPT),
                            HumanMessage(content=prompt)
                        ]
                    })
                    
                    # Extract sources
                    sources = extract_sources(response["messages"])
                    
                    # Get assistant response
                    assistant_response = response["messages"][-1].content
                    st.markdown(assistant_response)
                    
                    # Display sources
                    if sources["tools_used"]:
                        st.markdown("---")
                        tools_used_str = ", ".join(set(sources["tools_used"]))
                        st.caption(f"📊 **Sources:** {tools_used_str}")
                        
                        # Show expanders for detailed results
                        if sources["vector_search"]:
                            with st.expander("🔍 Vector Search Results", expanded=False):
                                for idx, vs_result in enumerate(sources["vector_search"], 1):
                                    st.markdown(f"**Query {idx}:** {vs_result['query']}")
                                    st.text_area("Result:", vs_result['result'], height=150, key=f"chat_vs_{idx}", label_visibility="collapsed")
                        
                        if sources["sql_queries"]:
                            with st.expander("💾 SQL Query Results", expanded=False):
                                for idx, sql_result in enumerate(sources["sql_queries"], 1):
                                    st.markdown(f"**Tool:** `{sql_result['tool']}`")
                                    st.markdown(f"**Arguments:** `{json.dumps(sql_result['args'], indent=2)}`")
                                    st.text_area("Result:", sql_result['result'], height=150, key=f"chat_sql_{idx}", label_visibility="collapsed")
                    
                    # Add to session state with sources
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_response,
                        "sources": sources
                    })
                    
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })
else:
    st.warning("⚠️ Agent is not available. Please ensure the agent script is properly configured.")

# Footer
st.markdown("""
<div class="footer">
    <p>© 2024 Energy Australia | Battery Trading Assistant | Powered by Databricks Mosaic AI</p>
</div>
""", unsafe_allow_html=True)

