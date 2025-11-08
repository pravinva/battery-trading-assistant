#!/usr/bin/env python3
"""
Run SQL script via Databricks SQL API
Usage: python3 run_sql_command.py scripts/02_generate_telemetry_data.sql [warehouse_id]
"""

import sys
import os
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState

def run_sql_file(filepath, warehouse_id=None):
    """Run a SQL file using Databricks SQL API"""
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return False
    
    # Read SQL file
    with open(filepath, 'r') as f:
        sql_content = f.read()
    
    # Initialize Databricks client
    try:
        w = WorkspaceClient()
        
        # Get warehouse ID
        if not warehouse_id:
            print("🔍 Finding available SQL warehouses...")
            warehouses = list(w.warehouses.list())
            if not warehouses:
                print("❌ No SQL warehouses found")
                print("💡 Please create a SQL warehouse or provide warehouse ID")
                return False
            
            # Use first available warehouse
            warehouse = warehouses[0]
            warehouse_id = warehouse.id
            print(f"✅ Using warehouse: {warehouse.name} (ID: {warehouse_id})")
        
        print(f"\n📄 Running SQL file: {filepath}")
        print(f"🏭 Warehouse ID: {warehouse_id}")
        print("=" * 80)
        
        # Split SQL into statements (preserve newlines for proper formatting)
        # Split by semicolon that's at the end of a line or followed by whitespace/newline
        import re
        statements = []
        
        # Remove comments but keep structure
        lines = []
        for line in sql_content.split('\n'):
            stripped = line.strip()
            if stripped and not stripped.startswith('--'):
                lines.append(line)  # Keep original line with formatting
        
        # Join lines and split by semicolons
        full_sql = '\n'.join(lines)
        # Split by semicolon followed by optional whitespace/newline
        parts = re.split(r';\s*\n', full_sql)
        
        for part in parts:
            part = part.strip()
            if part and not part.startswith('--'):
                # Remove trailing semicolon if any
                part = part.rstrip(';').strip()
                if part:
                    statements.append(part)
        
        print(f"📊 Found {len(statements)} SQL statements\n")
        
        # Execute each statement
        for i, sql in enumerate(statements, 1):
            print(f"Executing statement {i}/{len(statements)}...")
            print(f"SQL: {sql[:100]}..." if len(sql) > 100 else f"SQL: {sql}")
            
            try:
                # Execute SQL statement
                result = w.statement_execution.execute_statement(
                    warehouse_id=warehouse_id,
                    statement=sql,
                    wait_timeout="30s"
                )
                
                if result.status.state == StatementState.SUCCEEDED:
                    print(f"✅ Statement {i} succeeded")
                    if result.result and result.result.data_array:
                        print(f"   Rows returned: {len(result.result.data_array)}")
                else:
                    print(f"❌ Statement {i} failed - State: {result.status.state}")
                    # Get error details
                    import json
                    error_details = {}
                    if hasattr(result, '__dict__'):
                        error_details = {k: str(v) for k, v in result.__dict__.items() if v is not None}
                    
                    # Try to get error message
                    if hasattr(result.status, 'message') and result.status.message:
                        print(f"   Error: {result.status.message}")
                    elif hasattr(result, 'manifest') and result.manifest:
                        print(f"   Manifest: {result.manifest}")
                    else:
                        print(f"   Status details: {result.status}")
                        print(f"   Full result: {json.dumps(error_details, indent=2, default=str)[:500]}")
                    
                    # Don't continue if critical statements fail
                    if i <= 1:  # USE CATALOG is critical
                        print(f"\n⚠️  Critical statement failed. Stopping execution.")
                        return False
                
            except Exception as e:
                print(f"❌ Error executing statement {i}: {e}")
                print(f"   SQL: {sql[:200]}...")
                # Continue with next statement
                continue
            
            print()
        
        print("=" * 80)
        print("✅ All SQL statements executed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Alternative: Copy the SQL to Databricks SQL Editor")
        print(f"   File: {filepath}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 run_sql_command.py <sql_file> [warehouse_id]")
        print("Example: python3 run_sql_command.py scripts/02_generate_telemetry_data.sql")
        sys.exit(1)
    
    filepath = sys.argv[1]
    warehouse_id = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = run_sql_file(filepath, warehouse_id)
    sys.exit(0 if success else 1)

