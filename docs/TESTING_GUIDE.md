# Testing Guide: Streamlit App vs Genie Direct

## 🎯 Streamlit App (Recommended)

**When to use**: Test the complete agent system

**How it works**:
1. You ask a question in the Streamlit app
2. Agent decides which tool to use:
   - Simple queries → Predefined tools (get_battery_status, etc.)
   - Complex queries → Genie API (query_genie tool)
3. Shows sources at the bottom (Vector Search / SQL Query / Genie)

**Advantages**:
- ✅ Tests full integration
- ✅ Agent intelligently routes queries
- ✅ Shows which tools were used
- ✅ Complete user experience

**Test queries**:
- "What is RESS2 current SoC?" → Should use predefined tool
- "Compare average SoC across all batteries" → Should use Genie
- "Show me batteries with SoC below 50%" → Should use Genie

**URL**: http://localhost:8505

---

## 🔍 Genie Direct (For Debugging)

**When to use**: Verify Genie space configuration works

**How to test**:
1. Go to Databricks → Genie
2. Open "Battery Trading Agent" space
3. Ask questions directly in Genie chat

**Advantages**:
- ✅ Direct Genie testing
- ✅ Verify SQL expressions work
- ✅ Check if instructions are being followed
- ✅ Faster debugging if something's wrong

**Test queries**:
- "What's the average SoC for all batteries?"
- "Show me revenue for RESS2"
- "Which batteries have SoC above 80%?"

---

## 💡 Recommendation

**Start with Streamlit App** because:
1. It's the actual user experience
2. Tests the full agent → Genie integration
3. Shows if agent correctly routes to Genie
4. Verifies sources display correctly

**Then test Genie directly** if:
- Genie queries aren't working in the app
- Want to verify Genie space configuration
- Need to debug SQL expression issues

---

## 🔄 How the Agent Decides

The agent uses this logic:

```
IF question matches predefined tool patterns:
  → Use predefined tool (faster)
ELSE IF question is complex/custom:
  → Use Genie (query_genie tool)
```

**Examples**:
- "What is RESS2 SoC?" → `get_battery_status` (predefined)
- "Compare SoC across batteries" → `query_genie` (Genie)
- "Show revenue" → `get_battery_revenue` (predefined)
- "Which battery has highest revenue?" → `query_genie` (Genie)

---

## ✅ Testing Checklist

### Streamlit App Tests:
- [ ] Simple query works (uses predefined tool)
- [ ] Complex query works (uses Genie)
- [ ] Sources show correctly
- [ ] Genie queries show "Databricks Genie" in sources

### Genie Direct Tests:
- [ ] Genie understands battery domain
- [ ] SQL expressions are used correctly
- [ ] Filters work (e.g., "high SoC" uses soc_percent > 80)
- [ ] Measures work (e.g., "average SoC" uses AVG)

---

## 🎯 Best Practice

**Primary testing**: Use Streamlit App
- This is what users will experience
- Tests the complete system

**Secondary testing**: Use Genie directly
- Only if you need to debug Genie-specific issues
- Or verify Genie space configuration

Both are valuable, but start with the app!

