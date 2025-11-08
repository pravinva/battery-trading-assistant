# Genie SQL Query Fixes for NULL Results

## Issue: NULL Results from Genie SQL Queries

When Genie generates SQL queries for throughput calculations, it may return NULL because:

1. **Cumulative Fields Misuse**: Using `MAX(cum_energy_exported_mwh) - MIN(cum_energy_exported_mwh)` doesn't work correctly because:
   - Cumulative values may not change significantly in the time window
   - If all values are the same, MAX - MIN = 0 or NULL
   - Cumulative fields represent lifetime totals, not interval changes

2. **Better Approach**: Use the `throughput_mwh` field directly or calculate from `battery_dispatch` table

## Recommended SQL for Energy Throughput

### Option 1: Use throughput_mwh field (Recommended)
```sql
SELECT 
    SUM(throughput_mwh) AS total_throughput_mwh
FROM ea_trading.battery_trading.battery_telemetry
WHERE timestamp >= current_timestamp() - INTERVAL 12 HOURS
```

### Option 2: Calculate from dispatch table
```sql
SELECT 
    ROUND(SUM(ABS(dispatch_mw) * 5.0 / 60.0), 2) AS total_throughput_mwh
FROM ea_trading.battery_trading.battery_dispatch
WHERE dispatch_interval >= current_timestamp() - INTERVAL 12 HOURS
```

### Option 3: Calculate change in cumulative values (if needed)
```sql
SELECT 
    ROUND(SUM(exported + imported), 2) AS total_throughput_mwh
FROM (
    SELECT 
        battery_id,
        (MAX(cum_energy_exported_mwh) - MIN(cum_energy_exported_mwh)) AS exported,
        (MAX(cum_energy_imported_mwh) - MIN(cum_energy_imported_mwh)) AS imported
    FROM ea_trading.battery_trading.battery_telemetry
    WHERE timestamp >= current_timestamp() - INTERVAL 12 HOURS
    GROUP BY battery_id
    HAVING MAX(cum_energy_exported_mwh) != MIN(cum_energy_exported_mwh)
        OR MAX(cum_energy_imported_mwh) != MIN(cum_energy_imported_mwh)
)
```

## Why Genie's SQL Returns NULL

The generated SQL:
```sql
SELECT ROUND(SUM(exported + imported), 2) AS total_throughput_mwh
FROM (
    SELECT
        battery_id,
        MAX(cum_energy_exported_mwh) - MIN(cum_energy_exported_mwh) AS exported,
        MAX(cum_energy_imported_mwh) - MIN(cum_energy_imported_mwh) AS imported
    FROM ea_trading.battery_trading.battery_telemetry
    WHERE timestamp >= current_timestamp() - INTERVAL 12 HOURS
    GROUP BY battery_id
)
```

**Problems:**
1. If cumulative values don't change in the window, MAX - MIN = 0
2. If there's only one reading per battery, MAX - MIN = 0
3. SUM of NULLs or zeros returns NULL
4. Cumulative fields are meant for lifetime tracking, not interval calculations

## Solution: Update Genie Instructions

Add to Genie space instructions:

```
For energy throughput calculations:
- Use the throughput_mwh field directly from battery_telemetry table
- OR calculate from battery_dispatch table using ABS(dispatch_mw) * interval_duration
- Do NOT use MAX - MIN of cumulative energy fields (cum_energy_exported_mwh, cum_energy_imported_mwh)
- These cumulative fields represent lifetime totals, not interval changes
```

