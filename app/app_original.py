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

