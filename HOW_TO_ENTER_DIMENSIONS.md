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

   **Values Field**: 
   - ⚠️ **No Values field needed!** Genie will automatically discover values (RESS2, DPNTBESS, GANNBG1, GANNBL1) from your data
   - Just leave it empty or skip if the field doesn't exist

   **Instructions Field** (optional but recommended):
   ```
   Battery identifier - RESS2 and DPNTBESS at Darlington Point, GANNBG1 and GANNBL1 at Wooreen. Valid values: RESS2, DPNTBESS, GANNBG1, GANNBL1
   ```
   *Adding the values in Instructions helps Genie understand what values to expect*

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
│ Instructions (optional):                 │
│ [Battery identifier - RESS2 and DPNTBESS │
│  at Darlington Point, GANNBG1 and       │
│  GANNBL1 at Wooreen. Valid values:       │
│  RESS2, DPNTBESS, GANNBG1, GANNBL1]     │
│                                          │
│ [Cancel]  [Save/Add]                     │
└─────────────────────────────────────────┘
```

**Note**: There's no "Values" field - Genie auto-discovers values from your data!

---

## Tips:

1. **No Values Field Needed**: 
   - Genie automatically discovers values from your data
   - Just enter Name and SQL Expression
   - Genie will find RESS2, DPNTBESS, GANNBG1, GANNBL1 from the tables

2. **SQL Expression**:
   - Must include table name: `battery_telemetry.battery_id`
   - Not just `battery_id` (will cause error)

3. **Instructions Help**:
   - Even though there's no Values field, adding values in Instructions helps Genie understand context
   - Example: "Valid values: RESS2, DPNTBESS, GANNBG1, GANNBL1"

4. **Testing**:
   - After saving, try asking Genie: "Show me data for RESS2"
   - Genie should recognize RESS2 as a Battery ID value automatically

---

## What to Enter (Simplified):

**Just these two fields:**

1. **Name**: `Battery ID`
2. **SQL Expression**: `battery_telemetry.battery_id`
3. **Instructions** (optional): `Battery identifier. Valid values: RESS2, DPNTBESS, GANNBG1, GANNBL1`

That's it! Genie will discover the values automatically.

---

## Common Issues:

**Issue**: "Table name required" error
- **Fix**: Make sure SQL Expression includes table name: `battery_telemetry.battery_id`

**Issue**: Values not recognized
- **Fix**: Genie auto-discovers values, but you can help by mentioning them in Instructions field
- **Fix**: Make sure your tables have data - Genie reads values from actual data

**Issue**: No "Values" field
- **Fix**: This is normal! Genie auto-discovers values from your data. Just enter Name and SQL Expression.

