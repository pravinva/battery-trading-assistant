#!/bin/bash
# Run SQL script via Databricks CLI
# Usage: ./run_sql_cli.sh scripts/02_generate_telemetry_data.sql

SQL_FILE=$1

if [ -z "$SQL_FILE" ]; then
    echo "Usage: $0 <sql_file>"
    echo "Example: $0 scripts/02_generate_telemetry_data.sql"
    exit 1
fi

if [ ! -f "$SQL_FILE" ]; then
    echo "❌ File not found: $SQL_FILE"
    exit 1
fi

echo "📄 SQL File: $SQL_FILE"
echo ""
echo "Option 1: Copy SQL to Databricks SQL Editor"
echo "Option 2: Use Databricks SQL API (requires warehouse endpoint)"
echo ""
echo "SQL Content:"
echo "=========================================="
cat "$SQL_FILE"
echo ""
echo "=========================================="
echo ""
echo "To run via SQL Editor:"
echo "1. Open Databricks SQL Editor"
echo "2. Copy and paste the SQL above"
echo "3. Run"
echo ""
echo "To run via CLI (if SQL API is configured):"
echo "  databricks sql execute --warehouse-id <warehouse_id> --file $SQL_FILE"

