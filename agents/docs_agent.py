"""
Docs Agent - Specialized agent for documentation queries

This agent handles all documentation-related queries using Vector Search.
"""

from .base_agent import BaseAgent
from typing import Dict, Any, Optional
import re


class DocsAgent(BaseAgent):
    """Specialized agent for documentation queries via Vector Search"""
    
    def __init__(self, index_name: str):
        """
        Initialize Docs Agent
        
        Args:
            index_name: Vector Search index name
        """
        super().__init__(
            name="docs_agent",
            description="Searches technical documentation and explains processes via Vector Search"
        )
        self.index_name = index_name
    
    def can_handle(self, question: str) -> bool:
        """
        Determine if this is a documentation query
        
        Documentation queries typically:
        - Ask "how", "why", "explain"
        - Request technical information
        - Need process explanations
        - Ask about concepts, limits, specifications
        """
        docs_keywords = [
            'how', 'why', 'explain', 'what is', 'what are',
            'process', 'method', 'calculation', 'formula',
            'limit', 'threshold', 'specification', 'requirement',
            'documentation', 'document', 'guide', 'manual'
        ]
        
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in docs_keywords)
    
    def process(self, question: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Process documentation query using Vector Search
        
        Args:
            question: User question
            context: Optional context
            
        Returns:
            Response from Vector Search
        """
        # TODO: Implement using Vector Search integration
        # This will use the existing search_battery_docs functionality
        # from scripts/02_agent_development_local.py
        
        return f"[Docs Agent] Would process: {question}"

