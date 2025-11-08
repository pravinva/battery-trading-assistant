# Manual Guide: Adding Measures, Dimensions, and Filters to Genie Space

## Step-by-Step Instructions

Go to: **Genie > Battery Trading Agent > Configure > Instructions > SQL Expressions**

**Important**: Genie requires table names in SQL expressions. Use the format `table_name.column_name`.

If you get errors, try fully qualified names: `ea_trading.battery_trading.table_name.column_name`

---

## 📊 MEASURES (Click "Add" → Select "Measure")

### Measure 1: Average SoC
- **Name**: `Average SoC`
- **SQL Expression**: `AVG(battery_telemetry.soc_percent)`
- **Synonyms** (optional): `average state of charge, mean SoC, average battery level`
- **Instructions** (optional): `Average state of charge percentage across batteries from telemetry table`

### Measure 2: Total Revenue
- **Name**: `Total Revenue`
- **SQL Expression**: `SUM(battery_dispatch.revenue_dollar)`
- **Synonyms** (optional): `total earnings, cumulative revenue, total income`
- **Instructions** (optional): `Total revenue in dollars from battery dispatch table`

### Measure 3: Total Discharge Energy
- **Name**: `Total Discharge Energy`
- **SQL Expression**: `SUM(CASE WHEN battery_dispatch.dispatch_mw > 0 THEN battery_dispatch.dispatch_mw * 5/60 ELSE 0 END)`
- **Synonyms** (optional): `total discharge, energy exported, total discharge MWh`
- **Instructions** (optional): `Total energy discharged in MWh (positive dispatch values)`

### Measure 4: Total Charge Energy
- **Name**: `Total Charge Energy`
- **SQL Expression**: `SUM(CASE WHEN battery_dispatch.dispatch_mw < 0 THEN ABS(battery_dispatch.dispatch_mw) * 5/60 ELSE 0 END)`
- **Synonyms** (optional): `total charge, energy imported, total charge MWh`
- **Instructions** (optional): `Total energy charged in MWh (negative dispatch values)`

### Measure 5: Average Spot Price
- **Name**: `Average Spot Price`
- **SQL Expression**: `AVG(battery_dispatch.spot_price_dollar_per_mwh)`
- **Synonyms** (optional): `avg price, average price, mean spot price`
- **Instructions** (optional): `Average spot price per MWh from dispatch table`

### Measure 6: Number of Intervals
- **Name**: `Number of Intervals`
- **SQL Expression**: `COUNT(*)`
- **Synonyms** (optional): `count, number of records, interval count`
- **Instructions** (optional): `Number of trading intervals`

---

## 📐 DIMENSIONS (Click "Add" → Select "Dimension")

### Dimension 1: Battery ID
- **Name**: `Battery ID`
- **SQL Expression**: `battery_telemetry.battery_id` (or `battery_dispatch.battery_id` or `battery_assets.battery_id` - use the table you're querying)
- **Values** (one per line):
  ```
  RESS2
  DPNTBESS
  GANNBG1
  GANNBL1
  ```
- **Instructions** (optional): `Battery identifier - RESS2 and DPNTBESS at Darlington Point, GANNBG1 and GANNBL1 at Wooreen`

### Dimension 2: Site Location
- **Name**: `Site Location`
- **SQL Expression**: `battery_assets.site_name`
- **Values** (one per line):
  ```
  Darlington Point (Riverina)
  Wooreen (Jeeralang)
  ```
- **Instructions** (optional): `Physical location of battery sites from assets table`

### Dimension 3: Partner
- **Name**: `Partner`
- **SQL Expression**: `battery_assets.partner`
- **Instructions** (optional): `Battery partner/vendor name from assets table`

---

## 🔍 FILTERS (Click "Add" → Select "Filter")

### Filter 1: Recent Telemetry
- **Name**: `Recent Telemetry (Last 10 minutes)`
- **SQL Expression**: `battery_telemetry.reading_age_minutes <= 10`
- **Instructions**: `Filter for telemetry readings from the last 10 minutes`

### Filter 2: High SoC
- **Name**: `High SoC (>80%)`
- **SQL Expression**: `battery_telemetry.soc_percent > 80`
- **Instructions**: `Batteries with state of charge above 80%`

### Filter 3: Low SoC
- **Name**: `Low SoC (<20%)`
- **SQL Expression**: `battery_telemetry.soc_percent < 20`
- **Instructions**: `Batteries with state of charge below 20%`

### Filter 4: Positive Revenue
- **Name**: `Positive Revenue`
- **SQL Expression**: `battery_dispatch.revenue_dollar > 0`
- **Instructions**: `Filter for profitable trading intervals`

### Filter 5: Last 24 Hours
- **Name**: `Last 24 Hours`
- **SQL Expression**: `battery_dispatch.dispatch_interval >= current_timestamp() - INTERVAL 24 HOURS`
- **Instructions**: `Filter for dispatch data from the last 24 hours`

### Filter 6: Last Hour
- **Name**: `Last Hour`
- **SQL Expression**: `battery_dispatch.dispatch_interval >= current_timestamp() - INTERVAL 1 HOUR`
- **Instructions**: `Filter for dispatch data from the last hour`

---

## 📝 Quick Copy-Paste Reference

### Measures (Copy these SQL expressions - WITH table names):
```
AVG(battery_telemetry.soc_percent)
SUM(battery_dispatch.revenue_dollar)
SUM(CASE WHEN battery_dispatch.dispatch_mw > 0 THEN battery_dispatch.dispatch_mw * 5/60 ELSE 0 END)
SUM(CASE WHEN battery_dispatch.dispatch_mw < 0 THEN ABS(battery_dispatch.dispatch_mw) * 5/60 ELSE 0 END)
AVG(battery_dispatch.spot_price_dollar_per_mwh)
COUNT(*)
```

### Dimensions (Copy these SQL expressions - WITH table names):
```
battery_telemetry.battery_id
battery_assets.site_name
battery_assets.partner
```

### Filters (Copy these SQL expressions - WITH table names):
```
battery_telemetry.reading_age_minutes <= 10
battery_telemetry.soc_percent > 80
battery_telemetry.soc_percent < 20
battery_dispatch.revenue_dollar > 0
battery_dispatch.dispatch_interval >= current_timestamp() - INTERVAL 24 HOURS
battery_dispatch.dispatch_interval >= current_timestamp() - INTERVAL 1 HOUR
```

---

## 💡 Tips

1. **Order matters**: Add measures first, then dimensions, then filters
2. **Test after adding**: Try asking Genie a question to verify it understands
3. **Synonyms help**: Adding synonyms makes Genie recognize more ways to ask for the same thing
4. **Instructions are optional**: But they help Genie understand context better

---

## ✅ After Adding

Once you've added all expressions:
1. Click **"Save"** in the Configure dialog
2. Test Genie with: "What's the average SoC for all batteries?"
3. Verify it uses your measures/dimensions correctly

