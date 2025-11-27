"""
LLM Integration for Power System Analysis

This module provides integration with Large Language Models (LLMs) to enhance
the AI assistant capabilities for power system analysis and visualization.

The module supports:
1. Natural language understanding for power system queries
2. Advanced visualization intent detection
3. Enhanced response generation for technical questions
4. Context-aware conversation management
"""

import os
import requests
import json
import logging
import time
from typing import Dict, List, Any, Optional, Union, Tuple
import re
import sqlite3
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import visualization types from ai_assistant if available
try:
    from ai_assistant import VISUALIZATION_TYPES
except ImportError:
    # Fallback if import fails
    VISUALIZATION_TYPES = {
        "single_line_diagram": "Single-line diagram showing the power system topology",
        "bus_voltage_profile": "Bus voltage profile showing voltage magnitudes across buses",
        "branch_loading": "Branch loading plots showing the loading levels of transmission lines",
        "time_series": "Time-series plots showing temporal evolution of system parameters",
        "heat_map": "Heat map visualization of system-wide parameters",
        "power_flow_arrows": "Power flow visualization with directional arrows",
        "voltage_stability": "Voltage stability margin curves",
        "generation_stack": "Generation stack plots showing contribution from different sources",
        "risk_map": "Probabilistic risk maps for system conditions",
        "contingency_analysis": "Contingency analysis visualization showing system under contingencies",
        "correlation_heatmap": "Correlation heat maps between different system parameters",
        "clustering": "Clustering analysis of power system components",
        "anomaly": "Anomaly detection in power system data",
        "correlation": "Correlation analysis between system parameters",
        "forecast": "Load or generation forecasting",
        "reliability": "System reliability assessment",
        "congestion": "Transmission congestion analysis"
    }

