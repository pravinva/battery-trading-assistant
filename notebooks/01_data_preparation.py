# Databricks notebook source
# MAGIC %md
# MAGIC # Phase 1: Battery Trading Data Preparation
# MAGIC 
# MAGIC This notebook prepares:
# MAGIC 1. Synthetic Delta Lake tables (telemetry, availability, dispatch)
# MAGIC 2. Vector Search index on battery.pdf
# MAGIC 3. Unity Catalog governance setup

# COMMAND ----------
# MAGIC %pip install databricks-vectorsearch pypdf langchain-text-splitters databricks-agents mlflow

# COMMAND ----------
dbutils.library.restartPython()

# COMMAND ----------
# MAGIC %md
# MAGIC ## 1.1 Create Delta Tables for Structured Data

# COMMAND ----------
from pyspark.sql.types import *
from pyspark.sql.functions import *
from datetime import datetime, timedelta
import random

# Set catalog and schema
catalog = "ea_trading"
schema = "battery_trading"

spark.sql(f"CREATE CATALOG IF NOT EXISTS {catalog}")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")
spark.sql(f"USE CATALOG {catalog}")
spark.sql(f"USE SCHEMA {schema}")

# COMMAND ----------
# MAGIC %md
# MAGIC ### Battery Assets Table

# COMMAND ----------
battery_assets_data = [
    ("RESS2", "Riverina Energy Storage System 2", "Darlington Point", 50.0, 75.0, 7.5, "Wartsila", "2023-06-15", True),
    ("DPNTBESS", "Darlington Point BESS", "Darlington Point", 25.0, 50.0, 5.0, "Wartsila", "2022-11-20", True),
    ("GANNBG1", "Wooreen BESS Generator", "Jeeralang", 150.0, 300.0, 30.0, "Wartsila", "2024-03-10", True),
    ("GANNBL1", "Wooreen BESS Load", "Jeeralang", 150.0, 300.0, 30.0, "Wartsila", "2024-03-10", True),
]

battery_assets_schema = StructType([
    StructField("battery_id", StringType(), False),
    StructField("site_name", StringType(), False),
    StructField("location", StringType(), True),
    StructField("nameplate_capacity_mw", DoubleType(), True),
    StructField("max_soc_mwh", DoubleType(), True),
    StructField("min_soc_mwh", DoubleType(), True),
    StructField("partner", StringType(), True),
    StructField("commissioning_date", StringType(), True),
    StructField("aemo_registered", BooleanType(), True),
])

battery_assets_df = spark.createDataFrame(battery_assets_data, battery_assets_schema)
battery_assets_df.write.mode("overwrite").saveAsTable("battery_assets")

# Add column comments
spark.sql("""
ALTER TABLE battery_assets 
ALTER COLUMN battery_id COMMENT 'AEMO Dispatchable Unit ID (DUID)';
""")
spark.sql("""
ALTER TABLE battery_assets 
ALTER COLUMN nameplate_capacity_mw COMMENT 'Maximum charge/discharge capacity in MW';
""")
spark.sql("""
ALTER TABLE battery_assets 
ALTER COLUMN max_soc_mwh COMMENT 'Maximum state of charge in MWh - battery fully charged';
""")

print("✅ Created battery_assets table")

# COMMAND ----------
# MAGIC %md
# MAGIC ### Battery Telemetry Table (Time Series)

# COMMAND ----------
# Generate synthetic telemetry data for last 24 hours
from datetime import datetime, timedelta
import random

batteries = ["RESS2", "DPNTBESS", "GANNBG1", "GANNBL1"]
battery_capacities = {"RESS2": 75.0, "DPNTBESS": 50.0, "GANNBG1": 300.0, "GANNBL1": 300.0}

telemetry_data = []
base_time = datetime.now() - timedelta(hours=24)

for battery in batteries:
    max_soc = battery_capacities[battery]
    current_soc = max_soc * random.uniform(0.4, 0.8)  # Start at 40-80% SoC
    
    for i in range(288):  # 5-minute intervals for 24 hours
        timestamp = base_time + timedelta(minutes=5*i)
        
        # Simulate charging/discharging patterns
        soc_change = random.uniform(-2, 2)  # MWh change per interval
        current_soc = max(max_soc * 0.1, min(max_soc * 0.9, current_soc + soc_change))
        
        soc_percent = (current_soc / max_soc) * 100
        
        # Capability depends on SoC
        capability_charge = max_soc * 0.67 if soc_percent < 85 else max_soc * 0.3
        capability_discharge = max_soc * 0.67 if soc_percent > 15 else max_soc * 0.3
        
        telemetry_data.append((
            timestamp,
            battery,
            battery,  # DUID same as battery_id for simplicity
            current_soc,
            soc_percent,
            capability_charge,
            capability_discharge,
            random.uniform(100, 500),  # cum_energy_exported
            random.uniform(100, 500),  # cum_energy_imported
            random.uniform(50, 150),  # throughput last 7.5hrs
            max_soc,  # fullpackenergy
            random.randint(0, 15)  # reading_age_minutes
        ))

