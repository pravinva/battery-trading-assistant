#!/usr/bin/env python3
"""
Create Vector Search Index (assumes PDF chunks already exist in battery_documents table)
Usage: python3 create_vector_index_only.py
"""

from databricks.sdk import WorkspaceClient
from databricks.vector_search.client import VectorSearchClient

def create_vector_index():
    """Create Vector Search index if chunks already exist"""
    w = WorkspaceClient()
    vsc = VectorSearchClient(disable_notice=True)
    
    # Configuration
    catalog = "ea_trading"
    schema = "battery_trading"
    endpoint_name = "one-env-shared-endpoint-10"
    index_name = f"{catalog}.{schema}.battery_docs_index"
    
    print("=" * 80)
    print("Create Vector Search Index")
    print("=" * 80)
    print(f"\n🔍 Endpoint: {endpoint_name}")
    print(f"📊 Index: {index_name}")
    print(f"📁 Source Table: {catalog}.{schema}.battery_documents")
    
    try:
        # Check if index already exists
        try:
            existing_index = vsc.get_index(endpoint_name=endpoint_name, index_name=index_name)
            print(f"\n✅ Index already exists. Syncing...")
            # Wait for index to be ready
            import time
            max_attempts = 12
            for i in range(max_attempts):
                try:
                    existing_index.sync()
                    print(f"✅ Synced existing index: {index_name}")
                    break
                except Exception as sync_error:
                    if "not ready" in str(sync_error).lower() and i < max_attempts - 1:
                        if i % 2 == 0:
                            print(f"   Waiting for index to be ready... ({i*5}s)")
                        time.sleep(5)
                        continue
                    else:
                        print(f"⚠️  Index exists but sync failed: {sync_error}")
                        return False
            
            # Test vector search
            try:
                print("\n🧪 Testing vector search...")
                results = existing_index.similarity_search(
                    query_text="How is throughput calculated for batteries?",
                    columns=["content", "doc_title", "page_number"],
                    num_results=3
                )
                
                print("\n🔍 Test Vector Search Results:")
                for i, hit in enumerate(results.get('result', {}).get('data_array', []), 1):
                    print(f"\nResult {i}:")
                    print(f"Page: {hit[2]}")
                    print(f"Content: {hit[0][:200]}...")
            except Exception as test_error:
                print(f"⚠️  Index not ready for queries yet: {test_error}")
            
            print("\n" + "=" * 80)
            print("✅ Vector Search Index Ready!")
            print("=" * 80)
            return True
        except Exception as get_error:
            # Index doesn't exist, create it
            if "not found" not in str(get_error).lower() and "does not exist" not in str(get_error).lower():
                print(f"⚠️  Error checking index: {get_error}")
                raise
        
        # Create new index
        print(f"\n🔄 Creating Vector Search index...")
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
        
        # Wait a bit for index to be ready, then sync
        print("\n⏳ Waiting for index to be ready...")
        import time
        max_attempts = 12
        for i in range(max_attempts):
            time.sleep(5)
            try:
                index.sync()
                print("✅ Vector Search index sync triggered")
                break
            except Exception as sync_error:
                if "not ready" in str(sync_error).lower() and i < max_attempts - 1:
                    if i % 2 == 0:
                        print(f"   Still initializing... ({i*5}s)")
                    continue
                else:
                    print(f"⚠️  Sync may need to be triggered later when index is ready")
                    print(f"   Index created but not yet ready for sync")
                    return True
        
        # Test vector search (if index is ready)
        try:
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
        except Exception as test_error:
            print(f"⚠️  Index not ready for queries yet. It will be available shortly.")
        
        print("\n" + "=" * 80)
        print("✅ Vector Search Index Created Successfully!")
        print("=" * 80)
        print(f"\n📊 Index Details:")
        print(f"   Endpoint: {endpoint_name}")
        print(f"   Index: {index_name}")
        print(f"   Status: Created (may take a few minutes to be fully ready)")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Make sure:")
        print("   1. PDF chunks exist in battery_documents table")
        print("   2. You have permissions on the catalog and endpoint")
        print("   3. The endpoint 'one-env-shared-endpoint-10' exists and is accessible")
        return False

if __name__ == "__main__":
    success = create_vector_index()
    exit(0 if success else 1)

