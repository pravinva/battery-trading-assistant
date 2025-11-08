# Database Schema Documentation

## Overview

The Battery Trading Assistant uses **Unity Catalog** to manage four Delta Lake tables containing structured battery trading data. These tables store asset information, real-time telemetry, dispatch history, and document metadata for RAG (Retrieval-Augmented Generation).

**Catalog:** `ea_trading`  
**Schema:** `battery_trading`  
**Tables:** `battery_assets`, `battery_telemetry`, `battery_dispatch`, `battery_documents`

---

## Table Creation Process

### Step 1: Create Catalog and Schema

```sql
CREATE CATALOG IF NOT EXISTS ea_trading;
CREATE SCHEMA IF NOT EXISTS ea_trading.battery_trading;
USE CATALOG ea_trading;
USE SCHEMA battery_trading;
```

### Step 2: Create Tables

Tables are created using SQL DDL statements or PySpark DataFrames. The creation scripts are located in:
- **SQL Scripts:** `scripts/01_data_preparation.sql`
- **Python Notebook:** `notebooks/01_data_preparation.py`
- **Standalone Python:** `scripts/01_data_preparation_standalone.py`

### Step 3: Populate Data

- **Static Data:** `battery_assets` is populated with INSERT statements
- **Time-Series Data:** `battery_telemetry` and `battery_dispatch` are populated with synthetic data generation scripts
- **Document Data:** `battery_documents` is populated by processing `battery.pdf` and chunking it for Vector Search

---

## Table 1: `battery_assets`

**Purpose:** Master reference table containing battery asset specifications and metadata.

### Schema

| Column | Type | Description |
|--------|------|-------------|
| `battery_id` | STRING | AEMO Dispatchable Unit ID (DUID) - Primary identifier |
| `site_name` | STRING | Full site name |
| `location` | STRING | Physical location (city/region) |
| `nameplate_capacity_mw` | DOUBLE | Maximum charge/discharge capacity in MW |
| `max_soc_mwh` | DOUBLE | Maximum state of charge in MWh (battery fully charged) |
| `min_soc_mwh` | DOUBLE | Minimum state of charge in MWh (battery fully discharged) |
| `partner` | STRING | Technology partner (e.g., "Wartsila") |
| `commissioning_date` | STRING | Date when battery was commissioned (YYYY-MM-DD) |
| `aemo_registered` | BOOLEAN | Whether battery is registered with AEMO |

### Sample Data

| battery_id | site_name | location | nameplate_capacity_mw | max_soc_mwh | min_soc_mwh | partner | commissioning_date | aemo_registered |
|------------|-----------|----------|----------------------|-------------|-------------|---------|-------------------|-----------------|
| RESS2 | Riverina Energy Storage System 2 | Darlington Point | 50.0 | 75.0 | 7.5 | Wartsila | 2023-06-15 | TRUE |
| DPNTBESS | Darlington Point BESS | Darlington Point | 25.0 | 50.0 | 5.0 | Wartsila | 2022-11-20 | TRUE |
| GANNBG1 | Wooreen BESS Generator | Jeeralang | 150.0 | 300.0 | 30.0 | Wartsila | 2024-03-10 | TRUE |
| GANNBL1 | Wooreen BESS Load | Jeeralang | 150.0 | 300.0 | 30.0 | Wartsila | 2024-03-10 | TRUE |

### Creation SQL

```sql
CREATE OR REPLACE TABLE battery_assets (
    battery_id STRING NOT NULL,
    site_name STRING NOT NULL,
    location STRING,
    nameplate_capacity_mw DOUBLE,
    max_soc_mwh DOUBLE,
    min_soc_mwh DOUBLE,
    partner STRING,
    commissioning_date STRING,
    aemo_registered BOOLEAN
);

INSERT INTO battery_assets VALUES
    ('RESS2', 'Riverina Energy Storage System 2', 'Darlington Point', 50.0, 75.0, 7.5, 'Wartsila', '2023-06-15', TRUE),
    ('DPNTBESS', 'Darlington Point BESS', 'Darlington Point', 25.0, 50.0, 5.0, 'Wartsila', '2022-11-20', TRUE),
    ('GANNBG1', 'Wooreen BESS Generator', 'Jeeralang', 150.0, 300.0, 30.0, 'Wartsila', '2024-03-10', TRUE),
    ('GANNBL1', 'Wooreen BESS Load', 'Jeeralang', 150.0, 300.0, 30.0, 'Wartsila', '2024-03-10', TRUE);
```

