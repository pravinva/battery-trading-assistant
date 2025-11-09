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
import re
import plotly.graph_objects as go

# Cache agent initialization to avoid reloading on every page refresh
# Use file modification time to bust cache when file changes
@st.cache_resource
def load_agent(_file_mtime, _force_reload=False):
    """Load agent lazily - only when needed
    
    Args:
        _file_mtime: File modification time (used for cache busting)
        _force_reload: Force reload even if cached
    """
    AGENT_AVAILABLE = False
    AGENT_ERROR = None
    agent = None
    SYSTEM_PROMPT = None
    INDEX_NAME = None
    GENIE_ROOM_ID = None
    
    try:
        agent_script_path = Path(__file__).parent.parent / "scripts" / "02_agent_development_local.py"
        if agent_script_path.exists():
            # Clear any cached module to force reload
            import sys
            import importlib
            module_name = "agent_module"
            # Clear ALL cached modules related to agent - MORE AGGRESSIVE
            modules_to_remove = [k for k in sys.modules.keys() if 'agent' in k.lower() or '02_agent' in k.lower() or 'scripts' in k.lower()]
            for mod in modules_to_remove:
                if mod in sys.modules:
                    del sys.modules[mod]
            
            # Also clear importlib cache
            importlib.invalidate_caches()
            
            # Set USE_GENIE_MCP environment variable before loading module
            # This ensures the agent module uses the correct MCP setting
            if 'use_genie_mcp' in st.session_state:
                os.environ["USE_GENIE_MCP"] = "true" if st.session_state.use_genie_mcp else "false"
            elif "USE_GENIE_MCP" not in os.environ:
                os.environ["USE_GENIE_MCP"] = "false"
            
            spec = importlib.util.spec_from_file_location(module_name, agent_script_path)
            agent_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(agent_module)
            agent = agent_module.agent
            SYSTEM_PROMPT = agent_module.SYSTEM_PROMPT
            # Get configuration values
            INDEX_NAME = getattr(agent_module, 'INDEX_NAME', None)
            GENIE_ROOM_ID = getattr(agent_module, 'GENIE_ROOM_ID', None) or os.environ.get("GENIE_ROOM_ID", None)
            
            # Store agent module reference for log access
            st.session_state.agent_module = agent_module
            
            # Verify tools list - should only have search_battery_docs and query_genie
            if hasattr(agent_module, 'tools'):
                tools_list = agent_module.tools
                tool_names = [t.name for t in tools_list]
                if 'get_battery_status' in tool_names or 'get_battery_revenue' in tool_names or 'get_battery_info' in tool_names:
                    AGENT_ERROR = f"ERROR: Old SQL tools still present: {tool_names}. Expected only: ['search_battery_docs', 'query_genie']"
                    AGENT_AVAILABLE = False
                else:
                    AGENT_AVAILABLE = True
            else:
                AGENT_AVAILABLE = True
        else:
            AGENT_ERROR = f"Agent script not found at {agent_script_path}"
    except Exception as e:
        AGENT_AVAILABLE = False
        AGENT_ERROR = str(e)
    
    return AGENT_AVAILABLE, agent, SYSTEM_PROMPT, AGENT_ERROR, INDEX_NAME, GENIE_ROOM_ID

# Get file modification time for cache busting
agent_script_path = Path(__file__).parent.parent / "scripts" / "02_agent_development_local.py"
file_mtime = agent_script_path.stat().st_mtime if agent_script_path.exists() else 0

# Initialize session state for MCP toggle before loading agent
if 'use_genie_mcp' not in st.session_state:
    st.session_state.use_genie_mcp = os.environ.get("USE_GENIE_MCP", "false").lower() == "true"

# Set environment variable based on session state
os.environ["USE_GENIE_MCP"] = "true" if st.session_state.use_genie_mcp else "false"

# Load agent (cached, but cache invalidates when file changes)
AGENT_AVAILABLE, agent, SYSTEM_PROMPT, AGENT_ERROR, INDEX_NAME, GENIE_ROOM_ID = load_agent(file_mtime)

