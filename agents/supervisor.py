"""
Multi-Agent Supervisor Implementation

This module implements the Multi-Agent Supervisor pattern.
Currently uses custom routing logic, will migrate to databricks-ai-bridge when API is available.
"""

from .base_agent import BaseAgent
from .data_agent import DataAgent
from .docs_agent import DocsAgent
from typing import Dict, Any, Optional, List
import concurrent.futures
import threading


class SupervisorAgent(BaseAgent):
    """Supervisor agent that routes queries to specialized sub-agents"""
    
    def __init__(self, data_agent: DataAgent, docs_agent: DocsAgent):
        """
        Initialize Supervisor Agent
        
        Args:
            data_agent: Data agent for SQL queries
            docs_agent: Docs agent for documentation queries
        """
        super().__init__(
            name="supervisor",
            description="Routes queries to specialized agents and synthesizes responses"
        )
        self.data_agent = data_agent
        self.docs_agent = docs_agent
        self._execution_logs = []
    
    def _log(self, message: str):
        """Log execution steps"""
        import time
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        self._execution_logs.append(f"[{timestamp}] {message}")
    
    def get_logs(self) -> List[str]:
        """Get and clear execution logs"""
        logs = self._execution_logs.copy()
        self._execution_logs = []
        return logs
    
    def can_handle(self, question: str) -> bool:
        """Supervisor can handle any question by routing to sub-agents"""
        return True
    
    def _is_hybrid_query(self, question: str) -> bool:
        """Determine if query needs both agents"""
        question_lower = question.lower()
        
        # Check if it has both data and docs keywords
        data_keywords = ['soc', 'revenue', 'throughput', 'compare', 'show', 'what', 'current']
        docs_keywords = ['how', 'why', 'explain', 'process', 'method', 'limit']
        
        has_data = any(keyword in question_lower for keyword in data_keywords)
        has_docs = any(keyword in question_lower for keyword in docs_keywords)
        
        # Also check for connectors that suggest hybrid queries
        connectors = ['and', 'also', 'plus', 'including']
        has_connector = any(connector in question_lower for connector in connectors)
        
        return (has_data and has_docs) or (has_data and has_connector) or (has_docs and has_connector)
    
    def process(self, question: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Process question by routing to appropriate agent(s)
        
        Args:
            question: User question
            context: Optional context
            
        Returns:
            Synthesized response from agent(s)
        """
        self._log(f"📥 Received question: {question}")
        
        # Determine routing
        is_hybrid = self._is_hybrid_query(question)
        data_can_handle = self.data_agent.can_handle(question)
        docs_can_handle = self.docs_agent.can_handle(question)
        
        self._log(f"🔍 Routing analysis: hybrid={is_hybrid}, data={data_can_handle}, docs={docs_can_handle}")
        
        # Route to appropriate agent(s)
        if is_hybrid or (data_can_handle and docs_can_handle):
            # Use both agents in parallel
            self._log("🔄 Routing to both agents (parallel execution)")
            return self._process_hybrid(question, context)
        elif data_can_handle:
            # Route to data agent
            self._log("📊 Routing to Data Agent")
            result = self.data_agent.process(question, context)
            self._log("✅ Data Agent completed")
            return result
        elif docs_can_handle:
            # Route to docs agent
            self._log("📚 Routing to Docs Agent")
            result = self.docs_agent.process(question, context)
            self._log("✅ Docs Agent completed")
            return result
        else:
            # Try data agent as default (most queries are data-related)
            self._log("⚠️  No clear match, defaulting to Data Agent")
            result = self.data_agent.process(question, context)
            if "[Data Agent Error]" in result:
                # Fallback to docs agent
                self._log("⚠️  Data Agent failed, trying Docs Agent")
                result = self.docs_agent.process(question, context)
            return result
    
    def _process_hybrid(self, question: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Process hybrid query using both agents in parallel
        
        Args:
            question: User question
            context: Optional context
            
        Returns:
            Synthesized response from both agents
        """
        # Split question into data and docs parts if possible
        # For now, send full question to both agents
        # Future: Use LLM to decompose question
        
        self._log("🔄 Executing both agents in parallel...")
        
        # Execute both agents in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            data_future = executor.submit(self.data_agent.process, question, context)
            docs_future = executor.submit(self.docs_agent.process, question, context)
            
            # Wait for both to complete
            data_result = data_future.result()
            docs_result = docs_future.result()
        
        self._log("✅ Both agents completed")
        
        # Synthesize results
        response_parts = []
        
        # Add data result if valid
        if data_result and "[Data Agent Error]" not in data_result:
            response_parts.append(f"**Data Analysis:**\n{data_result}")
        
        # Add docs result if valid
        if docs_result and "[Docs Agent Error]" not in docs_result:
            response_parts.append(f"\n**Documentation:**\n{docs_result}")
        
        # Handle errors
        if not response_parts:
            if "[Data Agent Error]" in data_result:
                return f"{data_result}\n\nTried Docs Agent: {docs_result}"
            elif "[Docs Agent Error]" in docs_result:
                return f"{docs_result}\n\nTried Data Agent: {data_result}"
            else:
                return f"Both agents returned empty results.\nData: {data_result}\nDocs: {docs_result}"
        
        # Combine results
        synthesized = "\n\n---\n\n".join(response_parts)
        synthesized += "\n\n---\n*This response combines data analysis and documentation.*"
        
        return synthesized