telemetry_schema = StructType([
    StructField("timestamp", TimestampType(), False),
    StructField("battery_id", StringType(), False),
    StructField("duid", StringType(), False),
    StructField("soc_mwh", DoubleType(), True),
    StructField("soc_percent", DoubleType(), True),
    StructField("capability_charge_mw", DoubleType(), True),
    StructField("capability_discharge_mw", DoubleType(), True),
    StructField("cum_energy_exported_mwh", DoubleType(), True),
    StructField("cum_energy_imported_mwh", DoubleType(), True),
    StructField("throughput_mwh", DoubleType(), True),
    StructField("fullpackenergy_mwh", DoubleType(), True),
    StructField("reading_age_minutes", IntegerType(), True),
])

telemetry_df = spark.createDataFrame(telemetry_data, telemetry_schema)
telemetry_df.write.mode("overwrite").saveAsTable("battery_telemetry")

# Add column comments
spark.sql("""
ALTER TABLE battery_telemetry 
ALTER COLUMN soc_mwh COMMENT 'Current state of charge in MWh - from PI system integration';
""")
spark.sql("""
ALTER TABLE battery_telemetry 
ALTER COLUMN throughput_mwh COMMENT 'Total energy throughput over previous 7.5 hours - used for availability restrictions per Wartsila contractual limits';
""")

print(f"✅ Created battery_telemetry table with {telemetry_df.count()} rows")

# COMMAND ----------
# MAGIC %md
# MAGIC ### Battery Dispatch Table (Simplified)

# COMMAND ----------
dispatch_data = []
base_time = datetime.now() - timedelta(hours=24)

for battery in batteries:
    for i in range(288):
        timestamp = base_time + timedelta(minutes=5*i)
        
        # Simulate dispatch (positive = discharge, negative = charge)
        dispatch_mw = random.uniform(-30, 30)
        spot_price = random.uniform(50, 300)  # $/MWh
        revenue = (dispatch_mw * spot_price * (5/60))  # 5-minute settlement
        
        dispatch_data.append((
            timestamp,
            battery,
            battery,
            dispatch_mw,
            spot_price,
            revenue,
            random.choice(["RAISE_REG", "LOWER_REG", None]),
            random.uniform(0, 5) if random.random() > 0.7 else 0,
            random.uniform(0, 20) if random.random() > 0.7 else 0
        ))

dispatch_schema = StructType([
    StructField("dispatch_interval", TimestampType(), False),
    StructField("battery_id", StringType(), False),
    StructField("duid", StringType(), False),
    StructField("dispatch_mw", DoubleType(), True),
    StructField("spot_price_dollar_per_mwh", DoubleType(), True),
    StructField("revenue_dollar", DoubleType(), True),
    StructField("fcas_service", StringType(), True),
    StructField("fcas_mw", DoubleType(), True),
    StructField("fcas_price_dollar_per_mwh", DoubleType(), True),
])

dispatch_df = spark.createDataFrame(dispatch_data, dispatch_schema)
dispatch_df.write.mode("overwrite").saveAsTable("battery_dispatch")

print(f"✅ Created battery_dispatch table with {dispatch_df.count()} rows")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 1.2 Create Unity Catalog Volume and Upload PDF

# COMMAND ----------
# Create Volume for PDF storage (Unity Catalog modern approach)
volume_name = "pdfs"
volume_path = f"{catalog}.{schema}.{volume_name}"

try:
    spark.sql(f"CREATE VOLUME IF NOT EXISTS {volume_path}")
    print(f"✅ Created Volume: {volume_path}")
except Exception as e:
    if "already exists" in str(e).lower() or "RESOURCE_ALREADY_EXISTS" in str(e):
        print(f"✅ Volume already exists: {volume_path}")
    else:
        raise e

# COMMAND ----------
# Upload battery.pdf to Unity Catalog Volume
# Note: Upload the PDF file manually via Databricks UI or use dbutils.fs.cp from uploaded location
# For now, we'll check if it exists, if not, provide instructions

pdf_volume_path = f"/Volumes/{catalog}/{schema}/{volume_name}/battery.pdf"

