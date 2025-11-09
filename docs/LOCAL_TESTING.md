# Local Testing Guide for Genie MCP Integration

## Quick Test Script

Run the comprehensive test script:

```bash
cd /Users/pravin.varma/Documents/Demo/battery-trading-assistant
source venv/bin/activate
python scripts/test_mcp_local.py
```

This tests:
- MCP client initialization
- JSON module imports
- Direct function calls
- LangChain tool wrapper
- Error handling
- Genie logs

## Test via Streamlit App

1. **Start Streamlit**:
```bash
cd /Users/pravin.varma/Documents/Demo/battery-trading-assistant
source venv/bin/activate
export USE_GENIE_MCP=true
export GENIE_ROOM_ID="01f0bca10415147a91fe3c98f80e596e"
streamlit run app/app.py --server.port 8506
```

2. **Open browser**: http://localhost:8506

3. **Enable MCP toggle** in the sidebar (if not already enabled)

4. **Test queries**:
   - "What is the current SoC for RESS2?"
   - "Show me revenue for all batteries in the last 12 hours"
   - "Compare average SoC across all batteries"

5. **Check execution logs**: Expand "💾 SQL Query Results" → "📋 Execution Logs" to see MCP vs Direct API usage

## Test Individual Components

### Test MCP Tool Discovery
```bash
python scripts/discover_genie_mcp_tools.py
```

### Test Direct Function Call
```python
import os
os.environ["USE_GENIE_MCP"] = "true"
os.environ["GENIE_ROOM_ID"] = "01f0bca10415147a91fe3c98f80e596e"

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import importlib.util
spec = importlib.util.spec_from_file_location("agent", "scripts/02_agent_development_local.py")
agent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent)

# Test query
result = agent.query_genie_via_mcp("What is the current SoC for RESS2?", False)
print(result)
```

### Test LangChain Tool
```python
# Same setup as above, then:
tool = agent.query_genie
result = tool.invoke({"question": "Show me revenue for all batteries"})
print(result)
```

## Debug Mode

Enable detailed debug logging:
```bash
export DEBUG=true
python scripts/test_mcp_local.py
```

Or in Streamlit:
```bash
export DEBUG=true
streamlit run app/app.py --server.port 8506
```

## Check Logs

View execution logs:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import importlib.util
spec = importlib.util.spec_from_file_location("agent", "scripts/02_agent_development_local.py")
agent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent)

logs = agent.get_genie_logs()
for log in logs:
    print(log)
```

## Troubleshooting

1. **MCP client not initialized**: Check `USE_GENIE_MCP=true` and `GENIE_ROOM_ID` is set
2. **Broken pipe errors**: Network issue - retry after a few seconds
3. **JSON scoping errors**: Restart Streamlit to reload module
4. **Module not found**: Ensure `databricks-mcp` is installed: `pip install databricks-mcp`