# Get Genie room name from ID
@st.cache_resource
def get_genie_room_name(_room_id):
    """Get Genie room name from ID"""
    if not _room_id:
        return None
    try:
        from databricks.sdk import WorkspaceClient
        w = WorkspaceClient()
        if hasattr(w, 'genie'):
            genie = w.genie
            spaces_response = genie.list_spaces()
            spaces = spaces_response.spaces if hasattr(spaces_response, 'spaces') else spaces_response
            for space in spaces:
                space_id = getattr(space, 'space_id', getattr(space, 'id', None))
                if space_id == _room_id:
                    return getattr(space, 'title', getattr(space, 'name', None))
    except Exception:
        pass
    return None

GENIE_ROOM_NAME = get_genie_room_name(GENIE_ROOM_ID) if GENIE_ROOM_ID else None

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
    /* Energy Australia Brand Colors - Green Theme */
    :root {
        --ea-primary-green: #00A651;
        --ea-dark-green: #007A3D;
        --ea-light-green: #E6F5ED;
        --ea-accent-green: #00C85C;
        --ea-text-dark: #1A1A1A;
        --ea-text-gray: #666666;
        --ea-text-light-gray: #999999;
        --ea-bg-light: #F8F9FA;
        --ea-border: #E0E0E0;
        --ea-white: #FFFFFF;
    }
    
    /* Import Energy Australia font style */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Main container */
    .main {
        background-color: var(--ea-bg-light);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    /* Header - Energy Australia Style - Green Theme */
    .header-container {
        background: linear-gradient(135deg, #00A651 0%, #00C85C 100%);
        padding: 2rem 2.5rem;
        border-radius: 0;
        margin: -1rem -1rem 2rem -1rem;
        box-shadow: 0 2px 8px rgba(0, 166, 81, 0.2);
        position: relative;
        overflow: hidden;
    }
    
    .header-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: repeating-linear-gradient(
            45deg,
            transparent,
            transparent 10px,
            rgba(255, 255, 255, 0.03) 10px,
            rgba(255, 255, 255, 0.03) 20px
        );
        pointer-events: none;
    }
    
    .header-title {
        color: var(--ea-white);
        font-size: 2.25rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.02em;
        position: relative;
        z-index: 1;
    }
    
    .header-subtitle {
        color: rgba(255, 255, 255, 0.95);
        font-size: 1.1rem;
        margin-top: 0.75rem;
        font-weight: 400;
        position: relative;
        z-index: 1;
        line-height: 1.6;
    }
    
    .header-subtitle code {
        background: rgba(255, 255, 255, 0.25) !important;
        color: #FFFFFF !important;
        padding: 4px 8px !important;
        border-radius: 4px !important;
        font-weight: 500 !important;
        font-size: 0.95em !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
    }
    
    /* Chat container - Clean Energy Australia Style */
    .chat-container {
        background-color: var(--ea-white);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
        margin-bottom: 1rem;
        border: 1px solid var(--ea-border);
    }
    
    /* User message - Energy Australia Green */
    .user-message {
        background-color: var(--ea-primary-green);
        color: var(--ea-white);
        padding: 1rem 1.25rem;
        border-radius: 12px 12px 4px 12px;
        margin-bottom: 1rem;
        margin-left: 20%;
        box-shadow: 0 2px 4px rgba(0, 166, 81, 0.2);
        font-weight: 400;
    }
    
    /* Assistant message - Clean White with Green Accent */
    .assistant-message {
        background-color: var(--ea-white);
        color: var(--ea-text-dark);
        padding: 1rem 1.25rem;
        border-radius: 12px 12px 12px 4px;
        margin-bottom: 1rem;
        margin-right: 20%;
        border-left: 3px solid var(--ea-primary-green);
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
        border: 1px solid var(--ea-border);
    }
    
    /* Input area - Energy Australia Style */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 1.5px solid var(--ea-border);
        padding: 0.875rem 1rem;
        font-size: 0.95rem;
        transition: all 0.2s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--ea-primary-green);
        box-shadow: 0 0 0 3px rgba(0, 166, 81, 0.1);
        outline: none;
    }
    
    /* Button styling - Energy Australia Primary Green */
    .stButton > button {
        background-color: var(--ea-primary-green);
        color: var(--ea-white);
        border-radius: 8px;
        border: none;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.2s ease;
        width: 100%;
        box-shadow: 0 2px 4px rgba(0, 166, 81, 0.2);
    }
    
    .stButton > button:hover {
        background-color: var(--ea-accent-green);
        box-shadow: 0 4px 8px rgba(0, 166, 81, 0.3);
        transform: translateY(-1px);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Status indicator - Energy Australia Style */
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 8px;
        box-shadow: 0 0 0 2px rgba(0, 166, 81, 0.2);
    }
    
    .status-online {
        background-color: var(--ea-primary-green);
    }
    
    .status-offline {
        background-color: var(--ea-text-light-gray);
    }
    
    /* Footer - Energy Australia Style */
    .footer {
        text-align: center;
        padding: 1.5rem;
        color: var(--ea-text-gray);
        font-size: 0.875rem;
        margin-top: 3rem;
        border-top: 1px solid var(--ea-border);
        background-color: var(--ea-white);
    }
    
    /* Markdown styling - Clean Typography */
    .stMarkdown {
        line-height: 1.7;
        color: var(--ea-text-dark);
    }
    
    .stMarkdown strong {
        color: var(--ea-text-dark);
        font-weight: 600;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: var(--ea-white);
    }
    
    /* Chat message bubbles */
    [data-testid="stChatMessage"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: var(--ea-primary-green);
    }
    
    /* Caption styling for sources */
    .stCaption {
        color: var(--ea-text-gray);
        font-size: 0.875rem;
    }
    
    /* Overall page styling */
    .stApp {
        background-color: var(--ea-bg-light);
    }
    
    /* Hide Streamlit menu and footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
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
    # Build subtitle with Genie room and Vector Index info
    subtitle_parts = ["AI-powered insights for battery operations and trading"]
    
    if INDEX_NAME:
        # Shorten index name for display
        index_display = INDEX_NAME.split('.')[-1] if '.' in INDEX_NAME else INDEX_NAME
        subtitle_parts.append(f"Vector Index: <code>{index_display}</code>")
    
    if GENIE_ROOM_NAME:
        subtitle_parts.append(f"Genie Room: <code>{GENIE_ROOM_NAME}</code>")
    elif GENIE_ROOM_ID:
        # Fallback to ID if name not available
        subtitle_parts.append(f"Genie Room: <code>{GENIE_ROOM_ID[:8]}...</code>")
    
    subtitle_html = " | ".join(subtitle_parts)
    
    st.markdown(f"""
    <div class="header-container">
        <h1 class="header-title">Battery Trading Assistant</h1>
        <p class="header-subtitle">{subtitle_html}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Add Energy Australia tagline
    st.markdown("""
    <div style="margin-top: -1rem; margin-bottom: 1.5rem; padding-left: 0.5rem;">
        <p style="color: var(--ea-text-gray); font-size: 0.9rem; margin: 0; font-style: italic;">
            We're on it
        </p>
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
    
    # Genie MCP Toggle
    st.markdown("### 🔌 Configuration")
    
    # Toggle button for Genie MCP
    use_mcp = st.toggle(
        "Use Genie MCP Server",
        value=st.session_state.use_genie_mcp,
        help="Enable to use Genie via Model Context Protocol (MCP) instead of direct API. Requires databricks-mcp package."
    )
    
    # Update session state and environment variable if changed
    if use_mcp != st.session_state.use_genie_mcp:
        st.session_state.use_genie_mcp = use_mcp
        os.environ["USE_GENIE_MCP"] = "true" if use_mcp else "false"
        # Clear agent cache to reload with new setting
        load_agent.clear()
        st.rerun()
    
    # Show current MCP status
    if use_mcp:
        st.success("✅ Genie MCP enabled")
    else:
        st.info("ℹ️ Using direct Genie API")
    
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

def extract_plotly_charts(response_text):
    """Extract Plotly chart JSON from response text"""
    charts = []
    
    # Find all chart markers - be more flexible with whitespace and code blocks
    # Handle cases where markers might be after code block closers (```)
    # First, try to find markers even if they're inside code blocks or after them
    pattern = r'(?:```[^\n]*\n)?\[PLOTLY_CHART_START\]\s*(.*?)\s*\[PLOTLY_CHART_END\](?:[^\n]*\n```)?'
    matches = re.findall(pattern, response_text, re.DOTALL | re.MULTILINE)
    
    # Debug: Check if markers are found (silent - no UI messages)
    # Charts are optional, so don't show warnings if they're not present
    
    for idx, match in enumerate(matches):
        try:
            # Clean up the match - remove any extra whitespace or code block markers
            match_clean = match.strip()
            
            # Handle nested JSON string (when json field contains a JSON string)
            # The chart_data structure is: {"type": "line", "json": "{\"data\":[...]}"}
            # So we need to parse the outer JSON first
            chart_data = json.loads(match_clean)
            
            # Handle nested JSON structure
            # chart_data might be: {"type": "line", "json": {...}, "title": "..."}
            # OR: {"type": "line", "json": "{...}", "title": "..."}  (nested JSON string)
            if isinstance(chart_data, dict) and 'json' in chart_data:
                chart_json = chart_data.get('json')
                
                # If json field is a string, parse it
                if isinstance(chart_json, str):
                    try:
                        chart_json = json.loads(chart_json)
                        chart_data['json'] = chart_json
                    except json.JSONDecodeError as parse_err:
                        # If inner JSON parsing fails, try to extract just the dict part
                        # Sometimes the JSON string might have extra escaping
                        try:
                            # Remove extra escaping
                            chart_json_clean = chart_json.replace('\\"', '"').replace('\\n', '\n')
                            chart_json = json.loads(chart_json_clean)
                            chart_data['json'] = chart_json
                        except:
                            # If still fails, keep it as string and let render handle it
                            pass
                
                charts.append(chart_data)
            else:
                # Direct chart JSON (unlikely but handle it)
                charts.append({'json': chart_data})
            
            # Chart parsed successfully - no need to show success message
        except json.JSONDecodeError as e:
            # Only show error if DEBUG mode is enabled
            if os.environ.get("DEBUG", "false").lower() == "true":
                st.error(f"Could not parse chart data {idx + 1}: {e}")
                st.code(f"Match length: {len(match)}, First 500 chars: {match[:500]}", language='text')
                # Try to find where the JSON starts
                json_start = match.find('{')
                if json_start > 0:
                    st.code(f"JSON starts at position {json_start}, content: {match[json_start:json_start+200]}", language='text')
    
    return charts

def render_response_with_charts(response_text):
    """Render response text, extracting and displaying any Plotly charts"""
    charts = extract_plotly_charts(response_text)
    
    # Remove chart markers from text
    cleaned_text = re.sub(r'\[PLOTLY_CHART_START\].*?\[PLOTLY_CHART_END\]', '', response_text, flags=re.DOTALL)
    
    # Display cleaned text
    st.markdown(cleaned_text)
    
    # Display charts
    if charts:
        st.markdown("---")
        st.markdown("### 📊 Chart Visualization")
    for idx, chart_data in enumerate(charts):
        try:
            # Recreate Plotly figure from JSON
            # chart_data structure: {"type": "line", "json": {...}, "title": "..."}
            # The 'json' field might be a dict or a string
            chart_json = chart_data.get('json')
            
            # chart_json should be a dict with 'data' and 'layout' keys
            if isinstance(chart_json, dict):
                # Create figure directly from dict
                fig = go.Figure(chart_json)
            elif isinstance(chart_json, str):
                # Backward compatibility: parse JSON string to dict
                chart_dict = json.loads(chart_json)
                fig = go.Figure(chart_dict)
            else:
                raise ValueError(f"Chart JSON is neither string nor dict: {type(chart_json)}")
            
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            # Only show error if DEBUG mode is enabled
            if os.environ.get("DEBUG", "false").lower() == "true":
                st.error(f"Could not render chart {idx + 1}: {str(e)}")
                import traceback
                st.code(traceback.format_exc(), language='text')
                st.code(f"Chart data keys: {list(chart_data.keys()) if isinstance(chart_data, dict) else 'N/A'}", language='text')
                st.code(f"Chart JSON type: {type(chart_data.get('json'))}, value preview: {str(chart_data.get('json', ''))[:200]}", language='text')
    # No charts found - silently continue (charts are optional)

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
                elif tool_name in ['get_battery_status', 'get_battery_revenue', 'get_battery_info', 'query_genie']:
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
                elif tool_name in ['get_battery_status', 'get_battery_revenue', 'get_battery_info', 'query_genie']:
                    sources["tools_used"].append("SQL Query")
                    sources["sql_queries"].append({
                        "tool": tool_name,
                        "args": {},
                        "result": msg.content
                    })
    
    return sources

def build_message_history():
    """Convert Streamlit session state messages to LangChain message objects"""
    langchain_messages = [SystemMessage(content=SYSTEM_PROMPT)]
    
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            langchain_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            langchain_messages.append(AIMessage(content=msg["content"]))
    
    return langchain_messages

# Display chat history using Streamlit's chat components
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        # Use render_response_with_charts for assistant messages
        if message["role"] == "assistant":
            render_response_with_charts(message["content"])
        else:
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
                            tool_name = sql_result['tool']
                            if tool_name == 'query_genie':
                                st.markdown(f"**Tool:** `{tool_name}` (🤖 **Databricks Genie - Dynamic SQL Generation**)")
                                if 'question' in sql_result.get('args', {}):
                                    st.markdown(f"**Natural Language Question:** {sql_result['args']['question']}")
                                
                                # Note: Execution logs are only available for current session queries
                                # Historical queries won't have logs as they're cleared after reading
                                
                                # Extract SQL query from Genie response if present
                                result_text = sql_result.get('result', '')
                                if '```sql' in result_text:
                                    # Extract SQL from markdown code block
                                    sql_start = result_text.find('```sql') + 6
                                    sql_end = result_text.find('```', sql_start)
                                    if sql_end > sql_start:
                                        genie_sql = result_text[sql_start:sql_end].strip()
                                        st.markdown("**🔍 Dynamically Generated SQL:**")
                                        st.code(genie_sql, language='sql')
                                        st.caption("✨ This SQL was generated by Genie based on your natural language question - not hardcoded!")
                                
                                st.markdown("**Genie Response:**")
                                st.text_area("Result:", result_text, height=200, key=f"hist_genie_{idx}_{sql_idx}", label_visibility="collapsed")
                            else:
                                st.markdown(f"**Tool:** `{tool_name}` (Predefined SQL Tool)")
                                if sql_result.get('args'):
                                    st.markdown(f"**Arguments:** `{json.dumps(sql_result['args'], indent=2)}`")
                                st.text_area("Result:", sql_result['result'], height=200, key=f"hist_sql_{idx}_{sql_idx}", label_visibility="collapsed")

# Process pending query from sidebar (non-blocking)
if "pending_query" in st.session_state and st.session_state.pending_query:
    prompt = st.session_state.pending_query
    st.session_state.pending_query = None  # Clear it
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get agent response
    with st.chat_message("assistant"):
        with st.spinner("🤔 Thinking..."):
            try:
                # Build full conversation history (before adding current prompt to session state)
                message_history = build_message_history()
                # Add current prompt to history
                message_history.append(HumanMessage(content=prompt))
                
                # Invoke agent with full conversation history
                response = agent.invoke({
                    "messages": message_history
                })
                
                # NOW add user message to session state (after agent invocation)
                st.session_state.messages.append({"role": "user", "content": prompt})
                
                # Extract sources
                sources = extract_sources(response["messages"])
                
                # Get assistant response
                assistant_response = response["messages"][-1].content
                render_response_with_charts(assistant_response)
                
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
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get agent response
        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking..."):
                try:
                    # Build full conversation history (before adding current prompt to session state)
                    message_history = build_message_history()
                    # Add current prompt to history
                    message_history.append(HumanMessage(content=prompt))
                    
                    # Invoke agent with full conversation history
                    response = agent.invoke({
                        "messages": message_history
                    })
                    
                    # NOW add user message to session state (after agent invocation)
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    
                    # Extract sources
                    sources = extract_sources(response["messages"])
                    
                    # Get assistant response
                    assistant_response = response["messages"][-1].content
                    render_response_with_charts(assistant_response)
                    
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
                                for sql_idx, sql_result in enumerate(sources["sql_queries"], 1):
                                    tool_name = sql_result['tool']
                                    if tool_name == 'query_genie':
                                        st.markdown(f"**Tool:** `{tool_name}` (🤖 **Databricks Genie - Dynamic SQL Generation**)")
                                        if 'question' in sql_result.get('args', {}):
                                            st.markdown(f"**Natural Language Question:** {sql_result['args']['question']}")
                                        
                                        # Get execution logs from agent module stored in session state
                                        try:
                                            agent_module_logs = st.session_state.get('agent_module')
                                            if agent_module_logs and hasattr(agent_module_logs, 'get_genie_logs'):
                                                try:
                                                    logs = agent_module_logs.get_genie_logs()
                                                    if logs:
                                                        with st.expander("📋 Execution Logs (MCP vs Direct API)", expanded=True):
                                                            for log_entry in logs:
                                                                st.text(log_entry)
                                                except Exception as log_error:
                                                    # Silently fail if log retrieval fails - don't break the UI
                                                    if os.environ.get("DEBUG", "false").lower() == "true":
                                                        st.caption(f"⚠️ Could not retrieve logs: {log_error}")
                                        except Exception as e:
                                            # Silently fail if logs not available - don't break the UI
                                            pass
                                        
                                        # Extract SQL query from Genie response if present
                                        result_text = sql_result.get('result', '')
                                        if '```sql' in result_text:
                                            # Extract SQL from markdown code block
                                            sql_start = result_text.find('```sql') + 6
                                            sql_end = result_text.find('```', sql_start)
                                            if sql_end > sql_start:
                                                genie_sql = result_text[sql_start:sql_end].strip()
                                                st.markdown("**🔍 Dynamically Generated SQL:**")
                                                st.code(genie_sql, language='sql')
                                                st.caption("✨ This SQL was generated by Genie based on your natural language question - not hardcoded!")
                                        
                                        st.markdown("**Genie Response:**")
                                        st.text_area("Result:", result_text, height=200, key=f"chat_genie_{sql_idx}", label_visibility="collapsed")
                                    else:
                                        st.markdown(f"**Tool:** `{tool_name}` (Predefined SQL Tool)")
                                        if sql_result.get('args'):
                                            st.markdown(f"**Arguments:** `{json.dumps(sql_result['args'], indent=2)}`")
                                        st.text_area("Result:", sql_result['result'], height=200, key=f"chat_sql_{sql_idx}", label_visibility="collapsed")
                    
                    # Add to session state with sources
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_response,
                        "sources": sources
                    })
                    
                except Exception as e:
                    import traceback
                    error_traceback = traceback.format_exc()
                    
                    # More detailed error message
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    
                    # Show error in UI
                    st.error(error_msg)
                    
                    # Show full traceback in expander for debugging
                    with st.expander("🔍 Error Details (Click to expand)", expanded=False):
                        st.code(error_traceback, language='text')
                        
                        # Check for specific error types
                        error_str = str(e).lower()
                        if "broken pipe" in error_str or "errno 32" in error_str:
                            st.info("💡 **Network Connection Issue**: This is typically a temporary network problem. Please try again in a few seconds.")
                        elif "json" in error_str and ("local variable" in error_str or "not defined" in error_str):
                            st.warning("💡 **Module Reload Issue**: Please refresh the page or restart Streamlit to reload the module.")
                        elif "mcp" in error_str or "client" in error_str:
                            st.info("💡 **MCP Client Issue**: Check that:\n- `databricks-mcp` is installed\n- MCP server is enabled in workspace\n- Genie MCP toggle is enabled in sidebar")
                    
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

