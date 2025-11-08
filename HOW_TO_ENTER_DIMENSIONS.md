# How to Enter Dimensions in Genie UI - Step by Step

## Entering Dimension 1: Battery ID

### Step-by-Step Process:

1. **Navigate to SQL Expressions**
   - Go to: **Genie > Battery Trading Agent > Configure**
   - Click on **"Instructions"** tab
   - Click on **"SQL Expressions"** section

2. **Add New Dimension**
   - Click the **"Add"** button
   - Select **"Dimension"** from the dropdown/options

3. **Fill in the Form Fields**

   **Name Field:**
   ```
   Battery ID
   ```

   **SQL Expression Field:**
   ```
   battery_telemetry.battery_id
   ```
   *(Note: You can also use `battery_dispatch.battery_id` or `battery_assets.battery_id` depending on which table you're primarily querying)*

   **Values Field** (enter one per line):
   ```
   RESS2
   DPNTBESS
   GANNBG1
   GANNBL1
   ```
   *Important: Enter each value on a separate line, or use commas if the UI accepts comma-separated values*

   **Instructions Field** (optional):
   ```
   Battery identifier - RESS2 and DPNTBESS at Darlington Point, GANNBG1 and GANNBL1 at Wooreen
   ```

4. **Save**
   - Click **"Save"** or **"Add"** button to save the dimension

---

## Visual Guide - What You'll See:

```
┌─────────────────────────────────────────┐
│ Add Dimension                            │
├─────────────────────────────────────────┤
│ Name:                                    │
│ [Battery ID                    ]         │
│                                          │
│ SQL Expression:                          │
│ [battery_telemetry.battery_id ]         │
│                                          │
│ Values (one per line):                   │
│ ┌─────────────────────────────────────┐ │
│ │ RESS2                                │ │
│ │ DPNTBESS                             │ │
│ │ GANNBG1                              │ │
│ │ GANNBL1                              │ │
│ └─────────────────────────────────────┘ │
│                                          │
│ Instructions (optional):                 │
│ [Battery identifier - RESS2 and...]      │
│                                          │
│ [Cancel]  [Save/Add]                     │
└─────────────────────────────────────────┘
```

---

## Tips:

1. **Values Format**: 
   - Some UIs accept one value per line (press Enter after each)
   - Some accept comma-separated: `RESS2, DPNTBESS, GANNBG1, GANNBL1`
   - Check the UI format - it usually shows placeholder text

2. **SQL Expression**:
   - Must include table name: `battery_telemetry.battery_id`
   - Not just `battery_id` (will cause error)

3. **If Values Field Doesn't Exist**:
   - Some Genie versions might not have a "Values" field
   - In that case, just enter Name and SQL Expression
   - Genie will discover values automatically from the data

4. **Testing**:
   - After saving, try asking Genie: "Show me data for RESS2"
   - It should recognize RESS2 as a Battery ID value

---

## Quick Copy-Paste Values:

**For Values field** (copy exactly as shown, one per line):
```
RESS2
DPNTBESS
GANNBG1
GANNBG1
```

**Or if comma-separated format:**
```
RESS2, DPNTBESS, GANNBG1, GANNBL1
```

---

## Common Issues:

**Issue**: "Table name required" error
- **Fix**: Make sure SQL Expression includes table name: `battery_telemetry.battery_id`

**Issue**: Values not recognized
- **Fix**: Check spelling - must match exactly: `RESS2` (all caps), not `ress2` or `Ress2`

**Issue**: Can't find "Values" field
- **Fix**: Some Genie versions auto-discover values - just enter Name and SQL Expression

