"""
Docs Agent - Specialized agent for documentation queries

This agent handles all documentation-related queries using Vector Search.
"""

from .base_agent import BaseAgent
from typing import Dict, Any, Optional
import re
import sys
from pathlib import Path

# Import Vector Search function from existing implementation
_agent_module = None


def _get_vector_search_function():
    """Lazy import of search_battery_docs function from existing implementation"""
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


class DocsAgent(BaseAgent):
    """Specialized agent for documentation queries via Vector Search"""
    
    def __init__(self, index_name: str, endpoint_name: str):
        """
        Initialize Docs Agent
        
        Args:
            index_name: Vector Search index name
            endpoint_name: Vector Search endpoint name
        """
        super().__init__(
            name="docs_agent",
            description="Searches technical documentation and explains processes via Vector Search"
        )
        self.index_name = index_name
        self.endpoint_name = endpoint_name
        self._vector_search_func = None
    
    def _get_search_func(self):
        """Get the search_battery_docs function from existing implementation"""
        if self._vector_search_func is None:
            agent_module = _get_vector_search_function()
            if agent_module and hasattr(agent_module, 'search_battery_docs'):
                # Get the underlying function from the tool
                search_tool = agent_module.search_battery_docs
                if hasattr(search_tool, 'func'):
                    self._vector_search_func = search_tool.func
                elif hasattr(search_tool, 'invoke'):
                    def wrapper(query: str) -> str:
                        result = search_tool.invoke({"query": query})
                        return result if isinstance(result, str) else str(result)
                    self._vector_search_func = wrapper
                else:
                    self._vector_search_func = search_tool
            else:
                # Fallback: use Vector Search client directly
                try:
                    from databricks.vector_search.client import VectorSearchClient
                    vsc = VectorSearchClient(disable_notice=True)
                    
                    def direct_search(query: str) -> str:
                        index = vsc.get_index(endpoint_name=self.endpoint_name, index_name=self.index_name)
                        results = index.similarity_search(
                            query_text=query,
                            columns=["content", "doc_title", "page_number"],
                            num_results=3
                        )
                        context_parts = []
                        for hit in results.get('result', {}).get('data_array', []):
                            content, title, page = hit[0], hit[1], hit[2]
                            context_parts.append(f"[Page {page}] {content}")
                        return "\n\n".join(context_parts) if context_parts else "No relevant documentation found."
                    
                    self._vector_search_func = direct_search
                except Exception as e:
                    self._vector_search_func = None
        return self._vector_search_func
    
    def can_handle(self, question: str) -> bool:
        """
        Determine if this is a documentation query
        
        Documentation queries typically:
        - Ask "how", "why", "explain"
        - Request technical information
        - Need process explanations
        - Ask about concepts, limits, specifications
        """
        question_lower = question.lower()
        
        # Strong docs indicators
        strong_docs_keywords = [
            'how', 'why', 'explain', 'process', 'method', 'calculation', 'formula',
            'limit', 'threshold', 'specification', 'requirement',
            'documentation', 'document', 'guide', 'manual'
        ]
        
        # Weak docs indicators
        weak_docs_keywords = ['what is', 'what are']
        
        # Check for strong indicators
        has_strong_docs = any(keyword in question_lower for keyword in strong_docs_keywords)
        
        # Check for weak indicators (conceptual questions)
        has_weak_docs = any(keyword in question_lower for keyword in weak_docs_keywords)
        
        # Docs query if has strong indicators OR (weak indicator + conceptual context)
        if has_strong_docs:
            return True
        
        # If only weak indicator, check for conceptual context
        if has_weak_docs:
            # Check if "what is/are" is followed by conceptual terms
            conceptual_context = ['the', 'a', 'an', 'process', 'method', 'concept', 'definition']
            # Make sure it's not a data query
            data_indicators = ['soc', 'revenue', 'throughput', 'current', 'value', 'number']
            has_data_context = any(indicator in question_lower for indicator in data_indicators)
            return not has_data_context
        
        return False
    
    def process(self, question: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Process documentation query using Vector Search
        
        Args:
            question: User question
            context: Optional context
            
        Returns:
            Response from Vector Search
        """
        try:
            search_func = self._get_search_func()
            if search_func:
                result = search_func(question)
                return result
            else:
                return f"[Docs Agent Error] Vector Search integration not available. Please ensure scripts/02_agent_development_local.py exists and Vector Search is configured."
        except Exception as e:
            return f"[Docs Agent Error] Failed to process query: {str(e)}"