# Check if PDF exists in Volume
try:
    files = dbutils.fs.ls(f"/Volumes/{catalog}/{schema}/{volume_name}/")
    pdf_exists = any(f.name == "battery.pdf" for f in files)
    if pdf_exists:
        print(f"✅ PDF found in Volume: {pdf_volume_path}")
    else:
        print(f"⚠️  PDF not found in Volume. Attempting to copy from temporary location...")
        # Try to copy from dbfs:/tmp if it exists there
        try:
            dbutils.fs.cp("dbfs:/tmp/battery.pdf", pdf_volume_path)
            print(f"✅ Successfully copied PDF from dbfs:/tmp/battery.pdf to Volume")
        except Exception as copy_error:
            print(f"⚠️  Could not copy from temporary location. Please upload battery.pdf to: {pdf_volume_path}")
            print("   You can upload via:")
            print("   1. Databricks UI: Catalog → Volumes → ea_trading.battery_trading.pdfs → Upload")
            print("   2. Or upload to dbfs:/tmp/battery.pdf first, then re-run this cell")
except Exception as e:
    print(f"⚠️  Volume path not accessible yet. Please ensure PDF is uploaded to: {pdf_volume_path}")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 1.3 Create Vector Search Index on Battery PDF

# COMMAND ----------
from databricks.vector_search.client import VectorSearchClient
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import pandas as pd

# COMMAND ----------
# Read and chunk PDF from Unity Catalog Volume
pdf_path = pdf_volume_path
reader = PdfReader(pdf_path)

chunks_data = []
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=50,
    separators=["\n\n", "\n", ". ", " ", ""]
)

for page_num, page in enumerate(reader.pages):
    text = page.extract_text()
    if text.strip():  # Only process non-empty pages
        page_chunks = text_splitter.split_text(text)
        
        for idx, chunk in enumerate(page_chunks):
            chunks_data.append({
                'doc_id': 'battery_integration_wartsila_v1',
                'chunk_id': f'bat_int_p{page_num:03d}_c{idx:03d}',
                'content': chunk,
                'doc_title': 'Battery Trading Integration Architecture - Wartsila BESS',
                'doc_type': 'technical_specification',
                'page_number': page_num + 1,
                'chunk_index': idx,
                'created_timestamp': datetime.now()
            })

print(f"✅ Extracted {len(chunks_data)} chunks from {len(reader.pages)} pages")

# COMMAND ----------
# Save chunks to Delta table
chunks_df = spark.createDataFrame(pd.DataFrame(chunks_data))
chunks_df.write.mode("overwrite").saveAsTable("battery_documents")

spark.sql("""
ALTER TABLE battery_documents 
ALTER COLUMN content COMMENT 'Chunked text content from battery integration documentation - used for RAG retrieval';
""")

print("✅ Created battery_documents table")

# COMMAND ----------
# Create Vector Search index using existing endpoint
vsc = VectorSearchClient(disable_notice=True)

# Use existing shared endpoint
endpoint_name = "one-env-shared-endpoint-10"
print(f"✅ Using Vector Search endpoint: {endpoint_name}")

# COMMAND ----------
# Create Vector Search Index
index_name = f"{catalog}.{schema}.battery_docs_index"

index = vsc.create_delta_sync_index(
    endpoint_name=endpoint_name,
    index_name=index_name,
    source_table_name=f"{catalog}.{schema}.battery_documents",
    pipeline_type="TRIGGERED",
    primary_key="chunk_id",
    embedding_source_column="content",
    embedding_model_endpoint_name="databricks-gte-large-en"
)

print(f"✅ Created Vector Search index: {index_name}")

# COMMAND ----------
# Sync the index
index.sync()
print("✅ Vector Search index sync triggered")

# COMMAND ----------
# Test vector search
results = index.similarity_search(
    query_text="How is throughput calculated for batteries?",
    columns=["content", "doc_title", "page_number"],
    num_results=3
)

print("\n🔍 Test Vector Search Results:")
for i, hit in enumerate(results.get('result', {}).get('data_array', []), 1):
    print(f"\nResult {i}:")
    print(f"Page: {hit[2]}")
    print(f"Content: {hit[0][:200]}...")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 1.4 Validation Summary

# COMMAND ----------
print("=" * 80)
print("DATA PREPARATION COMPLETE")
print("=" * 80)
print(f"\n📊 Delta Tables Created:")
print(f"   ✅ {catalog}.{schema}.battery_assets: {spark.table('battery_assets').count()} rows")
print(f"   ✅ {catalog}.{schema}.battery_telemetry: {spark.table('battery_telemetry').count()} rows")
print(f"   ✅ {catalog}.{schema}.battery_dispatch: {spark.table('battery_dispatch').count()} rows")
print(f"   ✅ {catalog}.{schema}.battery_documents: {spark.table('battery_documents').count()} chunks")

print(f"\n🔍 Vector Search:")
print(f"   ✅ Endpoint: {endpoint_name}")
print(f"   ✅ Index: {index_name}")

print(f"\n➡️  Next Step: Run notebook 02_agent_development.py")

