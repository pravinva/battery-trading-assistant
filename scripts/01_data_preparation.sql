-- SQL Script for Data Preparation
-- Run this in Databricks SQL Editor
-- Each section can be run independently

-- ============================================
-- 1. Create Catalog and Schema
-- ============================================
CREATE CATALOG IF NOT EXISTS ea_trading;
CREATE SCHEMA IF NOT EXISTS ea_trading.battery_trading;
USE CATALOG ea_trading;
USE SCHEMA battery_trading;

-- ============================================
-- 2. Create Battery Assets Table
-- ============================================
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

ALTER TABLE battery_assets ALTER COLUMN battery_id COMMENT 'AEMO Dispatchable Unit ID (DUID)';
ALTER TABLE battery_assets ALTER COLUMN nameplate_capacity_mw COMMENT 'Maximum charge/discharge capacity in MW';
ALTER TABLE battery_assets ALTER COLUMN max_soc_mwh COMMENT 'Maximum state of charge in MWh - battery fully charged';

-- ============================================
-- 3. Create Battery Telemetry Table
-- ============================================
-- Note: This table requires Python to generate synthetic time-series data
-- Run the Python script for this part, or use the notebook

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

ALTER TABLE battery_telemetry ALTER COLUMN soc_mwh COMMENT 'Current state of charge in MWh - from PI system integration';
ALTER TABLE battery_telemetry ALTER COLUMN throughput_mwh COMMENT 'Total energy throughput over previous 7.5 hours - used for availability restrictions per Wartsila contractual limits';

-- ============================================
-- 4. Create Battery Dispatch Table
-- ============================================
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

-- ============================================
-- 5. Create Unity Catalog Volume
-- ============================================
CREATE VOLUME IF NOT EXISTS ea_trading.battery_trading.pdfs;

-- ============================================
-- 6. Create Battery Documents Table (for Vector Search)
-- ============================================
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

ALTER TABLE battery_documents ALTER COLUMN content COMMENT 'Chunked text content from battery integration documentation - used for RAG retrieval';

-- ============================================
-- Verification Queries
-- ============================================
SELECT COUNT(*) as asset_count FROM battery_assets;
SELECT COUNT(*) as telemetry_count FROM battery_telemetry;
SELECT COUNT(*) as dispatch_count FROM battery_dispatch;
SELECT COUNT(*) as document_chunks FROM battery_documents;

-- View sample data
SELECT * FROM battery_assets LIMIT 10;
SELECT * FROM battery_telemetry ORDER BY timestamp DESC LIMIT 10;
SELECT * FROM battery_dispatch ORDER BY dispatch_interval DESC LIMIT 10;

