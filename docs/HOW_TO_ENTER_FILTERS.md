# How to Enter Filters in Genie UI - Step by Step

## Understanding Filters

**What are Filters?**
Filters are SQL expressions that evaluate to a **boolean condition** (TRUE/FALSE), typically used in WHERE clauses. They filter rows based on conditions.

**Format**: `table_name.column_name operator value`
- Returns TRUE for rows that match the condition
- Returns FALSE for rows that don't match

---

## Entering Filter 1: Recent Telemetry (Example)

### Step-by-Step Process:

1. **Navigate to SQL Expressions**
   - Go to: **Genie > Battery Trading Agent > Configure**
   - Click on **"Instructions"** tab
   - Click on **"SQL Expressions"** section

2. **Add New Filter**
   - Click the **"Add"** button
   - Select **"Filter"** from the dropdown/options

3. **Fill in the Form Fields**

   **Name Field:**
   ```
   Recent Telemetry (Last 10 minutes)
   ```

   **SQL Expression Field:**
   ```
   battery_telemetry.reading_age_minutes <= 10
   ```
   *This is a boolean condition - returns TRUE when reading_age_minutes is 10 or less*

   **Instructions Field** (optional but helpful):
   ```
   Filter for telemetry readings from the last 10 minutes. Returns TRUE for rows where reading_age_minutes <= 10
   ```

4. **Save**
   - Click **"Save"** or **"Add"** button to save the filter

---

## Visual Guide - What You'll See:

```
┌─────────────────────────────────────────┐
│ Add Filter                               │
├─────────────────────────────────────────┤
│ Name:                                    │
│ [Recent Telemetry (Last 10 minutes)]    │
│                                          │
│ SQL Expression:                          │
│ [battery_telemetry.reading_age_minutes   │
│  <= 10                          ]        │
│                                          │
│ Instructions (optional):                 │
│ [Filter for telemetry readings from...]  │
│                                          │
│ [Cancel]  [Save/Add]                     │
└─────────────────────────────────────────┘
```

---

## Filter Examples - What to Enter:

### Filter 1: Recent Telemetry
- **Name**: `Recent Telemetry (Last 10 minutes)`
- **SQL Expression**: `battery_telemetry.reading_age_minutes <= 10`

### Filter 2: High SoC
- **Name**: `High SoC (>80%)`
- **SQL Expression**: `battery_telemetry.soc_percent > 80`

### Filter 3: Low SoC
- **Name**: `Low SoC (<20%)`
- **SQL Expression**: `battery_telemetry.soc_percent < 20`

### Filter 4: Positive Revenue
- **Name**: `Positive Revenue`
- **SQL Expression**: `battery_dispatch.revenue_dollar > 0`

### Filter 5: Last 24 Hours
- **Name**: `Last 24 Hours`
- **SQL Expression**: `battery_dispatch.dispatch_interval >= current_timestamp() - INTERVAL 24 HOURS`

### Filter 6: Last Hour
- **Name**: `Last Hour`
- **SQL Expression**: `battery_dispatch.dispatch_interval >= current_timestamp() - INTERVAL 1 HOUR`

---

## Key Points:

1. **Boolean Expressions**: Filters must evaluate to TRUE/FALSE
   - ✅ Correct: `battery_telemetry.soc_percent > 80` (returns TRUE/FALSE)
   - ❌ Wrong: `AVG(battery_telemetry.soc_percent)` (returns a number, not boolean)

2. **Table Names Required**: Always include table name
   - ✅ Correct: `battery_telemetry.soc_percent > 80`
   - ❌ Wrong: `soc_percent > 80` (will cause error)

3. **Common Operators**:
   - `>` (greater than)
   - `<` (less than)
   - `>=` (greater than or equal)
   - `<=` (less than or equal)
   - `=` (equals)
   - `!=` or `<>` (not equals)
   - `IN (...)` (value in list)
   - `LIKE 'pattern'` (pattern matching)

4. **How Genie Uses Filters**:
   - When you ask "Show me batteries with high SoC"
   - Genie will use: `WHERE battery_telemetry.soc_percent > 80`
   - Only rows where the condition is TRUE will be returned

---

## Quick Copy-Paste Reference:

```
battery_telemetry.reading_age_minutes <= 10
battery_telemetry.soc_percent > 80
battery_telemetry.soc_percent < 20
battery_dispatch.revenue_dollar > 0
battery_dispatch.dispatch_interval >= current_timestamp() - INTERVAL 24 HOURS
battery_dispatch.dispatch_interval >= current_timestamp() - INTERVAL 1 HOUR
```

---

## Common Issues:

**Issue**: "Table name required" error
- **Fix**: Make sure SQL Expression includes table name: `battery_telemetry.soc_percent > 80`

**Issue**: "Not a boolean expression" error
- **Fix**: Filters must return TRUE/FALSE. Use comparison operators (`>`, `<`, `=`, etc.)
- **Wrong**: `AVG(soc_percent)` (returns number)
- **Correct**: `soc_percent > 80` (returns TRUE/FALSE)

**Issue**: Filter not working
- **Fix**: Make sure the condition makes sense for the table
- **Fix**: Check that column exists in the specified table