### Key Relationships

- **Foreign Key:** Referenced by `battery_telemetry.battery_id` and `battery_dispatch.battery_id`
- **Use Cases:** Asset lookups, capacity planning, site information queries

---

## Table 2: `battery_telemetry`

**Purpose:** Time-series table storing real-time battery state of charge (SoC) and operational capabilities from PI system integration.

### Schema

| Column | Type | Description |
|--------|------|-------------|
| `timestamp` | TIMESTAMP | Reading timestamp (5-minute intervals) |
| `battery_id` | STRING | Foreign key to `battery_assets.battery_id` |
| `duid` | STRING | AEMO Dispatchable Unit ID (same as battery_id) |
| `soc_mwh` | DOUBLE | Current state of charge in MWh (from PI system) |
| `soc_percent` | DOUBLE | State of charge as percentage (0-100%) |
| `capability_charge_mw` | DOUBLE | Maximum charge capability at current SoC |
| `capability_discharge_mw` | DOUBLE | Maximum discharge capability at current SoC |
| `cum_energy_exported_mwh` | DOUBLE | Cumulative energy exported (lifetime) |
| `cum_energy_imported_mwh` | DOUBLE | Cumulative energy imported (lifetime) |
| `throughput_mwh` | DOUBLE | Total energy throughput over previous 7.5 hours (for availability restrictions) |
| `fullpackenergy_mwh` | DOUBLE | Full pack energy capacity (matches `max_soc_mwh` from assets) |
| `reading_age_minutes` | INT | Age of reading in minutes (for data freshness checks) |

### Data Characteristics

- **Frequency:** 5-minute intervals (288 readings per day)
- **Retention:** Last 24 hours of synthetic data (configurable)
- **Data Source:** Simulated PI system integration
- **Key Metrics:**
  - SoC varies between 10-90% of capacity
  - Capabilities depend on SoC (reduced near limits)
  - Throughput tracked for Wartsila contractual limits

### Creation SQL

```sql
CREATE OR REPLACE TABLE battery_telemetry (
    timestamp TIMESTAMP NOT NULL,
    battery_id STRING NOT NULL,
    duid STRING NOT NULL,
    soc_mwh DOUBLE,
    soc_percent DOUBLE,
    capability_charge_mw DOUBLE,
    capability_discharge_mw DOUBLE,
    cum_energy_exported_mwh DOUBLE,
    cum_energy_imported_mwh DOUBLE,
    throughput_mwh DOUBLE,
    fullpackenergy_mwh DOUBLE,
    reading_age_minutes INT
);
```

### Data Generation

Telemetry data is generated synthetically using SQL scripts (`scripts/02_generate_telemetry_data.sql`) or Python (`notebooks/01_data_preparation.py`). The generation logic:

1. **SoC Simulation:** Varies between 40-80% of capacity with random fluctuations
2. **Capability Calculation:** 
   - Charge capability reduced when SoC > 85%
   - Discharge capability reduced when SoC < 15%
3. **Throughput Tracking:** Rolling 7.5-hour window for availability restrictions
4. **Reading Age:** Simulated freshness (0-15 minutes)

### Sample Query

```sql
SELECT battery_id, soc_percent, capability_charge_mw, capability_discharge_mw
FROM battery_telemetry
WHERE battery_id = 'RESS2'
ORDER BY timestamp DESC
LIMIT 1;
```

### Use Cases

- Real-time SoC monitoring
- Availability calculations
- Capability queries for trading decisions
- Data freshness validation

