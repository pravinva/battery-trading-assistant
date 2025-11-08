-- Enable Change Data Feed (CDF) for Vector Search Delta Sync Index
-- Run this SQL first, then create the index

USE CATALOG ea_trading;
USE SCHEMA battery_trading;

-- Enable Change Data Feed on battery_documents table
ALTER TABLE battery_documents SET TBLPROPERTIES (delta.enableChangeDataFeed = true);

-- Verify CDF is enabled
SHOW TBLPROPERTIES battery_documents;

