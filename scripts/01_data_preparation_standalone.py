#!/usr/bin/env python3
"""
Standalone script for Data Preparation
Run with: python 01_data_preparation_standalone.py
Or with databricks-connect: databricks-connect run 01_data_preparation_standalone.py
"""

from pyspark.sql import SparkSession
from pyspark.sql.types import *
from pyspark.sql.functions import *
from datetime import datetime, timedelta
import random
from databricks.vector_search.client import VectorSearchClient
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import pandas as pd

# Initialize Spark
spark = SparkSession.builder.appName("BatteryTradingDataPrep").getOrCreate()

# Set catalog and schema
catalog = "ea_trading"
schema = "battery_trading"

print("Creating catalog and schema...")
spark.sql(f"CREATE CATALOG IF NOT EXISTS {catalog}")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")
spark.sql(f"USE CATALOG {catalog}")
spark.sql(f"USE SCHEMA {schema}")

print("\n=== Creating Battery Assets Table ===")
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

spark.sql("ALTER TABLE battery_assets ALTER COLUMN battery_id COMMENT 'AEMO Dispatchable Unit ID (DUID)'")
spark.sql("ALTER TABLE battery_assets ALTER COLUMN nameplate_capacity_mw COMMENT 'Maximum charge/discharge capacity in MW'")
spark.sql("ALTER TABLE battery_assets ALTER COLUMN max_soc_mwh COMMENT 'Maximum state of charge in MWh - battery fully charged'")
print("✅ Created battery_assets table")

print("\n=== Creating Battery Telemetry Table ===")
batteries = ["RESS2", "DPNTBESS", "GANNBG1", "GANNBL1"]
battery_capacities = {"RESS2": 75.0, "DPNTBESS": 50.0, "GANNBG1": 300.0, "GANNBL1": 300.0}

telemetry_data = []
base_time = datetime.now() - timedelta(hours=24)

for battery in batteries:
    max_soc = battery_capacities[battery]
    current_soc = max_soc * random.uniform(0.4, 0.8)
    
    for i in range(288):  # 5-minute intervals for 24 hours
        timestamp = base_time + timedelta(minutes=5*i)
        soc_change = random.uniform(-2, 2)
        current_soc = max(max_soc * 0.1, min(max_soc * 0.9, current_soc + soc_change))
        soc_percent = (current_soc / max_soc) * 100
        
        capability_charge = max_soc * 0.67 if soc_percent < 85 else max_soc * 0.3
        capability_discharge = max_soc * 0.67 if soc_percent > 15 else max_soc * 0.3
        
        telemetry_data.append((
            timestamp, battery, battery, current_soc, soc_percent,
            capability_charge, capability_discharge,
            random.uniform(100, 500), random.uniform(100, 500),
            random.uniform(50, 150), max_soc, random.randint(0, 15)
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
spark.sql("ALTER TABLE battery_telemetry ALTER COLUMN soc_mwh COMMENT 'Current state of charge in MWh - from PI system integration'")
spark.sql("ALTER TABLE battery_telemetry ALTER COLUMN throughput_mwh COMMENT 'Total energy throughput over previous 7.5 hours - used for availability restrictions per Wartsila contractual limits'")
print(f"✅ Created battery_telemetry table with {telemetry_df.count()} rows")

print("\n=== Creating Battery Dispatch Table ===")
dispatch_data = []
base_time = datetime.now() - timedelta(hours=24)

for battery in batteries:
    for i in range(288):
        timestamp = base_time + timedelta(minutes=5*i)
        dispatch_mw = random.uniform(-30, 30)
        spot_price = random.uniform(50, 300)
        revenue = (dispatch_mw * spot_price * (5/60))
        
        dispatch_data.append((
            timestamp, battery, battery, dispatch_mw, spot_price, revenue,
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

print("\n=== Creating Unity Catalog Volume ===")
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

pdf_volume_path = f"/Volumes/{catalog}/{schema}/{volume_name}/battery.pdf"
print(f"\n⚠️  Please upload battery.pdf to: {pdf_volume_path}")
print("   You can upload via Databricks UI: Catalog → Volumes → ea_trading.battery_trading.pdfs → Upload")

print("\n=== Processing PDF and Creating Vector Search Index ===")
print("Note: This requires the PDF to be uploaded first.")
print("After uploading, run the PDF processing section manually or use the notebook.")

print("\n" + "=" * 80)
print("DATA PREPARATION COMPLETE (Tables Created)")
print("=" * 80)
print(f"\n📊 Delta Tables Created:")
print(f"   ✅ {catalog}.{schema}.battery_assets")
print(f"   ✅ {catalog}.{schema}.battery_telemetry")
print(f"   ✅ {catalog}.{schema}.battery_dispatch")
print(f"\n📁 Volume Created:")
print(f"   ✅ {volume_path}")
print(f"\n➡️  Next Steps:")
print(f"   1. Upload battery.pdf to {pdf_volume_path}")
print(f"   2. Run notebook 02_agent_development.py or continue with PDF processing")

