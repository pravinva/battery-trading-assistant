# Demo Guide: Hybrid Queries (SQL + Documentation)

## 🎯 Demo Scenario: Agent Using Both SQL and Vector Search

This demonstrates the agent's ability to combine:
- **SQL queries** (live data from Delta tables)
- **Vector Search** (technical documentation)

---

## 🎬 Demo Queries (Copy these exactly)

### Demo 1: SoC Status + Operational Limits
**Query:**
```
What is RESS2 current SoC and what are the SoC limits for availability?
```

**Expected Behavior:**
- ✅ Uses `get_battery_status` → Gets current SoC from `battery_telemetry` table
- ✅ Uses `search_battery_docs` → Searches documentation for SoC limits
- ✅ Combines both sources in answer
- ✅ Shows sources: "SQL Query, Vector Search"

---

### Demo 2: Revenue + Throughput Explanation
**Query:**
```
Show me revenue for RESS2 in the last 24 hours and explain how throughput is calculated
```

**Expected Behavior:**
- ✅ Uses `get_battery_revenue` → Gets revenue from `battery_dispatch` table
- ✅ Uses `search_battery_docs` → Searches documentation for throughput calculation
- ✅ Combines financial data with technical explanation
- ✅ Shows sources: "SQL Query, Vector Search"

---

### Demo 3: Battery Info + Technical Specs
**Query:**
```
Get battery asset information for DPNTBESS and explain the PI integration process
```

**Expected Behavior:**
- ✅ Uses `get_battery_info` → Gets asset specs from `battery_assets` table
- ✅ Uses `search_battery_docs` → Searches documentation for PI integration
- ✅ Combines asset data with technical process
- ✅ Shows sources: "SQL Query, Vector Search"

---

### Demo 4: Current Status + Operational Guidelines
**Query:**
```
What's the current SoC for all batteries and what are the operational limits I should be aware of?
```

**Expected Behavior:**
- ✅ Uses `get_battery_status` → Gets SoC for all batteries
- ✅ Uses `search_battery_docs` → Searches for operational limits and guidelines
- ✅ Provides comprehensive operational view
- ✅ Shows sources: "SQL Query, Vector Search"

---

### Demo 5: Performance Analysis + Technical Context
**Query:**
```
Compare revenue performance for RESS2 and DPNTBESS, and explain how AEMO bidding works
```

**Expected Behavior:**
- ✅ Uses `get_battery_revenue` (twice) → Gets revenue for both batteries
- ✅ Uses `search_battery_docs` → Searches documentation for AEMO bidding process
- ✅ Combines performance comparison with technical context
- ✅ Shows sources: "SQL Query, Vector Search"

---

## 📊 What You'll See in the App

After asking a hybrid query, check the **Sources** section at the bottom:

```
📊 Sources: SQL Query, Vector Search

🔍 Vector Search Results ▼
  Query 1: [your search query]
  Result: [relevant documentation chunks]

💾 SQL Query Results ▼
  Tool: get_battery_status (or get_battery_revenue, etc.)
  Arguments: {...}
  Result: [SQL query results]
```

---

## 🎯 Best Demo Query (Recommended)

**Use this one for the best demo:**

```
What is RESS2 current SoC and what are the SoC limits for availability?
```

**Why it's perfect:**
- ✅ Clear SQL component (current SoC)
- ✅ Clear documentation component (SoC limits)
- ✅ Practical real-world question
- ✅ Shows agent combining both sources intelligently

---

## 💡 Demo Flow

1. **Open Streamlit App**: http://localhost:8505

2. **Ask the demo query** (copy-paste one from above)

3. **Watch the agent work**:
   - See "Thinking..." spinner
   - Agent decides to use multiple tools
   - Combines results from both sources

4. **Check Sources**:
   - Expand "Vector Search Results" → See documentation chunks
   - Expand "SQL Query Results" → See SQL tool used and results
   - Both should be present!

5. **Review Answer**:
   - Answer should cite both sources
   - Example: "According to telemetry, RESS2 SoC is X%. From the technical documentation, the SoC limits are..."

---

## 🔍 How to Verify It's Working

**Good signs:**
- ✅ Sources show "SQL Query, Vector Search" (both present)
- ✅ Answer references both data and documentation
- ✅ Vector Search expander shows documentation chunks
- ✅ SQL Query expander shows tool name and results

**If only one source appears:**
- Check if query is too simple (might only need one source)
- Try a more explicit hybrid query
- Check that Vector Search index is synced

---

## 📝 Demo Script

**Opening:**
"Let me show you how the agent combines live data with technical documentation..."

**Query:**
"What is RESS2 current SoC and what are the SoC limits for availability?"

**Explanation:**
"The agent is now:
1. Querying the telemetry table for current SoC
2. Searching the documentation for SoC limits
3. Combining both sources to give you a complete answer"

**Show Sources:**
"Notice here in the sources - we can see both SQL Query and Vector Search were used. Let me expand these to show you what was retrieved..."

---

## ✅ Testing Checklist

Before your demo:
- [ ] Streamlit app is running
- [ ] Vector Search index is synced
- [ ] Delta tables have data
- [ ] Genie space is configured
- [ ] Test query works and shows both sources

Ready to demo! 🎬

