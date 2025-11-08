# Quick Start Guide

## Prerequisites Check

1. ✅ Databricks CLI configured (`~/.databrickscfg` exists)
2. ✅ Virtual environment created (`venv/` directory)
3. ✅ Dependencies installed (`pip install -r requirements.txt`)

## Step-by-Step Execution

### Step 1: Upload PDF to Databricks

```bash
# Option 1: Using Databricks CLI
databricks fs cp data/battery.pdf dbfs:/Volumes/ea_trading/battery_trading/pdfs/battery.pdf

# Option 2: Upload via Databricks UI
# Go to Catalog → Volumes → ea_trading/battery_trading/pdfs → Upload battery.pdf
```

### Step 2: Upload Notebooks

```bash
# Get your Databricks email/username
USER_EMAIL="your.email@company.com"  # Update this!

# Upload notebooks
databricks workspace import notebooks/01_data_preparation.py "/Users/${USER_EMAIL}/battery-trading/01_data_preparation" --language PYTHON
databricks workspace import notebooks/02_agent_development.py "/Users/${USER_EMAIL}/battery-trading/02_agent_development" --language PYTHON
databricks workspace import notebooks/03_agent_evaluation.py "/Users/${USER_EMAIL}/battery-trading/03_agent_evaluation" --language PYTHON
databricks workspace import notebooks/04_deployment.py "/Users/${USER_EMAIL}/battery-trading/04_deployment" --language PYTHON
```

Or upload manually via Databricks UI:
1. Workspace → Create → Notebook
2. Upload each `.py` file

### Step 3: Run Notebooks Sequentially

#### 3.1 Run `01_data_preparation.py`
- **Purpose**: Create Delta tables and Vector Search index
- **Time**: ~10-15 minutes
- **Check**: 
  - ✅ Tables created: `battery_assets`, `battery_telemetry`, `battery_dispatch`, `battery_documents`
  - ✅ Vector Search endpoint: `ea_trading_endpoint`
  - ✅ Vector Search index: `ea_trading.battery_trading.battery_docs_index`

#### 3.2 Run `02_agent_development.py`
- **Purpose**: Build and test agent
- **Time**: ~5-10 minutes
- **Important**: Copy the MLflow Run ID from output!
- **Check**:
  - ✅ Agent created successfully
  - ✅ Test queries work
  - ✅ MLflow run ID saved

#### 3.3 Run `03_agent_evaluation.py`
- **Purpose**: Evaluate agent performance
- **Time**: ~10-15 minutes
- **Before running**: Update `AGENT_RUN_ID` with value from notebook 02
- **Check**:
  - ✅ Evaluation metrics displayed
  - ✅ Results table shown

#### 3.4 Run `04_deployment.py`
- **Purpose**: Deploy to production
- **Time**: ~15-20 minutes (includes endpoint deployment wait)
- **Before running**: Update `AGENT_RUN_ID` with value from notebook 02
- **Before running**: Update `<your_email>` in app creation section
- **Check**:
  - ✅ Model registered in Unity Catalog
  - ✅ Serving endpoint deployed and ready
  - ✅ App files created

### Step 4: Launch Databricks App

1. Go to Databricks Apps in workspace
2. Click "Create App"
3. Select source path: `/Workspace/Users/<your_email>/battery-trading-app`
4. Click "Create"
5. Launch and test!

## Common Issues & Solutions

### Issue: "Vector Search endpoint not found"
**Solution**: Ensure notebook 01 completed successfully. Check endpoint name matches `ea_trading_endpoint`.

### Issue: "PDF not found at /Volumes/..."
**Solution**: Upload battery.pdf to the correct volume path. Create volume if needed:
```sql
CREATE VOLUME IF NOT EXISTS ea_trading.battery_trading.pdfs;
```

### Issue: "Model serving endpoint not ready"
**Solution**: Wait longer (can take 10-15 minutes). Check endpoint status in Databricks UI under Model Serving.

### Issue: "Permission denied" errors
**Solution**: Ensure you have:
- CREATE permissions on catalog `ea_trading`
- USE CATALOG and USE SCHEMA permissions
- Vector Search access
- Model Serving access

## Testing the Agent

Once deployed, test with these queries:

1. **Structured Query**: "What is the current SoC for RESS2?"
2. **Unstructured Query**: "How is throughput calculated?"
3. **Hybrid Query**: "What's DPNTBESS current SoC and what are the SoC limits?"
4. **Revenue Query**: "Show revenue for all batteries in last 24 hours"

## Next Steps

- Customize system prompt in `agent/agent.py`
- Add more evaluation questions in notebook 03
- Enhance Streamlit UI in `app/app.py`
- Add more tools as needed

