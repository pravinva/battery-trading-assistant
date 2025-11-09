"""
Base Agent Class for Multi-Agent Supervisor Pattern

This module provides a base class for specialized agents in the Multi-Agent Supervisor architecture.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseAgent(ABC):
    """Base class for specialized agents in the Multi-Agent Supervisor pattern"""
    
    def __init__(self, name: str, description: str):
        """
        Initialize base agent
        
        Args:
            name: Agent name (e.g., "data_agent", "docs_agent")
            description: Agent description for routing decisions
        """
        self.name = name
        self.description = description
    
    @abstractmethod
    def can_handle(self, question: str) -> bool:
        """
        Determine if this agent can handle the given question
        
        Args:
            question: User question
            
        Returns:
            True if agent can handle, False otherwise
        """
        pass
    
    @abstractmethod
    def process(self, question: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Process the question and return response
        
        Args:
            question: User question
            context: Optional context from previous interactions
            
        Returns:
            Agent response
        """
        pass
    
    def get_description(self) -> str:
        """Get agent description for routing"""
        return self.description

