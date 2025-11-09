"""
Data Agent - Specialized agent for SQL queries and data analysis

This agent handles all data-related queries using Genie (MCP/Direct API).
"""

from .base_agent import BaseAgent
from typing import Dict, Any, Optional
import re
import sys
from pathlib import Path

# Import Genie query functions from existing implementation
# We'll import the actual functions from the agent script
_agent_module = None


def _get_genie_query_function():
    """Lazy import of query_genie function from existing implementation"""
    global _agent_module
    if _agent_module is None:
        # Import the agent module dynamically with error handling
        agent_script_path = Path(__file__).parent.parent / "scripts" / "02_agent_development_local.py"
        if agent_script_path.exists():
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("agent_module", agent_script_path)
                _agent_module = importlib.util.module_from_spec(spec)
                # Suppress print statements during import to avoid noise
                import sys
                import io
                old_stdout = sys.stdout
                sys.stdout = io.StringIO()
                try:
                    spec.loader.exec_module(_agent_module)
                finally:
                    sys.stdout = old_stdout
            except Exception as e:
                # If import fails, set to a sentinel value to avoid retrying
                _agent_module = False
                print(f"⚠️  Warning: Could not import agent module: {e}")
    return _agent_module if _agent_module is not False else None


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
        self._genie_module = None
    
    def _get_query_genie_func(self):
        """Get the query_genie function from existing implementation"""
        if self._genie_module is None:
            agent_module = _get_genie_query_function()
            if agent_module:
                # Prefer direct API functions over tool wrapper
                # Check for direct API function first (more reliable)
                if hasattr(agent_module, 'query_genie_via_direct_api'):
                    # Use direct API function - it takes (question, is_visualization_request)
                    def wrapper(question: str, is_viz: bool = False) -> str:
                        return agent_module.query_genie_via_direct_api(question, is_viz)
                    self._genie_module = wrapper
                elif hasattr(agent_module, 'query_genie_via_mcp'):
                    # Use MCP function
                    def wrapper(question: str, is_viz: bool = False) -> str:
                        return agent_module.query_genie_via_mcp(question, is_viz)
                    self._genie_module = wrapper
                elif hasattr(agent_module, 'query_genie'):
                    # Fallback to tool wrapper
                    query_genie_tool = agent_module.query_genie
                    if hasattr(query_genie_tool, 'invoke'):
                        def wrapper(question: str) -> str:
                            result = query_genie_tool.invoke({"question": question})
                            return result if isinstance(result, str) else str(result)
                        self._genie_module = wrapper
                    else:
                        self._genie_module = query_genie_tool
        return self._genie_module
    
    def can_handle(self, question: str) -> bool:
        """
        Determine if this is a data query
        
        Data queries typically:
        - Ask for specific values (SoC, revenue, throughput)
        - Request comparisons or aggregations
        - Need SQL execution
        - Ask "what", "show", "compare", "calculate"
        """
        question_lower = question.lower()
        
        # Strong data indicators (must have at least one)
        strong_data_keywords = [
            'soc', 'revenue', 'throughput', 'dispatch', 'charge', 'discharge',
            'compare', 'show', 'calculate', 'total', 'average', 'sum',
            'current', 'last', 'hour', 'day', 'week', 'month',
            'battery', 'batteries', 'plot', 'chart', 'graph'
        ]
        
        # Weak data indicators (not enough on their own)
        weak_data_keywords = ['what']
        
        # Check for strong indicators
        has_strong_data = any(keyword in question_lower for keyword in strong_data_keywords)
        
        # Check for weak indicators (only count if combined with strong or specific patterns)
        has_weak_data = any(keyword in question_lower for keyword in weak_data_keywords)
        
        # Data query if has strong indicators OR (weak indicator + data context)
        if has_strong_data:
            return True
        
        # If only weak indicator, check for data context
        if has_weak_data:
            # Check if "what" is followed by data-related terms
            data_context = ['is the', 'are the', 'was', 'were', 'value', 'number', 'amount']
            return any(context in question_lower for context in data_context)
        
        return False
    
    def process(self, question: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Process data query using Genie
        
        Args:
            question: User question
            context: Optional context
            
        Returns:
            Response from Genie
        """
        try:
            query_func = self._get_query_genie_func()
            if query_func:
                # Detect visualization request
                explicit_viz_keywords = ['plot', 'chart', 'graph', 'visualize', 'visualization', 'show me a', 'display a', 'create a']
                is_visualization_request = any(keyword in question.lower() for keyword in explicit_viz_keywords)
                
                # Call the Genie query function
                if hasattr(query_func, '__call__'):
                    # Check function signature to determine how to call it
                    import inspect
                    try:
                        sig = inspect.signature(query_func)
                        # If it accepts is_visualization_request parameter, pass it
                        if 'is_visualization_request' in sig.parameters or len(sig.parameters) == 2:
                            result = query_func(question, is_visualization_request)
                        else:
                            # Tool wrapper or function that only takes question
                            result = query_func(question)
                        return result
                    except Exception as sig_error:
                        # If signature inspection fails, try both approaches
                        try:
                            result = query_func(question, is_visualization_request)
                            return result
                        except TypeError:
                            result = query_func(question)
                            return result
                else:
                    return f"[Data Agent Error] Could not call Genie function"
            else:
                return f"[Data Agent Error] Genie integration not available. Please ensure scripts/02_agent_development_local.py exists."
        except Exception as e:
            return f"[Data Agent Error] Failed to process query: {str(e)}"