class LLMIntegration:
    """
    Integrates Large Language Models (LLMs) with the power system visualization tool.
    
    This class provides methods to:
    1. Process natural language queries with LLMs
    2. Detect visualization intents from user messages
    3. Generate enhanced responses for power system questions
    4. Provide context-aware conversation management
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo", 
                 api_base: Optional[str] = None, database_path: Optional[str] = None):
        """
        Initialize the LLM integration.
        
        Args:
            api_key: API key for the LLM service (OpenAI by default)
            model: Model name to use
            api_base: Alternative API endpoint if not using OpenAI directly
            database_path: Path to the SQLite database with power system data
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        self.api_base = api_base or "https://api.openai.com/v1"
        self.database_path = database_path
        self.system_prompt = self._get_system_prompt()
        
        # Check if we have API access
        self.api_available = self.api_key is not None
        if not self.api_available:
            logger.warning("No API key provided. LLM integration will use rule-based fallbacks.")
            
        # Try to connect to database if provided
        self.db_conn = None
        if database_path:
            try:
                self.db_conn = sqlite3.connect(database_path)
                logger.info(f"Connected to database: {database_path}")
            except Exception as e:
                logger.error(f"Database connection error: {e}")
    
    def _get_system_prompt(self) -> str:
        """
        Generate the system prompt for power system analysis.
        
        Returns:
            System prompt for the LLM
        """
        visualization_options = "\n".join([f"- {k}: {v}" for k, v in VISUALIZATION_TYPES.items()])
        
        return f"""You are an expert power systems engineer and data visualization specialist.
You analyze electrical grid data, particularly focusing on comparing Static Line Rating (SLR) 
and Dynamic Line Rating (DLR) methodologies.

Your knowledge includes:
- Power flow analysis and contingency management
- Transmission line thermal limits and rating methodologies
- Voltage stability and power system security
- Statistical analysis of power system data
- Advanced visualization techniques for grid data

When asked for visualizations, you can generate the following types:
{visualization_options}

For visualization requests:
1. Identify the most appropriate visualization type from the list above
2. Provide a brief explanation of what the visualization shows
3. Include relevant parameters needed for the visualization

For technical questions:
1. Provide concise, technically accurate explanations
2. Reference power system engineering principles
3. Use equations when appropriate, but explain them clearly

For data analysis questions:
1. Suggest appropriate statistical methods
2. Explain how to interpret the results
3. Mention limitations or assumptions

Always be helpful, accurate, and focused on power system topics.
"""
    
    def process_query(self, query: str, history: Optional[List[Dict]] = None, 
                     session_context: Optional[Dict] = None) -> Dict:
        """
        Process a user query using LLM.
        
        Args:
            query: User's query text
            history: Conversation history as a list of message dictionaries
            session_context: Additional context for the session
            
        Returns:
            Response dictionary with text and metadata
        """
        # Check if this is a visualization request
        is_visualization = self.detect_visualization_intent(query)
        
        # If we have API access, use the LLM
        if self.api_available:
            try:
                return self._process_with_llm(query, history, session_context, is_visualization)
            except Exception as e:
                logger.error(f"LLM processing error: {e}")
                # Fall back to rule-based processing if LLM fails
                return self._process_with_rules(query, is_visualization)
        else:
            # Use rule-based processing if no API access
            return self._process_with_rules(query, is_visualization)
    
    def _process_with_llm(self, query: str, history: Optional[List[Dict]], 
                         session_context: Optional[Dict], is_visualization: bool) -> Dict:
        """
        Process query using the LLM API.
        
        Args:
            query: User's query text
            history: Conversation history
            session_context: Additional context
            is_visualization: Whether this is a visualization request
            
        Returns:
            Response dictionary
        """
        # Prepare messages for the API call
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add session context if available
        if session_context:
            context_str = json.dumps(session_context)
            messages.append({"role": "system", "content": f"Session context: {context_str}"})
        
        # Add conversation history if available
        if history:
            for message in history[-5:]:  # Include last 5 messages for context
                messages.append({"role": message["role"], "content": message["content"]})
        
        # Add user query
        if is_visualization:
            # Add special instructions for visualization requests
            viz_instruction = "This is a visualization request. Please identify the specific type of visualization needed from the available options."
            messages.append({"role": "user", "content": f"{viz_instruction}\n\nUser query: {query}"})
        else:
            messages.append({"role": "user", "content": query})
        
        # Make API call
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        response = requests.post(
            f"{self.api_base}/chat/completions",
            headers=headers,
            data=json.dumps(data)
        )
        
        if response.status_code != 200:
            raise Exception(f"API error: {response.status_code}, {response.text}")
        
        result = response.json()
        response_text = result["choices"][0]["message"]["content"]
        
        # Process the response
        response_data = {
            "response": response_text,
            "role": "assistant",
            "timestamp": time.time()
        }
        
        # Extract visualization type if this is a visualization request
        if is_visualization:
            # Check for visualization type in the response
            viz_type = self._extract_visualization_type(response_text)
            if viz_type:
                response_data["visualization_type"] = viz_type
            else:
                # Default to the detected type if we couldn't extract from response
                response_data["visualization_type"] = is_visualization.get("visualization_type", "general_visualization")
        
        return response_data
    
    def _process_with_rules(self, query: str, is_visualization: Dict) -> Dict:
        """
        Process query using rule-based methods when LLM is not available.
        
        Args:
            query: User's query text
            is_visualization: Dictionary with visualization intent info
            
        Returns:
            Response dictionary
        """
        query_lower = query.lower()
        
        # Check if this is a visualization request
        if is_visualization and is_visualization.get("visualization_type") != "general_visualization":
            viz_type = is_visualization["visualization_type"]
            viz_desc = VISUALIZATION_TYPES.get(viz_type, "visualization")
            
            response = f"I'll generate a {viz_type.replace('_', ' ')} visualization for you. This will show {viz_desc.lower()}."
            
            return {
                "response": response,
                "visualization_type": viz_type,
                "role": "assistant",
                "timestamp": time.time()
            }
        
        # Handle other types of queries with rules
        if "slr" in query_lower and "dlr" in query_lower and ("compare" in query_lower or "difference" in query_lower):
            return {
                "response": ("Dynamic Line Rating (DLR) adapts transmission line capacity based on real-time weather conditions, "
                           "while Static Line Rating (SLR) uses fixed conservative ratings. DLR typically allows for 10-30% higher "
                           "capacity utilization compared to SLR, reducing congestion and enabling greater renewable integration."),
                "role": "assistant",
                "timestamp": time.time()
            }
        elif "bus" in query_lower or "buses" in query_lower:
            return {
                "response": "Buses are connection points in the power system where generators, loads, and transmission lines meet. "
                           "They are characterized by voltage magnitude, angle, and connected components.",
                "role": "assistant",
                "timestamp": time.time()
            }
        elif "branch" in query_lower or "line" in query_lower:
            return {
                "response": "Branches (transmission lines and transformers) connect buses in the power system. "
                           "They transfer power between different parts of the grid and have thermal limits that constrain their operation.",
                "role": "assistant",
                "timestamp": time.time()
            }
        elif "contingency" in query_lower:
            return {
                "response": "Contingency analysis examines how the power system behaves when components fail. "
                           "N-1 contingency analysis ensures the system remains operational after any single component failure.",
                "role": "assistant",
                "timestamp": time.time()
            }
        else:
            return {
                "response": "I understand you have a question about power systems. To provide better assistance, "
                           "could you please specify if you're asking about buses, branches, contingencies, "
                           "or comparing SLR and DLR methodologies?",
                "role": "assistant",
                "timestamp": time.time()
            }
    
    def detect_visualization_intent(self, message: str) -> Dict:
        """
        Detect if the user is requesting a visualization and what type.
        
        Args:
            message: User's message
            
        Returns:
            Dictionary with visualization intent information or None
        """
        if self.api_available:
            try:
                # Use LLM to detect visualization intent
                return self._detect_visualization_with_llm(message)
            except Exception as e:
                logger.error(f"LLM visualization detection error: {e}")
                # Fall back to rule-based detection
                return self._detect_visualization_with_rules(message)
        else:
            # Use rule-based detection if LLM not available
            return self._detect_visualization_with_rules(message)
    
    def _detect_visualization_with_llm(self, message: str) -> Dict:
        """
        Use LLM to detect visualization intent.
        
        Args:
            message: User's message
            
        Returns:
            Dictionary with visualization intent information
        """
        # List all visualization types for the LLM
        viz_types_list = "\n".join([f"- {k}" for k in VISUALIZATION_TYPES.keys()])
        
        # Prepare the prompt
        prompt = f"""Analyze the following user message and determine if they are requesting a visualization. 
If they are, identify the specific type of visualization from this list:

{viz_types_list}

If none match exactly, choose the closest one. If it's not a visualization request, return "general_visualization".
Output ONLY a JSON object with a single key "visualization_type" and the value as the type.

User message: {message}

JSON:"""

        # Make API call
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a visualization intent classifier for power systems."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 50
        }
        
        response = requests.post(
            f"{self.api_base}/chat/completions",
            headers=headers,
            data=json.dumps(data)
        )
        
        if response.status_code != 200:
            raise Exception(f"API error: {response.status_code}, {response.text}")
        
        result = response.json()
        response_text = result["choices"][0]["message"]["content"].strip()
        
        # Extract JSON from response
        try:
            # Try to parse the response as JSON directly
            intent_data = json.loads(response_text)
            return intent_data
        except json.JSONDecodeError:
            # Try to extract JSON using regex if direct parsing fails
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    intent_data = json.loads(json_match.group(0))
                    return intent_data
                except:
                    pass
            
            # If all parsing fails, extract the visualization type using simple text matching
            for viz_type in VISUALIZATION_TYPES.keys():
                if viz_type in response_text or viz_type.replace("_", " ") in response_text:
                    return {"visualization_type": viz_type}
            
            # Default fallback
            return {"visualization_type": "general_visualization"}
    
    def _detect_visualization_with_rules(self, message: str) -> Dict:
        """
        Rule-based detection of visualization intent.
        
        Args:
            message: User's message
            
        Returns:
            Dictionary with visualization intent information
        """
        message_lower = message.lower()
        
        # Check for visualization keywords
        viz_keywords = ["show", "plot", "graph", "visualize", "display", "chart", "diagram"]
        is_viz_request = any(keyword in message_lower for keyword in viz_keywords)
        
        if not is_viz_request:
            return {"visualization_type": "general_visualization"}
        
        # Check for specific visualization types
        if "single line" in message_lower or "diagram" in message_lower or "topology" in message_lower:
            return {"visualization_type": "single_line_diagram"}
        elif "bus voltage" in message_lower or "voltage profile" in message_lower:
            return {"visualization_type": "bus_voltage_profile"}
        elif "branch load" in message_lower or "loading plot" in message_lower or "line load" in message_lower:
            return {"visualization_type": "branch_loading"}
        elif "time-series" in message_lower or "temporal" in message_lower or "over time" in message_lower:
            return {"visualization_type": "time_series"}
        elif "heat map" in message_lower or "heatmap" in message_lower or "color map" in message_lower:
            return {"visualization_type": "heat_map"}
        elif "power flow" in message_lower or "arrows" in message_lower or "flow direction" in message_lower:
            return {"visualization_type": "power_flow_arrows"}
        elif "voltage stability" in message_lower or "margin curve" in message_lower or "pv curve" in message_lower:
            return {"visualization_type": "voltage_stability"}
        elif "generation stack" in message_lower or "generation mix" in message_lower or "supply stack" in message_lower:
            return {"visualization_type": "generation_stack"}
        elif "risk map" in message_lower or "probabilistic" in message_lower or "uncertainty" in message_lower:
            return {"visualization_type": "risk_map"}
        elif "contingency analysis" in message_lower or "outage" in message_lower or "n-1" in message_lower:
            return {"visualization_type": "contingency_analysis"}
        elif "correlation" in message_lower and "heat" in message_lower:
            return {"visualization_type": "correlation_heatmap"}
        elif "cluster" in message_lower or "grouping" in message_lower or "segmentation" in message_lower:
            return {"visualization_type": "clustering"}
        elif "anomaly" in message_lower or "outlier" in message_lower or "unusual" in message_lower:
            return {"visualization_type": "anomaly"}
        elif "forecast" in message_lower or "predict" in message_lower or "future" in message_lower:
            return {"visualization_type": "forecast"}
        elif "reliability" in message_lower or "resilience" in message_lower or "robustness" in message_lower:
            return {"visualization_type": "reliability"}
        elif "congestion" in message_lower or "bottleneck" in message_lower or "constraint" in message_lower:
            return {"visualization_type": "congestion"}
        
        # Default for general visualization requests
        return {"visualization_type": "general_visualization"}
    
    def _extract_visualization_type(self, response_text: str) -> Optional[str]:
        """
        Extract visualization type from LLM response.
        
        Args:
            response_text: Response from the LLM
            
        Returns:
            Visualization type or None if not found
        """
        response_lower = response_text.lower()
        
        # First try to find exact matches
        for viz_type in VISUALIZATION_TYPES.keys():
            viz_type_words = viz_type.replace('_', ' ')
            if viz_type in response_lower or viz_type_words in response_lower:
                return viz_type
        
        # Try looser matching if exact match fails
        for viz_type, description in VISUALIZATION_TYPES.items():
            key_terms = viz_type.replace('_', ' ').split()
            if all(term in response_lower for term in key_terms):
                return viz_type
        
        return None

    def get_db_summary(self) -> Dict:
        """
        Get a summary of the database structure and content.
        
        Returns:
            Dictionary with database summary information
        """
        if not self.db_conn:
            return {"error": "No database connection available"}
        
        try:
            cursor = self.db_conn.cursor()
            
            # Get list of tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            summary = {"tables": {}}
            
            # Get information about each table
            for table_name in [t[0] for t in tables]:
                # Get column info
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                
                # Add to summary
                summary["tables"][table_name] = {
                    "columns": [col[1] for col in columns],
                    "column_types": [col[2] for col in columns],
                    "row_count": row_count
                }
            
            return summary
        
        except Exception as e:
            logger.error(f"Error getting database summary: {e}")
            return {"error": f"Database error: {str(e)}"}
        
    def generate_context_for_query(self, query: str) -> Dict:
        """
        Generate relevant context information for a query.
        
        Args:
            query: User's query text
            
        Returns:
            Dictionary with context information
        """
        context = {}
        
        # Get database summary if available
        if self.db_conn:
            context["database"] = self.get_db_summary()
        
        # Add visualization types
        context["visualization_types"] = list(VISUALIZATION_TYPES.keys())
        
        # Add query-specific context
        query_lower = query.lower()
        
        if "bus" in query_lower or "buses" in query_lower:
            # Add bus-related information
            if self.db_conn:
                try:
                    # Get summary of bus data
                    df = pd.read_sql_query("SELECT * FROM buses LIMIT 5", self.db_conn)
                    context["bus_data_sample"] = df.to_dict('records')
                except:
                    pass
        
        if "branch" in query_lower or "line" in query_lower:
            # Add branch-related information
            if self.db_conn:
                try:
                    # Get summary of branch data
                    df = pd.read_sql_query("SELECT * FROM branches LIMIT 5", self.db_conn)
                    context["branch_data_sample"] = df.to_dict('records')
                except:
                    pass
        
        if "contingency" in query_lower:
            # Add contingency-related information
            if self.db_conn:
                try:
                    # Get list of contingencies
                    df = pd.read_sql_query(
                        "SELECT DISTINCT contingency_id FROM contingency_branches LIMIT 10", 
                        self.db_conn
                    )
                    context["contingencies"] = df["contingency_id"].tolist()
                except:
                    pass
        
        return context


# Simple test function
def test_llm_integration():
    """Test the LLM integration with a few queries."""
    # Create LLM integration instance
    llm = LLMIntegration()
    
    # Test queries
    test_queries = [
        "What is the difference between SLR and DLR?",
        "Show me a single line diagram of the system",
        "Can you explain what a contingency analysis is?",
        "Generate a bus voltage profile visualization",
        "How many buses are in the system?"
    ]
    
    print("Testing LLM integration...")
    for query in test_queries:
        print(f"\nQuery: {query}")
        viz_intent = llm.detect_visualization_intent(query)
        print(f"Visualization intent: {viz_intent}")
        
        response = llm.process_query(query)
        print(f"Response: {response.get('response', '')[:100]}...")
        
        if "visualization_type" in response:
            print(f"Visualization type: {response['visualization_type']}")
    
    print("\nTest completed")


if __name__ == "__main__":
    test_llm_integration()