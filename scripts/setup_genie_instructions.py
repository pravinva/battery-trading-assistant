#!/usr/bin/env python3
"""
Generate and optionally update Genie space instructions
"""

from databricks.sdk import WorkspaceClient
import os

GENIE_SPACE_ID = os.environ.get("GENIE_ROOM_ID", "01f0bca10415147a91fe3c98f80e596e")

GENIE_INSTRUCTIONS = """You are an expert battery trading assistant for Energy Australia.

You help traders and operators by:
1. Providing real-time battery status (SoC, capabilities, telemetry)
2. Analyzing dispatch performance and revenue
3. Explaining technical specifications and processes from documentation
4. Answering questions about Wartsila BESS integration, AEMO bidding, and operational limits

Important context:
- RESS2 and DPNTBESS are at Darlington Point (Riverina)
- GANNBG1 and GANNBL1 are at Wooreen (Jeeralang) - new Wartsila site
- SoC readings older than 10 minutes may trigger availability restrictions
- Throughput limits over 7.5 hour windows affect bidding

Available tables:
- battery_telemetry: Current SoC, capabilities, and telemetry readings
- battery_dispatch: Dispatch history, revenue, and trading intervals
- battery_assets: Asset specifications, capacity, location, partner details
- battery_documents: Document metadata (technical documentation is in Vector Search)

When answering:
- Always use specific data from tables
- Cite sources (e.g., "According to telemetry..." or "From dispatch data...")
- For operational questions, query live data from telemetry and dispatch tables
- Format numbers appropriately (SoC as %, revenue as currency, capacity as MW/MWh)
- Be precise with battery IDs: RESS2, DPNTBESS, GANNBG1, GANNBL1
- Consider time windows when analyzing performance (last 24 hours, last hour, etc.)"""

def check_genie_space():
    """Check Genie space and display current instructions"""
    w = WorkspaceClient()
    genie = w.genie
    
    print(f"🔍 Checking Genie space: {GENIE_SPACE_ID}")
    
    try:
        space = genie.get_space(space_id=GENIE_SPACE_ID)
        print(f"✅ Found space: {getattr(space, 'title', 'Unknown')}")
        print(f"   Description: {getattr(space, 'description', 'None')}")
        print(f"   Warehouse ID: {getattr(space, 'warehouse_id', 'Unknown')}")
        
        # Check if we can update instructions via API
        print("\n📝 Instructions Configuration:")
        print("   Genie space instructions must be configured via UI:")
        print("   1. Go to Genie > Battery Trading Agent > Configure")
        print("   2. Go to 'Instructions' tab")
        print("   3. Paste the instructions from GENIE_INSTRUCTIONS.md")
        print("   4. Click 'Save'")
        
        print("\n📄 Instructions to add:")
        print("=" * 80)
        print(GENIE_INSTRUCTIONS)
        print("=" * 80)
        
        # Check if API supports updating instructions
        if hasattr(genie, 'update_space'):
            print("\n✅ API supports updating space - checking parameters...")
            # Would need to check what parameters update_space accepts
        else:
            print("\n⚠️  Instructions must be updated via UI (no API method available)")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_genie_space()
    
    print("\n" + "=" * 80)
    print("📋 Next Steps:")
    print("=" * 80)
    print("1. Open GENIE_INSTRUCTIONS.md for full instructions")
    print("2. Go to Databricks UI > Genie > Battery Trading Agent > Configure")
    print("3. Add instructions in the 'Instructions' tab")
    print("4. (Optional) Add SQL Expressions and Example Queries")
    print("5. Save the configuration")

