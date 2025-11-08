# Create Genie Space: battery-trading-agent

Since Genie spaces cannot be created programmatically, please create it manually:

## Steps to Create Genie Space

1. **Go to Databricks Workspace**
   - Log into your Databricks workspace

2. **Open Genie**
   - Click on **"Genie"** in the left sidebar

3. **Create New Space**
   - Click the **"New"** button (upper-right corner)

4. **Configure Space**
   - **Name**: `battery-trading-agent`
   - **Catalog**: `ea_trading`
   - **Schema**: `battery_trading`
   - **Tables to include**:
     - `ea_trading.battery_trading.battery_telemetry`
     - `ea_trading.battery_trading.battery_dispatch`
     - `ea_trading.battery_trading.battery_assets`
     - `ea_trading.battery_trading.battery_documents`

5. **Select SQL Warehouse**
   - Choose a SQL warehouse (Pro or Serverless)
   - Ensure you have "CAN USE" permission

6. **Create**
   - Click **"Create"** to finalize

## After Creation

Once created, run this script to get the space ID:

```bash
python3 scripts/create_genie_room.py
```

It will find the space and display the `space_id`. Then set it as an environment variable:

```bash
export GENIE_ROOM_ID="<space_id_from_script>"
```

Or add it to your `.env` file or `~/.databrickscfg`.

## Verify

The script will automatically detect if the space exists and display its ID.

