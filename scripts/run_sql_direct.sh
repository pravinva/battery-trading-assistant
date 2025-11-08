#!/bin/bash
# Direct SQL execution using Databricks SQL API
# Requires: DATABRICKS_WAREHOUSE_ID environment variable or pass as argument

SQL_FILE=${1:-scripts/02_generate_telemetry_data.sql}
WAREHOUSE_ID=${2:-${DATABRICKS_WAREHOUSE_ID}}

if [ -z "$WAREHOUSE_ID" ]; then
    echo "❌ Error: SQL Warehouse ID required"
    echo ""
    echo "Usage: $0 [sql_file] [warehouse_id]"
    echo "   Or set: export DATABRICKS_WAREHOUSE_ID=<your_warehouse_id>"
    echo ""
    echo "To find your warehouse ID:"
    echo "  databricks sql warehouses list"
    exit 1
fi

if [ ! -f "$SQL_FILE" ]; then
    echo "❌ File not found: $SQL_FILE"
    exit 1
fi

echo "📄 Running: $SQL_FILE"
echo "🏭 Warehouse ID: $WAREHOUSE_ID"
echo ""

# Try using databricks sql execute if available
if command -v databricks &> /dev/null; then
    echo "Attempting to run via Databricks CLI..."
    databricks sql execute --warehouse-id "$WAREHOUSE_ID" --file "$SQL_FILE" 2>&1
else
    echo "❌ Databricks CLI not found"
    echo "💡 Copy the SQL content to Databricks SQL Editor instead"
    cat "$SQL_FILE"
fi
