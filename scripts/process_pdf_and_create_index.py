#!/usr/bin/env python3
"""
Process PDF and Create Vector Search Index
Run with: python3 process_pdf_and_create_index.py
"""

from pyspark.sql import SparkSession
from databricks.vector_search.client import VectorSearchClient
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import pandas as pd
from datetime import datetime

# Initialize Spark
spark = SparkSession.builder.appName("BatteryPDFProcessing").getOrCreate()

# Configuration
catalog = "ea_trading"
schema = "battery_trading"
endpoint_name = "one-env-shared-endpoint-10"
pdf_volume_path = f"/Volumes/{catalog}/{schema}/pdfs/battery.pdf"

print("=" * 80)
print("PDF Processing and Vector Search Index Creation")
print("=" * 80)

# Set catalog and schema
spark.sql(f"USE CATALOG {catalog}")
spark.sql(f"USE SCHEMA {schema}")

print(f"\n📄 Reading PDF from: {pdf_volume_path}")
reader = PdfReader(pdf_volume_path)

chunks_data = []
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=50,
    separators=["\n\n", "\n", ". ", " ", ""]
)

print(f"📖 Processing {len(reader.pages)} pages...")

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

print("\n💾 Saving chunks to Delta table...")
chunks_df = spark.createDataFrame(pd.DataFrame(chunks_data))
chunks_df.write.mode("overwrite").saveAsTable("battery_documents")

spark.sql("""
ALTER TABLE battery_documents 
ALTER COLUMN content COMMENT 'Chunked text content from battery integration documentation - used for RAG retrieval';
""")

print("✅ Created battery_documents table")

print(f"\n🔍 Creating Vector Search index using endpoint: {endpoint_name}")
vsc = VectorSearchClient(disable_notice=True)

index_name = f"{catalog}.{schema}.battery_docs_index"

try:
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
    
    # Sync the index
    print("\n🔄 Syncing index...")
    index.sync()
    print("✅ Vector Search index sync triggered")
    
    # Test vector search
    print("\n🧪 Testing vector search...")
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
    
    print("\n" + "=" * 80)
    print("✅ PDF Processing and Vector Search Index Creation Complete!")
    print("=" * 80)
    print(f"\n📊 Summary:")
    print(f"   ✅ Processed PDF: {len(reader.pages)} pages")
    print(f"   ✅ Created chunks: {len(chunks_data)}")
    print(f"   ✅ Delta table: {catalog}.{schema}.battery_documents")
    print(f"   ✅ Vector Search endpoint: {endpoint_name}")
    print(f"   ✅ Vector Search index: {index_name}")
    
except Exception as e:
    print(f"❌ Error creating index: {e}")
    if "already exists" in str(e).lower() or "RESOURCE_ALREADY_EXISTS" in str(e):
        print(f"⚠️  Index may already exist. Attempting to sync existing index...")
        try:
            index = vsc.get_index(endpoint_name=endpoint_name, index_name=index_name)
            index.sync()
            print(f"✅ Synced existing index: {index_name}")
        except Exception as e2:
            print(f"❌ Error syncing index: {e2}")
            raise e2
    else:
        raise e

