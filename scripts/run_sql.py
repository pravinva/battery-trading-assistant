#!/usr/bin/env python3
"""
Run SQL script via Databricks SQL API
Usage: python run_sql.py scripts/02_generate_telemetry_data.sql
"""

import sys
import os
import json
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState

def run_sql_file(filepath):
    """Run a SQL file using Databricks SQL API"""
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return False
    
    # Read SQL file
    with open(filepath, 'r') as f:
        sql_content = f.read()
    
    # Remove comments and empty lines for cleaner execution
    lines = []
    for line in sql_content.split('\n'):
        line = line.strip()
        # Skip empty lines and comment-only lines
        if line and not line.startswith('--'):
            lines.append(line)
    
    # Join SQL statements (split by semicolon)
    sql_statements = []
    current_statement = []
    
    for line in lines:
        if line.endswith(';'):
            current_statement.append(line[:-1])  # Remove semicolon
            sql_statements.append(' '.join(current_statement))
            current_statement = []
        else:
            current_statement.append(line)
    
    if current_statement:
        sql_statements.append(' '.join(current_statement))
    
    print(f"📄 Running SQL file: {filepath}")
    print(f"📊 Found {len(sql_statements)} SQL statements")
    
    # Initialize Databricks client
    try:
        w = WorkspaceClient()
        
        # Get SQL warehouse endpoint (you may need to specify your warehouse ID)
        print("\n⚠️  Note: This requires a SQL warehouse endpoint.")
        print("   Alternative: Use Databricks SQL Editor or run via REST API")
        print("\nSQL statements to run:")
        print("=" * 80)
        for i, stmt in enumerate(sql_statements, 1):
            print(f"\n-- Statement {i}")
            print(stmt[:200] + "..." if len(stmt) > 200 else stmt)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Alternative: Copy the SQL to Databricks SQL Editor")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_sql.py <sql_file>")
        print("Example: python run_sql.py scripts/02_generate_telemetry_data.sql")
        sys.exit(1)
    
    filepath = sys.argv[1]
    run_sql_file(filepath)

