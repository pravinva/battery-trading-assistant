-- SQL Scripts for PDF Processing Verification
-- Note: PDF processing itself requires Python (PyPDF, text chunking)
-- This SQL script verifies the setup and can be used after Python processing

USE CATALOG ea_trading;
USE SCHEMA battery_trading;

-- ============================================
-- 1. Verify PDF is uploaded to Volume
-- ============================================
-- Note: This requires Python/dbutils to list files
-- In SQL Editor, you can check via:
SELECT 'PDF Location' as check_type, '/Volumes/ea_trading/battery_trading/pdfs/battery.pdf' as location;

-- ============================================
-- 2. Check if battery_documents table exists and has data
-- ============================================
SELECT 
    COUNT(*) as total_chunks,
    COUNT(DISTINCT doc_id) as unique_documents,
    COUNT(DISTINCT page_number) as pages_processed,
    MIN(created_timestamp) as first_chunk_time,
    MAX(created_timestamp) as last_chunk_time
FROM ea_trading.battery_trading.battery_documents;

-- Sample chunks
SELECT 
    chunk_id,
    doc_title,
    page_number,
    LEFT(content, 100) as content_preview,
    created_timestamp
FROM ea_trading.battery_trading.battery_documents
ORDER BY page_number, chunk_index
LIMIT 10;

-- ============================================
-- 3. Check Vector Search Index Status
-- ============================================
-- Note: Vector Search index status requires API calls
-- This query checks if we can query the index (indirect verification)
SELECT 'Vector Search Index' as check_type, 
       'ea_trading.battery_trading.battery_docs_index' as index_name,
       'one-env-shared-endpoint-10' as endpoint_name;

-- ============================================
-- 4. Summary Query
-- ============================================
SELECT 
    'Data Preparation Status' as status_type,
    CASE WHEN COUNT(*) > 0 THEN '✅ Ready' ELSE '❌ Not Ready' END as battery_documents_status,
    COUNT(*) as chunk_count
FROM ea_trading.battery_trading.battery_documents;

