"""
Data Agent - Specialized agent for SQL queries and data analysis

This agent handles all data-related queries using Genie (MCP/Direct API).
"""

from .base_agent import BaseAgent
from typing import Dict, Any, Optional
import re


class DataAgent(BaseAgent):
    """Specialized agent for data queries via Genie"""
    
    def __init__(self, genie_room_id: str):
        """
        Initialize Data Agent
        
        Args:
            genie_room_id: Genie space ID for SQL queries
        """
        super().__init__(
            name="data_agent",
            description="Handles all SQL queries, data analysis, and chart generation via Genie"
        )
        self.genie_room_id = genie_room_id
    
    def can_handle(self, question: str) -> bool:
        """
        Determine if this is a data query
        
        Data queries typically:
        - Ask for specific values (SoC, revenue, throughput)
        - Request comparisons or aggregations
        - Need SQL execution
        - Ask "what", "show", "compare", "calculate"
        """
        data_keywords = [
            'soc', 'revenue', 'throughput', 'dispatch', 'charge', 'discharge',
            'compare', 'show', 'what', 'calculate', 'total', 'average', 'sum',
            'current', 'last', 'hour', 'day', 'week', 'month',
            'battery', 'batteries', 'plot', 'chart', 'graph'
        ]
        
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in data_keywords)
    
    def process(self, question: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Process data query using Genie
        
        Args:
            question: User question
            context: Optional context
            
        Returns:
            Response from Genie
        """
        # TODO: Implement using Genie integration
        # This will use the existing query_genie functionality
        # from scripts/02_agent_development_local.py
        
        return f"[Data Agent] Would process: {question}"

