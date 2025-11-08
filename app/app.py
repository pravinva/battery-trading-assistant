import streamlit as st
import sys
import os
from pathlib import Path

# Add parent directory to path to import agent
sys.path.append(str(Path(__file__).parent.parent))

from langchain_core.messages import HumanMessage, SystemMessage
import importlib.util
from pathlib import Path

# Try to import agent - handle if not available
# Note: Can't use normal import because module name starts with number
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
    
    for query in quick_queries:
        if st.button(f"💬 {query[:40]}...", key=f"quick_{hash(query)}"):
            if AGENT_AVAILABLE:
                st.session_state.messages.append({"role": "user", "content": query})
                st.rerun()
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
        st.rerun()

# Main chat interface
st.markdown("### 💬 Chat with Assistant")

# Display chat history
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f"""
        <div class="user-message">
            <strong>You:</strong><br>
            {message["content"]}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="assistant-message">
            <strong>Assistant:</strong><br>
            {message["content"]}
        </div>
        """, unsafe_allow_html=True)

# Chat input
if AGENT_AVAILABLE:
    user_input = st.text_input(
        "Ask a question about battery operations, trading, or technical documentation:",
        key="user_input",
        placeholder="e.g., What is RESS2 current SoC?"
    )
    
    col1, col2 = st.columns([1, 10])
    with col1:
        send_button = st.button("Send", type="primary")
    
    # Process user input
    if send_button and user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Show loading
        with st.spinner("🤔 Thinking..."):
            try:
                # Invoke agent
                response = agent.invoke({
                    "messages": [
                        SystemMessage(content=SYSTEM_PROMPT),
                        HumanMessage(content=user_input)
                    ]
                })
                
                # Get assistant response
                assistant_response = response["messages"][-1].content
                
                # Add assistant message
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_response
                })
                
            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })
        
        st.rerun()
else:
    st.warning("⚠️ Agent is not available. Please ensure the agent script is properly configured.")

# Footer
st.markdown("""
<div class="footer">
    <p>© 2024 Energy Australia | Battery Trading Assistant | Powered by Databricks Mosaic AI</p>
</div>
""", unsafe_allow_html=True)

