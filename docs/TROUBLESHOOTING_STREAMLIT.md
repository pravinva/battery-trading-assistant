# Troubleshooting Streamlit MCP Issues

## If Vector Search Works But Genie MCP Doesn't

### Step 1: Check MCP Toggle
1. Open Streamlit app (http://localhost:8506)
2. Check sidebar → "🔌 Configuration"
3. Ensure "Use Genie MCP Server" toggle is **ON** (green)
4. If it was off, toggle it ON and wait for page reload

### Step 2: Clear Streamlit Cache
1. In Streamlit UI, click the menu (☰) in top right
2. Click "Clear cache"
3. Refresh the page

### Step 3: Check Error Details
When you get an error:
1. Look for the error message
2. Click "🔍 Error Details (Click to expand)" to see full traceback
3. Check the error type:
   - **Network/Broken Pipe**: Temporary network issue - retry
   - **JSON scoping**: Module reload issue - restart Streamlit
   - **MCP Client**: Check MCP setup

### Step 4: Restart Streamlit
```bash
# Kill existing Streamlit processes
pkill -f "streamlit run app/app.py"

# Restart with MCP enabled
cd /Users/pravin.varma/Documents/Demo/battery-trading-assistant
source venv/bin/activate
export USE_GENIE_MCP=true
export GENIE_ROOM_ID="01f0bca10415147a91fe3c98f80e596e"
streamlit run app/app.py --server.port 8506
```

### Step 5: Run Diagnostic
```bash
python scripts/diagnose_streamlit_mcp.py
```

This will test MCP initialization in a Streamlit-like context.

### Step 6: Check Logs
In Streamlit UI, after running a query:
1. Expand "💾 SQL Query Results"
2. Expand "📋 Execution Logs (MCP vs Direct API)"
3. Check if logs show MCP or Direct API usage

### Common Issues

**Issue: "MCP client not initialized"**
- Solution: Ensure `databricks-mcp` is installed: `pip install databricks-mcp`
- Check MCP toggle is ON in sidebar

**Issue: "Broken pipe" errors**
- Solution: Network issue - wait a few seconds and retry
- Check internet connection
- Verify Databricks workspace is accessible

**Issue: Vector search works but Genie doesn't**
- Solution: This suggests MCP client initialization failed
- Check error details expander
- Run diagnostic script
- Restart Streamlit with MCP enabled

**Issue: No logs showing**
- Solution: Logs are cleared after reading
- Run a new query to see fresh logs
- Check if query_genie tool was actually called

### Verify MCP is Working

Run this test query in Streamlit:
```
What is the current SoC for RESS2?
```

Then check:
1. Error message (if any)
2. Execution logs expander - should show MCP tool calls
3. Response should include "via MCP" in the header