---

## Table 3: `battery_dispatch`

**Purpose:** Historical dispatch records showing energy market participation, spot prices, and revenue.

### Schema

| Column | Type | Description |
|--------|------|-------------|
| `dispatch_interval` | TIMESTAMP | 5-minute dispatch interval timestamp |
| `battery_id` | STRING | Foreign key to `battery_assets.battery_id` |
| `duid` | STRING | AEMO Dispatchable Unit ID |
| `dispatch_mw` | DOUBLE | Dispatch amount (positive = discharge, negative = charge) |
| `spot_price_dollar_per_mwh` | DOUBLE | NEM spot price at dispatch interval ($/MWh) |
| `revenue_dollar` | DOUBLE | Revenue for this interval (dispatch_mw × price × duration) |
| `fcas_service` | STRING | FCAS service type (e.g., "RAISE_REG", "LOWER_REG") or NULL |
| `fcas_mw` | DOUBLE | FCAS service MW provided |
| `fcas_price_dollar_per_mwh` | DOUBLE | FCAS service price ($/MWh) |

### Data Characteristics

- **Frequency:** 5-minute intervals (288 intervals per day)
- **Settlement:** 5-minute settlement periods
- **Revenue Calculation:** `dispatch_mw × spot_price × (5 minutes / 60 minutes)`
- **FCAS Participation:** ~30% of intervals include FCAS services

### Creation SQL

```sql
CREATE OR REPLACE TABLE battery_dispatch (
    dispatch_interval TIMESTAMP NOT NULL,
    battery_id STRING NOT NULL,
    duid STRING NOT NULL,
    dispatch_mw DOUBLE,
    spot_price_dollar_per_mwh DOUBLE,
    revenue_dollar DOUBLE,
    fcas_service STRING,
    fcas_mw DOUBLE,
    fcas_price_dollar_per_mwh DOUBLE
);
```

### Data Generation

Dispatch data is generated synthetically (`scripts/03_generate_dispatch_data.sql`) with:
- **Dispatch Range:** -30 to +30 MW (random)
- **Spot Prices:** $50-$300/MWh (random)
- **FCAS Services:** Random assignment (30% probability)
- **Revenue:** Calculated from dispatch and price

### Sample Query

```sql
SELECT 
    battery_id,
    SUM(revenue_dollar) as total_revenue,
    AVG(spot_price_dollar_per_mwh) as avg_price,
    COUNT(*) as intervals
FROM battery_dispatch
WHERE dispatch_interval >= current_timestamp() - INTERVAL 24 HOURS
GROUP BY battery_id;
```

### Use Cases

- Revenue analysis and reporting
- Performance comparison across batteries
- Spot price trend analysis
- FCAS participation tracking

---

## Table 4: `battery_documents`

**Purpose:** Chunked text content from battery integration documentation (`battery.pdf`) for Vector Search and RAG.

### Schema

| Column | Type | Description |
|--------|------|-------------|
| `doc_id` | STRING | Document identifier (e.g., "battery.pdf") |
| `chunk_id` | STRING | Unique chunk identifier |
| `content` | STRING | Chunked text content (for RAG retrieval) |
| `doc_title` | STRING | Document title |
| `doc_type` | STRING | Document type (e.g., "PDF", "Technical Manual") |
| `page_number` | INT | Source page number |
| `chunk_index` | INT | Chunk index within document |
| `created_timestamp` | TIMESTAMP | When chunk was created |

### Data Population

1. **PDF Upload:** `battery.pdf` uploaded to Unity Catalog Volume (`/Volumes/ea_trading/battery_trading/pdfs/`)
2. **PDF Processing:** Extracted using `pypdf` library
3. **Chunking:** Split into ~500-character chunks with overlap using `langchain-text-splitters`
4. **Storage:** Chunks inserted into `battery_documents` table
5. **Vector Index:** Delta Sync Vector Search index created on this table

### Creation SQL

