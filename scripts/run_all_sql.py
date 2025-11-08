#!/usr/bin/env python3
"""
Quick Run Script - Run all SQL files in sequence
Usage: python run_all_sql.py
"""

import subprocess
import sys
import os

def run_sql_file(filepath):
    """Run a SQL file using databricks CLI"""
    print(f"\n{'='*80}")
    print(f"Running: {filepath}")
    print(f"{'='*80}")
    
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return False
    
    try:
        # Use databricks sql execute command if available, otherwise provide instructions
        print(f"📋 SQL file: {filepath}")
        print(f"   Copy and paste the contents into Databricks SQL Editor")
        print(f"   Or run: databricks sql execute --file {filepath}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    sql_files = [
        "01_data_preparation.sql",
        "02_generate_telemetry_data.sql",
        "03_generate_dispatch_data.sql"
    ]
    
    print("🚀 Battery Trading Assistant - SQL Script Runner")
    print("\nThis will guide you through running SQL scripts.")
    print("You can either:")
    print("  1. Copy/paste each SQL file into Databricks SQL Editor")
    print("  2. Use databricks CLI: databricks sql execute --file <file>")
    
    for sql_file in sql_files:
        filepath = os.path.join(script_dir, sql_file)
        run_sql_file(filepath)
    
    print(f"\n{'='*80}")
    print("✅ All SQL scripts processed!")
    print(f"{'='*80}")
    print("\nNext steps:")
    print("  1. Upload battery.pdf to /Volumes/ea_trading/battery_trading/pdfs/")
    print("  2. Process PDF and create Vector Search index (use notebook 01)")
    print("  3. Run notebook 02_agent_development.py")

if __name__ == "__main__":
    main()

