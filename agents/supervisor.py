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
import re


class SupervisorAgent(BaseAgent):
    """Supervisor agent that routes queries to specialized sub-agents"""
    
    def __init__(self, data_agent: DataAgent, docs_agent: DocsAgent, llm_endpoint: str = "databricks-claude-sonnet-4-5"):
        """
        Initialize Supervisor Agent
        
        Args:
            data_agent: Data agent for SQL queries
            docs_agent: Docs agent for documentation queries
            llm_endpoint: LLM endpoint for synthesis (optional, defaults to same as Single Agent)
        """
        super().__init__(
            name="supervisor",
            description="Routes queries to specialized agents and synthesizes responses"
        )
        self.data_agent = data_agent
        self.docs_agent = docs_agent
        self.llm_endpoint = llm_endpoint
        self._execution_logs = []
        self._llm = None
    
    def _get_llm(self):
        """Lazy load LLM for synthesis"""
        if self._llm is None:
            try:
                try:
                    from databricks_langchain import ChatDatabricks
                except ImportError:
                    from langchain_community.chat_models import ChatDatabricks
                self._llm = ChatDatabricks(endpoint=self.llm_endpoint, temperature=0.1)
            except Exception as e:
                # If LLM fails to load, that's okay - we'll fallback to concatenation
                self._llm = False
                self._log(f"⚠️  LLM not available for synthesis: {e}")
        return self._llm if self._llm is not False else None
    
    def _clean_raw_output(self, raw_output: str, output_type: str = "data") -> str:
        """
        Clean raw output by removing debug info and formatting
        
        Args:
            raw_output: Raw output from agent
            output_type: "data" or "docs"
            
        Returns:
            Cleaned output
        """
        if not raw_output:
            return ""
        
        cleaned = raw_output
        
        # Remove DEBUG INFO sections
        cleaned = re.sub(r'DEBUG INFO.*?```.*?```', '', cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'DEBUG:.*?\n', '', cleaned)
        
        # Remove raw query results markers if they're just debug
        if output_type == "data":
            # Keep SQL queries but remove excessive debug
            cleaned = re.sub(r'DEBUG: Question:.*?\n', '', cleaned)
            cleaned = re.sub(r'DEBUG: Message ID:.*?\n', '', cleaned)
            cleaned = re.sub(r'DEBUG: Conversation ID:.*?\n', '', cleaned)
            cleaned = re.sub(r'DEBUG: Genie Response \(raw\):.*?\n', '', cleaned)
            cleaned = re.sub(r'DEBUG: SQL Query:.*?\n', '', cleaned)
            cleaned = re.sub(r'DEBUG: Query Data:.*?\n', '', cleaned)
            
            # Remove raw JSON responses (will be synthesized instead)
            # Try to extract meaningful data from JSON if present
            if cleaned.strip().startswith('{') and '"query"' in cleaned:
                # Try to extract SQL query and results from JSON
                import json as json_module
                try:
                    json_data = json_module.loads(cleaned)
                    sql_query = json_data.get('query', '')
                    if 'statement_response' in json_data and 'result' in json_data['statement_response']:
                        result_data = json_data['statement_response']['result']
                        if 'data_array' in result_data:
                            # Extract readable data
                            rows = []
                            for row in result_data['data_array']:
                                if 'values' in row:
                                    values = [v.get('string_value', v.get('double_value', v.get('int_value', ''))) for v in row['values']]
                                    rows.append(values)
                            if rows:
                                # Format as readable text
                                formatted_results = "Query Results:\n"
                                for row in rows:
                                    formatted_results += f"{', '.join(str(v) for v in row)}\n"
                                if sql_query:
                                    cleaned = f"SQL Query: {sql_query}\n\n{formatted_results}"
                                else:
                                    cleaned = formatted_results
                except Exception:
                    # If JSON parsing fails, keep original but mark for synthesis
                    pass
            
            # Remove excessive "Raw Query Results" if it's just arrays
            # But keep formatted SQL queries
            if '```sql' in cleaned:
                # Keep SQL blocks
                pass
            else:
                # Remove raw array outputs like ['RESS 2', '62.0', '82.7']
                cleaned = re.sub(r'Raw Query Results:.*?\[.*?\]', '', cleaned, flags=re.DOTALL)
        
        # Clean up multiple newlines
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
        return cleaned.strip()
    
    def _synthesize_single_agent_response(self, question: str, raw_result: str, agent_type: str) -> Optional[str]:
        """
        Synthesize single-agent response if it contains raw data/JSON
        
        Args:
            question: Original user question
            raw_result: Raw output from agent
            agent_type: "data" or "docs"
            
        Returns:
            Synthesized response or None if synthesis not needed/fails
        """
        # Check if result contains raw JSON or needs synthesis
        needs_synthesis = False
        
        if agent_type == "data":
            # Check for raw JSON responses (even if prefixed with headers)
            if '"query"' in raw_result and ('{"query"' in raw_result or '"statement_response"' in raw_result):
                needs_synthesis = True
            # Check for responses that start with Genie headers followed by JSON
            elif raw_result.count('🤖') > 0 and ('{"query"' in raw_result or 'statement_response' in raw_result):
                needs_synthesis = True
            # Check for raw data arrays or excessive technical details
            elif '["' in raw_result and '"]' in raw_result and raw_result.count('[') > 3:
                needs_synthesis = True
        
        if not needs_synthesis:
            return None
        
        llm = self._get_llm()
        if not llm:
            return None
        
        try:
            # Clean input
            cleaned_result = self._clean_raw_output(raw_result, agent_type)
            
            # Check for chart markers
            chart_markers = ""
            if "[PLOTLY_CHART_START]" in raw_result and "[PLOTLY_CHART_END]" in raw_result:
                import re as re_module
                chart_match = re_module.search(r'\[PLOTLY_CHART_START\].*?\[PLOTLY_CHART_END\]', raw_result, re_module.DOTALL)
                if chart_match:
                    chart_markers = chart_match.group(0)
                    cleaned_result = re_module.sub(r'\[PLOTLY_CHART_START\].*?\[PLOTLY_CHART_END\]', '', cleaned_result, flags=re_module.DOTALL)
            
            # Build synthesis prompt
            source_label = "Data Analysis (from SQL queries via Databricks Genie)" if agent_type == "data" else "Documentation (from technical documentation)"
            
            # Check if user requested visualization
            viz_keywords = ['plot', 'chart', 'graph', 'visualize', 'visualization', 'show me a', 'display a', 'create a']
            is_viz_request = any(keyword in question.lower() for keyword in viz_keywords)
            
            synthesis_prompt = f"""You are a helpful assistant that formats technical data into clear, readable answers.

User Question: {question}

{source_label}:
{cleaned_result}

Please convert this technical response into a clear, natural answer that:
1. Directly answers the user's question in a conversational way
2. Extracts and presents the key information (numbers, values, facts) clearly
3. Uses proper formatting with spaces around numbers and currency (e.g., "$100 revenue", not "$100revenue")
4. Maintains a professional, expert tone appropriate for Energy Australia operations
5. Removes technical details like SQL queries, JSON structures, and debug information
6. Presents data in a readable format (e.g., "RESS2 has a SoC of 82.7%" instead of raw arrays)
{"7. IMPORTANT: The user requested a visualization/chart. A chart has been generated and will be displayed below your response. Do NOT say you cannot create charts or visualizations - the chart is already created and will appear." if is_viz_request and chart_markers else ""}

Do not include:
- Raw JSON structures
- SQL queries (unless the user specifically asked to see the SQL)
- Technical implementation details
- Debug information
{"- Statements saying you cannot create charts or visualizations (the chart is already generated)" if is_viz_request and chart_markers else ""}

Provide a clean, readable answer:"""
            
            self._log(f"🤖 Synthesizing {agent_type} agent response with LLM...")
            
            # Call LLM
            response = llm.invoke(synthesis_prompt)
            
            # Extract content
            if hasattr(response, 'content'):
                synthesized = response.content
            elif isinstance(response, str):
                synthesized = response
            else:
                synthesized = str(response)
            
            self._log("✅ LLM synthesis completed")
            
            # Append chart markers if present
            synthesized = synthesized.strip()
            if chart_markers:
                synthesized += f"\n\n{chart_markers}"
                self._log("📊 Chart markers preserved")
            
            return synthesized
            
        except Exception as e:
            self._log(f"⚠️  LLM synthesis failed: {e}")
            return None
    
    def _synthesize_with_llm(self, question: str, data_result: str, docs_result: str) -> Optional[str]:
        """
        Synthesize agent outputs using LLM
        
        Args:
            question: Original user question
            data_result: Raw output from DataAgent
            docs_result: Raw output from DocsAgent
            
        Returns:
            Synthesized response or None if synthesis fails
        """
        llm = self._get_llm()
        if not llm:
            return None
        
        try:
            # Clean inputs
            cleaned_data = self._clean_raw_output(data_result, "data")
            cleaned_docs = self._clean_raw_output(docs_result, "docs")
            
            # Check for chart markers in data result (preserve them)
            chart_markers = ""
            if "[PLOTLY_CHART_START]" in data_result and "[PLOTLY_CHART_END]" in data_result:
                import re as re_module
                chart_match = re_module.search(r'\[PLOTLY_CHART_START\].*?\[PLOTLY_CHART_END\]', data_result, re_module.DOTALL)
                if chart_match:
                    chart_markers = chart_match.group(0)
                    # Remove chart markers from cleaned_data so they don't appear in prompt
                    cleaned_data = re_module.sub(r'\[PLOTLY_CHART_START\].*?\[PLOTLY_CHART_END\]', '', cleaned_data, flags=re_module.DOTALL)
            
            # Check if user requested visualization
            viz_keywords = ['plot', 'chart', 'graph', 'visualize', 'visualization', 'show me a', 'display a', 'create a']
            is_viz_request = any(keyword in question.lower() for keyword in viz_keywords)
            
            # Build synthesis prompt
            synthesis_prompt = f"""You are a helpful assistant that synthesizes information from multiple sources to answer user questions about battery operations and trading.

User Question: {question}

Data Analysis Results (from SQL queries via Databricks Genie):
{cleaned_data}

Documentation Results (from technical documentation):
{cleaned_docs}

Please synthesize these results into a clear, coherent answer that:
1. Directly answers the user's question in a natural, conversational way
2. Combines relevant information from both data and documentation seamlessly
3. Includes specific numbers/values from the data when relevant (e.g., SoC percentages, revenue amounts, throughput values)
4. Explains concepts from documentation when helpful for understanding
5. Uses proper formatting with spaces around numbers and currency (e.g., "$100 revenue", not "$100revenue")
6. Maintains a professional, expert tone appropriate for Energy Australia operations
7. **IMPORTANT: Cite the source of information** - When presenting data or numbers, add "(Data Analysis)" at the end of sentences that come from the data results. When presenting concepts, definitions, or explanations from documentation, add "(Documentation)" at the end of those sentences. You can cite multiple sources in a single sentence if it combines both.
{"8. IMPORTANT: The user requested a visualization/chart. A chart has been generated and will be displayed below your response. Do NOT say you cannot create charts or visualizations - the chart is already created and will appear." if is_viz_request and chart_markers else ""}

Do not include:
- DEBUG information or debug markers
- Raw SQL queries (unless the user specifically asked to see the SQL)
- Raw query result arrays like ['RESS 2', '62.0', '82.7']
- Page numbers, line numbers, or file paths from documentation
- Technical implementation details unless relevant to the answer
{"- Statements saying you cannot create charts or visualizations (the chart is already generated)" if is_viz_request and chart_markers else ""}

Citation format examples:
- "RESS2 currently has a SoC of 82.7% (Data Analysis)."
- "Throughput is calculated using the throughput_mwh field in the battery_telemetry table (Documentation)."
- "The current SoC for RESS2 is 82.7% (Data Analysis), and throughput limits are enforced to prevent violations in the next 30 minutes (Documentation)."

Provide a clean, synthesized answer with proper citations:"""
            
            self._log("🤖 Synthesizing response with LLM...")
            
            # Call LLM
            response = llm.invoke(synthesis_prompt)
            
            # Extract content from response
            if hasattr(response, 'content'):
                synthesized = response.content
            elif isinstance(response, str):
                synthesized = response
            else:
                synthesized = str(response)
            
            self._log("✅ LLM synthesis completed")
            
            # Append chart markers if they were present
            synthesized = synthesized.strip()
            if chart_markers:
                synthesized += f"\n\n{chart_markers}"
                self._log("📊 Chart markers preserved in synthesized response")
            
            return synthesized
            
        except Exception as e:
            self._log(f"⚠️  LLM synthesis failed: {e}")
            return None
    
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
            
            # Check if result needs synthesis (raw JSON/data)
            if result and "[Data Agent Error]" not in result:
                synthesized = self._synthesize_single_agent_response(question, result, "data")
                if synthesized:
                    return synthesized
                
                # Fallback: clean result if it has debug info
                cleaned = self._clean_raw_output(result, "data")
                # Only use cleaned version if it's significantly different (has debug info)
                if cleaned != result and len(cleaned) > len(result) * 0.5:  # At least 50% of original
                    return cleaned
            return result
        elif docs_can_handle:
            # Route to docs agent
            self._log("📚 Routing to Docs Agent")
            result = self.docs_agent.process(question, context)
            self._log("✅ Docs Agent completed")
            
            # Check if result needs synthesis (raw data)
            if result and "[Docs Agent Error]" not in result:
                synthesized = self._synthesize_single_agent_response(question, result, "docs")
                if synthesized:
                    return synthesized
                
                # Fallback: clean result if needed
                cleaned = self._clean_raw_output(result, "docs")
                # Only use cleaned version if it's significantly different
                if cleaned != result and len(cleaned) > len(result) * 0.5:
                    return cleaned
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
        
        # Try to synthesize with LLM first
        synthesized_response = None
        if data_result and "[Data Agent Error]" not in data_result and docs_result and "[Docs Agent Error]" not in docs_result:
            # Both agents succeeded - try LLM synthesis
            synthesized_response = self._synthesize_with_llm(question, data_result, docs_result)
        
        # If synthesis succeeded, use it
        if synthesized_response:
            self._log("✅ Using LLM-synthesized response")
            return synthesized_response
        
        # Fallback to original concatenation method (safe fallback)
        self._log("⚠️  Using fallback concatenation method")
        
        # Synthesize results (original method)
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


