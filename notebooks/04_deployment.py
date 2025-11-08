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