```sql
CREATE OR REPLACE TABLE battery_documents (
    doc_id STRING,
    chunk_id STRING,
    content STRING,
    doc_title STRING,
    doc_type STRING,
    page_number INT,
    chunk_index INT,
    created_timestamp TIMESTAMP
);
```

### Vector Search Integration

- **Index Name:** `ea_trading.battery_trading.battery_docs_index`
- **Embedding Model:** `databricks-gte-large-en`
- **Index Type:** Delta Sync (automatically syncs with table changes)
- **Change Data Feed:** Enabled on `battery_documents` table

### Use Cases

- Technical documentation queries
- Process explanations (PI integration, AEMO bidding)
- Operational limits and guidelines
- Troubleshooting and FAQs

---

## Data Relationships

```
battery_assets (1) ──┐
                     ├── (many) battery_telemetry
                     └── (many) battery_dispatch

battery_documents (standalone, used for Vector Search)
```

### Foreign Key Relationships

- `battery_telemetry.battery_id` → `battery_assets.battery_id`
- `battery_dispatch.battery_id` → `battery_assets.battery_id`

### Join Examples

```sql
-- Get current SoC with asset info
SELECT 
    a.battery_id,
    a.site_name,
    a.nameplate_capacity_mw,
    t.soc_percent,
    t.capability_charge_mw,
    t.capability_discharge_mw
FROM battery_assets a
JOIN battery_telemetry t ON a.battery_id = t.battery_id
WHERE t.timestamp = (SELECT MAX(timestamp) FROM battery_telemetry WHERE battery_id = a.battery_id);

-- Get revenue with asset info
SELECT 
    a.battery_id,
    a.site_name,
    SUM(d.revenue_dollar) as total_revenue
FROM battery_assets a
JOIN battery_dispatch d ON a.battery_id = d.battery_id
WHERE d.dispatch_interval >= current_timestamp() - INTERVAL 24 HOURS
GROUP BY a.battery_id, a.site_name;
```

---

## Data Generation Scripts

### SQL Scripts

1. **`scripts/01_data_preparation.sql`**
   - Creates catalog, schema, and all table structures
   - Inserts static `battery_assets` data
   - Creates Unity Catalog Volume

2. **`scripts/02_generate_telemetry_data.sql`**
   - Generates 24 hours of telemetry data (288 rows per battery)
   - Creates synthetic SoC, capabilities, and throughput data

3. **`scripts/03_generate_dispatch_data.sql`**
   - Generates 24 hours of dispatch data (288 intervals per battery)
   - Creates synthetic dispatch, prices, and revenue

### Python Scripts

1. **`notebooks/01_data_preparation.py`**
   - Complete data preparation notebook
   - Creates tables and generates synthetic data
   - Processes PDF and creates Vector Search index

2. **`scripts/process_pdf_and_create_index.py`**
   - Standalone script for PDF processing
   - Chunks PDF and creates Vector Search index

---

## Verification Queries

After table creation, verify data:

```sql
-- Count records
SELECT 'battery_assets' as table_name, COUNT(*) as count FROM battery_assets
UNION ALL
SELECT 'battery_telemetry', COUNT(*) FROM battery_telemetry
UNION ALL
SELECT 'battery_dispatch', COUNT(*) FROM battery_dispatch
UNION ALL
SELECT 'battery_documents', COUNT(*) FROM battery_documents;

-- Check latest telemetry
SELECT battery_id, MAX(timestamp) as latest_reading
FROM battery_telemetry
GROUP BY battery_id;

-- Check revenue summary
SELECT battery_id, SUM(revenue_dollar) as total_revenue
FROM battery_dispatch
GROUP BY battery_id;
```

---

## Notes

- **Synthetic Data:** All data is synthetically generated for demonstration purposes
- **Time Windows:** Telemetry and dispatch data cover the last 24 hours
- **Update Frequency:** Data can be refreshed by re-running generation scripts
- **Unity Catalog:** All tables are managed under Unity Catalog for governance and lineage
- **Vector Search:** `battery_documents` table has a Delta Sync Vector Search index for RAG queries

