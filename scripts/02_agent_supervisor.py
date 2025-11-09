#!/usr/bin/env python3
"""
Battery Trading Agent - Multi-Agent Supervisor Implementation

This is the future architecture using Multi-Agent Supervisor pattern.
It will coexist with the current single-agent implementation for gradual migration.

Architecture:
- Supervisor Agent: Routes queries to specialized agents
- Data Agent: Handles SQL queries via Genie
- Docs Agent: Handles documentation queries via Vector Search
- Future: Analytics Agent, Alert Agent, etc.
"""

import warnings
import os

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
os.environ["PYTHONWARNINGS"] = "ignore"

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from agents.supervisor import SupervisorAgent
from agents.data_agent import DataAgent
from agents.docs_agent import DocsAgent

# Configuration
CATALOG = "ea_trading"
SCHEMA = "battery_trading"
ENDPOINT_NAME = "one-env-shared-endpoint-10"
INDEX_NAME = f"{CATALOG}.{SCHEMA}.battery_docs_index"
LLM_ENDPOINT = "databricks-claude-sonnet-4-5"

# Genie Configuration
GENIE_ROOM_ID = os.environ.get("GENIE_ROOM_ID", "01f0bca10415147a91fe3c98f80e596e")

# Set USE_GENIE_MCP environment variable before initializing agents
# This ensures agents use the correct Genie integration method
USE_GENIE_MCP = os.environ.get("USE_GENIE_MCP", "false").lower() == "true"

print("=" * 80)
print("Multi-Agent Supervisor Implementation")
print("=" * 80)
print()

# Show Genie integration method
if USE_GENIE_MCP:
    print("🔌 Genie Integration: MCP Server")
else:
    print("🔌 Genie Integration: Direct API")
print()

# Initialize specialized agents
print("🔧 Initializing specialized agents...")
data_agent = DataAgent(genie_room_id=GENIE_ROOM_ID)
docs_agent = DocsAgent(index_name=INDEX_NAME, endpoint_name=ENDPOINT_NAME)
print("✅ Data Agent initialized")
print("✅ Docs Agent initialized")

# Initialize supervisor
print("\n🔧 Initializing Supervisor Agent...")
supervisor = SupervisorAgent(data_agent=data_agent, docs_agent=docs_agent)
print("✅ Supervisor Agent initialized")

print("\n" + "=" * 80)
print("Multi-Agent Supervisor Ready!")
print("=" * 80)
print()
print("Agents available:")
print(f"  - {data_agent.name}: {data_agent.description}")
print(f"  - {docs_agent.name}: {docs_agent.description}")
print(f"  - {supervisor.name}: {supervisor.description}")
print()
print("Usage:")
print("  response = supervisor.process('What is the current SoC for RESS2?')")
print("  logs = supervisor.get_logs()")
print("=" * 80)

# Export for use in other modules
__all__ = ['supervisor', 'data_agent', 'docs_agent', 'SupervisorAgent', 'DataAgent', 'DocsAgent']


