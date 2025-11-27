"""
LLM-enhanced AI Assistant for Power System Analysis

This module integrates the LLM capabilities with the existing AI assistant
for enhanced power system analysis and visualization.
"""

import os
import logging
import json
import time
from typing import Dict, List, Any, Optional, Tuple

# Import the base AI assistant
from ai_assistant import ConversationalAIAssistant, QueryType, VISUALIZATION_TYPES

# Import LLM integration
from llm_integration import LLMIntegration

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LLMEnhancedAssistant(ConversationalAIAssistant):
    """
    Enhanced AI Assistant with LLM integration for power system analysis.
    
    This class extends the base ConversationalAIAssistant with LLM capabilities
    for improved natural language understanding and response generation.
    """
    
    def __init__(self, database_path: str, config_path: str = "config.json",
                 api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        """
        Initialize the LLM-enhanced AI assistant.
        
        Args:
            database_path: Path to the SQLite database
            config_path: Path to configuration file
            api_key: API key for the LLM service
            model: LLM model to use
        """
        # Initialize the base assistant
        super().__init__(database_path, config_path)
        
        # Initialize LLM integration
        self.llm = LLMIntegration(
            api_key=api_key, 
            model=model,
            database_path=database_path
        )
        
        # Flag to indicate LLM availability
        self.llm_available = self.llm.api_available
        logger.info(f"LLM enhanced assistant initialized. LLM available: {self.llm_available}")
    
    def process_query(self, session_id: str, query: str) -> Dict[str, Any]:
        """
        Process a user query with LLM enhancement if available.
        
        Args:
            session_id: ID of the conversation session
            query: User's natural language query
            
        Returns:
            Dictionary containing response text and metadata
        """
        # Check if session exists
        if session_id not in self.sessions:
            return {"error": "Invalid session ID"}
        
        # Update session activity timestamp
        self.sessions[session_id]["last_active"] = time.time()
        
        # Add query to history
        self.sessions[session_id]["history"].append({
            "role": "user",
            "content": query,
            "timestamp": time.time()
        })
        
        # Get conversation history
        history = self.sessions[session_id]["history"]
        
        # Get session context
        session_context = {
            "expertise_level": self.sessions[session_id].get("expertise_level", "intermediate"),
            "client_id": self.sessions[session_id].get("client_id", "unknown")
        }
        
        # Check if we should use LLM or base assistant
        if self.llm_available:
            # Try with LLM first
            try:
                # First, detect if this is a visualization request
                viz_intent = self.llm.detect_visualization_intent(query)
                
                # Generate response with LLM
                response_data = self.llm.process_query(
                    query=query,
                    history=history,
                    session_context=session_context
                )
                
                # Check if this is a visualization request
                if viz_intent and viz_intent.get("visualization_type") != "general_visualization":
                    if "visualization_type" not in response_data:
                        response_data["visualization_type"] = viz_intent["visualization_type"]
                
                # Add suggestions
                response_data["suggestions"] = self._generate_suggestions(query)
                
                # Add response to history
                self.sessions[session_id]["history"].append({
                    "role": "assistant",
                    "content": response_data["response"],
                    "timestamp": time.time()
                })
                
                return response_data
                
            except Exception as e:
                logger.error(f"LLM processing error: {e}")
                logger.info("Falling back to base assistant")
                # Fall back to base assistant if LLM fails
        
        # Use base assistant processing
        return super().process_query(session_id, query)
    
    def classify_visualization_intent(self, message: str) -> Dict[str, str]:
        """
        Enhanced classification of visualization intent using LLM if available.
        
        Args:
            message: User message requesting visualization
            
        Returns:
            Dict containing the classified visualization type
        """
        # Try LLM-based classification if available
        if self.llm_available:
            try:
                return self.llm.detect_visualization_intent(message)
            except Exception as e:
                logger.error(f"LLM visualization detection error: {e}")
                # Fall back to rule-based if LLM fails
                logger.info("Falling back to rule-based classification")
        
        # Fall back to rule-based classification from base assistant
        message_lower = message.lower()
        
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


# Function to update the existing classify_visualization_intent function
def classify_visualization_intent(message: str) -> Dict[str, str]:
    """
    Enhanced classification of visualization intent that can be used separately.
    This is a standalone version of the method that can be imported directly.
    
    Args:
        message: User message requesting visualization
        
    Returns:
        Dict containing the classified visualization type
    """
    # Try to use LLM if available
    try:
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            llm = LLMIntegration(api_key=api_key)
            if llm.api_available:
                return llm.detect_visualization_intent(message)
    except Exception as e:
        logger.error(f"Error using LLM for visualization classification: {e}")
    
    # Fall back to rule-based classification
    message_lower = message.lower()
    
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


# Test function
def test_llm_assistant():
    """Test the LLM-enhanced assistant."""
    import sys
    
    # Get database path from command line or use default
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        # Default path if none provided
        db_path = "data.db"
    
    print(f"Initializing LLM-enhanced AI Assistant with database: {db_path}")
    assistant = LLMEnhancedAssistant(db_path)
    
    # Create a test session
    session_id = assistant.create_session("test_client", "intermediate")
    
    # Test queries
    test_queries = [
        "How many buses are in the system?",
        "Explain the difference between SLR and DLR",
        "Show me a single line diagram of the system",
        "Generate a bus voltage profile visualization",
        "What is a contingency analysis?",
        "Show me time-series data for bus voltages",
        "Create a heat map of system congestion"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        response = assistant.process_query(session_id, query)
        print(f"Response: {response['response']}")
        
        # Check if visualization
        if "visualization_type" in response:
            print(f"Visualization type: {response['visualization_type']}")


if __name__ == "__main__":
    test_llm_assistant()