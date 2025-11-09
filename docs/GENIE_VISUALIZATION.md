# Genie Visualization Integration

## Current Situation

When users ask Genie for visualizations (e.g., "plot revenue by battery"), Genie UI automatically:
1. Generates appropriate SQL queries
2. Executes the queries
3. **Automatically creates and displays charts** based on the data

However, our agent is currently:
1. Detecting visualization requests
2. Creating its own charts from raw query data
3. Not leveraging Genie's built-in visualization capabilities

## The Problem

Genie's UI shows charts, but the Genie Conversation API response structure doesn't explicitly expose visualization metadata in a way we can directly use. The API returns:
- `text`: Natural language response
- `query`: SQL query object with `statement_id`
- `attachments`: Array of attachment objects

## What We're Checking

We've added debug logging to check if Genie returns visualization metadata in attachments:

```python
# Check for visualization/chart metadata
if hasattr(attachment, 'visualization') or hasattr(attachment, 'chart') or hasattr(attachment, 'viz'):
    vis_metadata = getattr(attachment, 'visualization', None) or getattr(attachment, 'chart', None) or getattr(attachment, 'viz', None)
    print(f"Found visualization metadata: {vis_metadata}")
```

## Current Approach

Since Genie's API doesn't expose visualization specs directly, we:
1. **Detect visualization requests** using keywords (plot, chart, graph, visualize, etc.)
2. **Extract query results** from Genie's SQL execution
3. **Create our own Plotly charts** based on:
   - Question context (comparison → bar chart, time series → line chart)
   - Data structure (categorical + numeric → bar chart)
   - Column names (battery_id → x-axis, revenue → y-axis)

## Potential Improvements

### Option 1: Use Genie's Query Description
Genie's `query.description` field might contain hints about visualization:
- "You're looking for revenue comparison across batteries"
- This could inform our chart type selection

### Option 2: Infer from SQL Query
Analyze Genie's generated SQL to determine chart type:
- `GROUP BY battery_id` → Bar chart
- `ORDER BY timestamp` → Line chart
- `COUNT(*)` → Bar or pie chart

### Option 3: Check Genie UI API
Genie UI might have a separate API endpoint for visualization data that we're not using.

### Option 4: Improve Our Chart Logic
Enhance our chart creation to better match Genie's decisions:
- Use Genie's query description as guidance
- Analyze SQL structure more intelligently
- Better column name detection and mapping

## Next Steps

1. **Check debug logs** (`/tmp/genie_debug.log`) for visualization-related keys in attachments
2. **Test with visualization requests** and inspect attachment structure
3. **Compare Genie UI charts** with our generated charts to identify differences
4. **Consider using Genie's query description** to inform chart type selection

## Debugging

To see what Genie returns for visualization requests:

```bash
# Ask a visualization question in Streamlit
# Then check the debug log:
tail -200 /tmp/genie_debug.log | grep -A 10 -i "visualization\|chart\|viz"
```

Look for:
- `⚠️ Found visualization metadata`
- `⚠️ Found visualization-related keys`
- Any keys containing: `viz`, `chart`, `graph`, `visualization`, `plot`

