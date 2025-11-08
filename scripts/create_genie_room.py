#!/usr/bin/env python3
"""
Create a Databricks Genie room for battery trading agent
"""

from databricks.sdk import WorkspaceClient
import json

def create_genie_room():
    """Create a Genie room called 'battery-trading-agent'"""
    
    w = WorkspaceClient()
    
    print("🔍 Checking Genie API availability...")
    
    if not hasattr(w, 'genie'):
        print("❌ Genie API not available in SDK")
        return None
    
    genie = w.genie
    
    # Check available methods
    print(f"✅ Genie API found")
    print(f"Available methods: {[m for m in dir(genie) if not m.startswith('_')]}")
    
    # Try to list existing spaces
    try:
        print("\n📋 Listing existing Genie spaces...")
        spaces_response = genie.list_spaces()
        # Check the response structure
        if hasattr(spaces_response, 'spaces'):
            spaces = spaces_response.spaces
        elif hasattr(spaces_response, 'items'):
            spaces = spaces_response.items
        else:
            # Try to access directly
            spaces = spaces_response
        
        if spaces:
            print(f"Found {len(spaces)} existing spaces:")
            for space in spaces:
                space_name = getattr(space, 'title', getattr(space, 'name', 'Unknown'))
                space_id = getattr(space, 'space_id', getattr(space, 'id', 'Unknown'))
                print(f"  - {space_name} (ID: {space_id})")
                
                # Check if our target space exists (case-insensitive, handle variations)
                target_names = ["battery-trading-agent", "battery trading agent", "Battery Trading Agent"]
                if space_name.lower().replace("-", " ").strip() in [n.lower().replace("-", " ").strip() for n in target_names]:
                    print(f"\n✅ Found existing space '{space_name}'!")
                    print(f"   Space ID: {space_id}")
                    return space_id
        else:
            print("No existing spaces found")
    except Exception as e:
        print(f"⚠️  Could not list spaces: {e}")
        import traceback
        traceback.print_exc()
    
    # Genie spaces cannot be created programmatically - must use UI
    print("\n⚠️  Genie spaces cannot be created via API")
    print("   They must be created manually through the Databricks UI")
    print("\n📝 To create 'battery-trading-agent' space:")
    print("   1. Go to your Databricks workspace")
    print("   2. Click on 'Genie' in the sidebar")
    print("   3. Click 'New' button (upper-right)")
    print(f"   4. Name it: 'battery-trading-agent'")
    print(f"   5. Select catalog: {CATALOG}")
    print(f"   6. Select schema: {SCHEMA}")
    print("   7. Select tables:")
    print(f"      - {CATALOG}.{SCHEMA}.battery_telemetry")
    print(f"      - {CATALOG}.{SCHEMA}.battery_dispatch")
    print(f"      - {CATALOG}.{SCHEMA}.battery_assets")
    print(f"      - {CATALOG}.{SCHEMA}.battery_documents")
    print("   8. Click 'Create'")
    print("\n   After creating, run this script again to get the space ID")
    return None

if __name__ == "__main__":
    # Configuration
    CATALOG = "ea_trading"
    SCHEMA = "battery_trading"
    
    room_id = create_genie_room()
    
    if room_id:
        print(f"\n✅ Success! Found Genie space!")
        print(f"   Space ID: {room_id}")
        print(f"\n📝 Set this environment variable:")
        print(f"   export GENIE_ROOM_ID=\"{room_id}\"")
        print(f"\n   Or add to your shell profile (~/.zshrc or ~/.bashrc):")
        print(f"   echo 'export GENIE_ROOM_ID=\"{room_id}\"' >> ~/.zshrc")
        print(f"\n   Then restart your terminal or run:")
        print(f"   source ~/.zshrc")
    else:
        print("\n⚠️  Could not find 'battery-trading-agent' space")
        print("   Please create it manually and run this script again")

