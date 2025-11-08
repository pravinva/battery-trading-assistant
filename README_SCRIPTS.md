# Standalone Scripts and SQL Files

## Quick Start

### Option 1: Run SQL in Databricks SQL Editor

1. Open Databricks SQL Editor
2. Run these SQL files in order:

```bash
# 1. Create tables and structure
scripts/01_data_preparation.sql

# 2. Generate telemetry data
scripts/02_generate_telemetry_data.sql

# 3. Generate dispatch data  
scripts/03_generate_dispatch_data.sql
```

### Option 2: Run Python Scripts

```bash
# Make scripts executable
chmod +x scripts/*.py

# Run data preparation
python scripts/01_data_preparation_standalone.py

# Or with databricks-connect
databricks-connect run scripts/01_data_preparation_standalone.py
```

### Option 3: Copy SQL to SQL Editor

Each SQL file can be copied and pasted directly into Databricks SQL Editor.

## Files Created

- `scripts/01_data_preparation.sql` - Creates catalog, schema, tables, and volume
- `scripts/02_generate_telemetry_data.sql` - Generates synthetic telemetry data
- `scripts/03_generate_dispatch_data.sql` - Generates synthetic dispatch data
- `scripts/01_data_preparation_standalone.py` - Python version (requires Spark)
- `scripts/run_all_sql.py` - Helper script to run all SQL files

## After Running SQL

1. Upload `battery.pdf` to `/Volumes/ea_trading/battery_trading/pdfs/battery.pdf`
2. Process PDF and create Vector Search index (use notebook 01 or Python script)
3. Continue with notebooks 02, 03, 04 for agent development and deployment

