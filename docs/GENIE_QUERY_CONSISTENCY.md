# Genie Query Consistency Guide

## Issue: Different SQL for Same Question

Genie may generate different SQL queries depending on context. This document explains why and how to ensure consistency.

## Example: "Which battery has the highest discharge capability?"

### Query 1: From Genie UI (Theoretical)
```sql
SELECT battery_id, site_name, nameplate_capacity_mw AS max_discharge_capability_mw
FROM ea_trading.battery_trading.battery_assets
WHERE nameplate_capacity_mw IS NOT NULL
ORDER BY nameplate_capacity_mw DESC
LIMIT 1
```
**Uses:** `battery_assets.nameplate_capacity_mw` (theoretical maximum)

### Query 2: From Streamlit UI (Current Operational)
```sql
SELECT battery_id, capability_discharge_mw
FROM ea_trading.battery_trading.battery_telemetry
WHERE capability_discharge_mw IS NOT NULL
ORDER BY capability_discharge_mw DESC
LIMIT 1
```
**Uses:** `battery_telemetry.capability_discharge_mw` (current operational)

## Why This Happens

Both interpretations are valid:
- **Theoretical**: Design specification, doesn't change
- **Current Operational**: Real-time value, can vary with SoC/temperature

Genie may choose differently based on:
- Question phrasing ("current" vs "maximum")
- Context from previous messages
- Examples in Genie space
- SQL expressions defined

## Solution: Add Clear Instructions

### 1. Update Genie Instructions

Add this to your Genie space instructions:

```
**Discharge Capability Clarification**

When asked about "discharge capability" or "discharge capacity":
- **Theoretical/Maximum**: Use `battery_assets.nameplate_capacity_mw` - design specification
- **Current/Operational**: Use `battery_telemetry.capability_discharge_mw` - real-time operational value

**Default**: If question doesn't specify "current" or "operational", use `nameplate_capacity_mw` (theoretical maximum).
```

### 2. Add SQL Expressions

Add these measures to Genie space:

**Measure: Maximum Discharge Capability**
- SQL: `MAX(battery_assets.nameplate_capacity_mw)`
- Synonyms: `max discharge capacity, theoretical discharge capability, nameplate capacity`
- Instructions: `Theoretical maximum from design specs. Use for "highest discharge capability" without "current" qualifier.`

**Measure: Current Discharge Capability**
- SQL: `MAX(battery_telemetry.capability_discharge_mw)`
- Synonyms: `current discharge capacity, operational discharge capability`
- Instructions: `Current operational capability. Use only when question specifies "current" or "operational".`

### 3. Add Example Queries

Add these to Genie space SQL examples:

**Example 1: Theoretical Maximum**
- Question: "Which battery has the highest discharge capability?"
- SQL: Uses `battery_assets.nameplate_capacity_mw`

**Example 2: Current Operational**
- Question: "Which battery has the highest current discharge capability?"
- SQL: Uses `battery_telemetry.capability_discharge_mw`

## Best Practices

1. **Be specific in questions**: Use "current" or "theoretical" when possible
2. **Add examples**: Include both interpretations in Genie SQL examples
3. **Define measures**: Add SQL expressions for both concepts
4. **Document defaults**: Specify which interpretation to use by default

## Testing

Test both interpretations:

1. **Theoretical**: "Which battery has the highest discharge capability?"
   - Expected: Uses `battery_assets.nameplate_capacity_mw`
   - Result: Should return GANNBG1/GANNBL1 (150 MW)

2. **Current**: "Which battery has the highest current discharge capability?"
   - Expected: Uses `battery_telemetry.capability_discharge_mw`
   - Result: May vary based on current SoC/conditions

## Related Fields

| Field | Table | Type | Description |
|-------|-------|------|-------------|
| `nameplate_capacity_mw` | `battery_assets` | Theoretical | Design specification, constant |
| `capability_discharge_mw` | `battery_telemetry` | Current | Real-time operational capability |
| `capability_charge_mw` | `battery_telemetry` | Current | Real-time operational charge capability |

Both are valid - choose based on question context!

