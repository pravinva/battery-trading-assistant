#!/usr/bin/env python3
"""
Run PDF Processing directly via Databricks API (no job)
Usage: python3 run_pdf_direct.py
"""

from databricks.sdk import WorkspaceClient
from databricks.vector_search.client import VectorSearchClient
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import pandas as pd
from datetime import datetime

def process_pdf_direct():
    """Process PDF and create Vector Search index directly"""
    w = WorkspaceClient()
    
    # Configuration
    catalog = "ea_trading"
    schema = "battery_trading"
    endpoint_name = "one-env-shared-endpoint-10"
    pdf_volume_path = f"/Volumes/{catalog}/{schema}/pdfs/battery.pdf"
    
    print("=" * 80)
    print("PDF Processing and Vector Search Index Creation")
    print("=" * 80)
    
    # Note: This requires Spark context which is only available in Databricks runtime
    # For CLI execution, we need to use SQL execution API or workspace API
    
    print("\n⚠️  Note: PDF processing requires Databricks runtime with Spark.")
    print("   This script needs to run in a Databricks notebook or cluster.")
    print("\n💡 Options:")
    print("   1. Run notebook directly in Databricks workspace UI")
    print("   2. Use databricks-connect (if configured)")
    print("   3. Execute via workspace API (requires notebook execution)")
    
    print(f"\n📋 To run manually:")
    print(f"   1. Open: /Users/pravin.varma@databricks.com/battery-trading/process_pdf_index")
    print(f"   2. Attach to cluster with Unity Catalog enabled")
    print(f"   3. Run all cells")
    
    return False

if __name__ == "__main__":
    process_pdf_direct()

