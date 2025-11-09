# Multi-Agent Supervisor Implementation
# 
# This package contains specialized agents for the Multi-Agent Supervisor pattern.
#
# Structure:
# - base_agent.py: Base class for all agents
# - supervisor.py: Supervisor agent that routes queries
# - data_agent.py: Data/Genie agent
# - docs_agent.py: Documentation/Vector Search agent
#
# See docs/MULTI_AGENT_SUPERVISOR_PLAN.md for architecture details.

from .base_agent import BaseAgent
from .supervisor import SupervisorAgent
from .data_agent import DataAgent
from .docs_agent import DocsAgent

__all__ = ['BaseAgent', 'SupervisorAgent', 'DataAgent', 'DocsAgent']
