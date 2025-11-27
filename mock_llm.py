"""
Mock LLM Integration for Power System Analysis

This module provides a mock implementation of LLM capabilities when no API
access is available. It enhances the rule-based assistant with better
visualization intent detection and response generation without requiring
external API access.
"""

import logging
import time
from typing import Dict, List, Any, Optional, Tuple

# Import visualization types from ai_assistant
from ai_assistant import VISUALIZATION_TYPES, ConversationalAIAssistant, QueryType

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockLLMAssistant(ConversationalAIAssistant):
    """
    Enhanced AI Assistant with mock LLM capabilities for power system analysis.
    
    This class extends the base ConversationalAIAssistant with enhanced
    rule-based methods that mimic LLM capabilities without requiring API access.
    """
    
    def __init__(self, database_path: str, config_path: str = "config.json"):
        """
        Initialize the mock LLM-enhanced AI assistant.
        
        Args:
            database_path: Path to the SQLite database
            config_path: Path to configuration file
        """
        # Initialize the base assistant
        super().__init__(database_path, config_path)
        
        # Flag to indicate this is a mock LLM
        self.llm_available = True  # We pretend it's available but it's actually enhanced rules
        logger.info("Mock LLM Assistant initialized (enhanced rules without API)")
        
        # Enhanced rule patterns for visualization detection
        self._init_enhanced_patterns()
    
    def _init_enhanced_patterns(self):
        """Initialize enhanced patterns for visualization detection"""
        # This extends the basic patterns with more variations and synonyms
        self.enhanced_viz_patterns = {
            "single_line_diagram": [
                "single line", "diagram", "topology", "network diagram", "grid layout",
                "system diagram", "schematic", "connection diagram", "network visualization"
            ],
            "bus_voltage_profile": [
                "bus voltage", "voltage profile", "voltage magnitude", "voltage level",
                "voltage across", "bus potential", "nodal voltage", "voltage distribution"
            ],
            "branch_loading": [
                "branch load", "loading plot", "line load", "transmission line load",
                "loading level", "branch utilization", "line capacity", "power flow loading"
            ],
            "time_series": [
                "time-series", "temporal", "over time", "chronological", "time plot",
                "time evolution", "time varying", "historical data", "time dependent"
            ],
            "heat_map": [
                "heat map", "heatmap", "color map", "thermal map", "density plot",
                "intensity map", "gradient visualization", "color-coded map"
            ],
            "power_flow_arrows": [
                "power flow", "arrows", "flow direction", "directional flow",
                "vector flow", "flow visualization", "directional arrows"
            ],
            "voltage_stability": [
                "voltage stability", "margin curve", "pv curve", "qv curve",
                "stability margin", "collapse point", "stability analysis"
            ],
            "generation_stack": [
                "generation stack", "generation mix", "supply stack", "energy mix",
                "production stack", "generation contribution", "stacked generation"
            ],
            "risk_map": [
                "risk map", "probabilistic", "uncertainty", "risk visualization",
                "probability map", "confidence level", "uncertainty visualization"
            ],
            "contingency_analysis": [
                "contingency analysis", "outage", "n-1", "security analysis",
                "failure scenario", "contingency simulation", "outage study"
            ],
            "correlation_heatmap": [
                "correlation heat", "correlation map", "variable correlation",
                "parameter correlation", "correlation matrix", "relationship map"
            ],
            "clustering": [
                "cluster", "grouping", "segmentation", "classification",
                "data clusters", "k-means", "hierarchical clustering"
            ],
            "anomaly": [
                "anomaly", "outlier", "unusual", "abnormal", "deviation",
                "anomaly detection", "outlier analysis", "unusual pattern"
            ],
            "forecast": [
                "forecast", "predict", "future", "projection", "estimation",
                "predicted values", "forecasting", "trend prediction"
            ],
            "reliability": [
                "reliability", "resilience", "robustness", "dependability",
                "availability", "system reliability", "grid resilience"
            ],
            "congestion": [
                "congestion", "bottleneck", "constraint", "transmission constraint",
                "flow limitation", "network congestion", "congestion analysis"
            ]
        }
    
    def classify_visualization_intent(self, message: str) -> Dict[str, str]:
        """
        Enhanced classification of visualization intent using extended rule patterns.
        
        Args:
            message: User message requesting visualization
            
        Returns:
            Dict containing the classified visualization type
        """
        message_lower = message.lower()
        
        # Check for words related to visualization in general
        viz_words = ["show", "plot", "graph", "chart", "display", "visualize", 
                    "visualisation", "visualization", "draw", "create", "generate"]
        
        has_viz_intent = any(word in message_lower for word in viz_words)
        
        # Check for specific visualization types using enhanced patterns
        for viz_type, patterns in self.enhanced_viz_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                return {"visualization_type": viz_type}
        
        # If there are visualization words but no specific type matched,
        # classify as general visualization
        if has_viz_intent:
            return {"visualization_type": "general_visualization"}
            
        # Default to no visualization intent
        return {"visualization_type": "none"}
    
    def process_query(self, session_id: str, query: str) -> Dict[str, Any]:
        """
        Process a user query with enhanced rule-based response generation.
        
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
        
        # Process with base functionality first
        response = super().process_query(session_id, query)
        
        # Get query type from session history
        query_type = None
        if 'conversation_history' in self.sessions[session_id]:
            # Find the last query type
            history = self.sessions[session_id]['conversation_history']
            for entry in reversed(history):
                if entry.get('role') == 'user' and 'query_type' in entry:
                    query_type = entry.get('query_type')
                    break
        
        # Enhanced statistical analysis results
        if query_type == QueryType.STATISTICAL_ANALYSIS:
            try:
                # Check if response contains analysis results
                if isinstance(response, dict) and not response.get("error"):
                    # Enhance the statistical analysis with insights and recommendations
                    enhanced_results = self._enhance_statistical_analysis(query, response)
                    
                    # Add insights and recommendations to the response
                    if "insights" in enhanced_results and enhanced_results["insights"]:
                        response["response"] += "\n\n## Key Insights:\n"
                        for insight in enhanced_results["insights"]:
                            response["response"] += f"- {insight}\n"
                    
                    if "recommendations" in enhanced_results and enhanced_results["recommendations"]:
                        response["response"] += "\n## Recommendations:\n"
                        for recommendation in enhanced_results["recommendations"]:
                            response["response"] += f"- {recommendation}\n"
                    
                    # Add extra fields if present
                    for key, value in enhanced_results.items():
                        if key not in response and key not in ["response", "suggestions"]:
                            response[key] = value
            except Exception as e:
                logger.error(f"Error enhancing statistical analysis: {str(e)}")
        
        # Enhanced visualization detection
        viz_intent = self.classify_visualization_intent(query)
        if viz_intent["visualization_type"] != "none":
            response["visualization_type"] = viz_intent["visualization_type"]
            
            # Add enhanced explanation based on visualization type
            if viz_intent["visualization_type"] in VISUALIZATION_TYPES:
                viz_name = viz_intent["visualization_type"].replace("_", " ").title()
                response["response"] += f"\n\nI'll create a {viz_name} visualization for you. " \
                                       f"This will help you {self._get_viz_purpose(viz_intent['visualization_type'])}."
        
        # Enhanced suggestions based on query context
        enhanced_suggestions = self._generate_enhanced_suggestions(query)
        if enhanced_suggestions:
            response["suggestions"] = enhanced_suggestions
            
        return response
    
    def _enhance_statistical_analysis(self, query: str, analysis_results: Dict) -> Dict:
        """
        Enhance statistical analysis results with mock LLM capabilities.
        
        Args:
            query: Original user query
            analysis_results: Results from statistical analysis
            
        Returns:
            Enhanced analysis results with insights and recommendations
        """
        enhanced_results = analysis_results.copy()
        
        # Add insights section
        enhanced_results["insights"] = []
        
        # Generate insights based on analysis results
        if "violation_summary" in analysis_results:
            vs = analysis_results["violation_summary"]
            if vs.get("total_count", 0) > 0:
                enhanced_results["insights"].append(
                    f"There are {vs.get('total_count', 0)} violations across {vs.get('case_count', 0)} cases, "
                    f"indicating potential system stress points that require attention."
                )
                
                if vs.get("std_dev", 0) > vs.get("avg_value", 0) * 0.5:
                    enhanced_results["insights"].append(
                        "The high standard deviation in violation values suggests significant variability "
                        "in violation severity. Focus on the most severe outliers first."
                    )
        
        if "branch_summary" in analysis_results:
            bs = analysis_results["branch_summary"]
            if bs.get("avg_normal_rating", 0) > 0:
                enhanced_results["insights"].append(
                    f"The transmission system has {bs.get('line_count', 0)} branches with an average "
                    f"normal rating of {bs.get('avg_normal_rating', 0):.2f} MVA and emergency rating of "
                    f"{bs.get('avg_emergency_rating', 0):.2f} MVA."
                )
        
        if "bus_summary" in analysis_results:
            bus = analysis_results["bus_summary"]
            voltage_range = bus.get("max_voltage", 0) - bus.get("min_voltage", 0)
            if voltage_range > 0.2:  # More than 0.2 p.u. range
                enhanced_results["insights"].append(
                    f"The system has a wide voltage range of {voltage_range:.3f} p.u. "
                    f"({bus.get('min_voltage', 0):.3f} to {bus.get('max_voltage', 0):.3f}), "
                    f"suggesting potential voltage regulation issues."
                )
        
        if "dlr_benefits" in analysis_results:
            dlr = analysis_results["dlr_benefits"]
            if dlr.get("resolution_percentage", 0) > 50:
                enhanced_results["insights"].append(
                    f"DLR technology resolves {dlr.get('resolution_percentage', 0):.1f}% of violations, "
                    f"demonstrating significant value for grid operations."
                )
        
        # Add recommendations section
        enhanced_results["recommendations"] = []
        
        # Generate recommendations based on analysis results and insights
        if "congested_lines" in analysis_results and analysis_results["congested_lines"]:
            enhanced_results["recommendations"].append(
                "Consider applying DLR to the most frequently congested lines to increase transfer capacity."
            )
        
        if "voltage_hotspots" in analysis_results and analysis_results["voltage_hotspots"]:
            enhanced_results["recommendations"].append(
                "Review reactive power support near voltage violation hotspots to improve voltage profiles."
            )
        
        if "violation_by_type" in analysis_results and analysis_results["violation_by_type"]:
            # Get most common violation type
            most_common = analysis_results["violation_by_type"][0] if analysis_results["violation_by_type"] else None
            if most_common:
                violation_type = most_common.get("violation_type", "")
                if "branch" in violation_type.lower() or "flow" in violation_type.lower():
                    enhanced_results["recommendations"].append(
                        "Consider transmission expansion planning or operational procedures to address recurring branch flow violations."
                    )
                elif "voltage" in violation_type.lower():
                    enhanced_results["recommendations"].append(
                        "Evaluate capacitor bank placement or SVCs to address voltage violations."
                    )
        
        # Return enhanced results
        return enhanced_results
        
    def _get_viz_purpose(self, viz_type: str) -> str:
        """Get the purpose description for a visualization type"""
        purposes = {
            "single_line_diagram": "understand the overall network topology and connections",
            "bus_voltage_profile": "analyze voltage variations across different buses in the system",
            "branch_loading": "identify heavily loaded transmission lines and potential bottlenecks",
            "time_series": "observe how parameters change over time and identify trends",
            "heat_map": "identify patterns and hotspots in system-wide parameters",
            "power_flow_arrows": "understand the direction and magnitude of power flows",
            "voltage_stability": "assess the system's proximity to voltage collapse",
            "generation_stack": "understand the contribution from different generation sources",
            "risk_map": "assess areas of potential risk and uncertainty",
            "contingency_analysis": "understand system behavior under various outage scenarios",
            "correlation_heatmap": "identify relationships between different system parameters",
            "clustering": "identify natural groupings in power system data",
            "anomaly": "detect unusual patterns or outliers in the system",
            "forecast": "anticipate future system conditions and prepare accordingly",
            "reliability": "understand the system's ability to maintain service under various conditions",
            "congestion": "identify transmission bottlenecks and constrained paths"
        }
        
        return purposes.get(viz_type, "visualize this aspect of the power system")
    
    def _generate_enhanced_suggestions(self, query: str) -> List[str]:
        """Generate enhanced follow-up suggestions based on the query"""
        query_lower = query.lower()
        
        # Initialize suggestions
        suggestions = []
        
        # Check for DLR/SLR related queries
        if "dlr" in query_lower or "dynamic line" in query_lower:
            suggestions.append("Compare DLR with SLR benefits")
            suggestions.append("Show economic impact of DLR")
            
        if "slr" in query_lower or "static line" in query_lower:
            suggestions.append("Why is DLR better than SLR?")
            suggestions.append("Show thermal violations with SLR")
        
        # Check for contingency related queries
        if "contingency" in query_lower or "outage" in query_lower or "n-1" in query_lower:
            suggestions.append("Which contingency has the most violations?")
            suggestions.append("Compare worst-case contingencies")
            
        # Check for visualization related queries
        if "visualize" in query_lower or "plot" in query_lower or "graph" in query_lower:
            suggestions.append("Show a heatmap of line loadings")
            suggestions.append("Create a time-series of bus voltages")
        
        # Check for statistical analysis related queries
        if any(term in query_lower for term in ["statistics", "statistical", "analysis", "stats", "metrics"]):
            suggestions.append("Show violation statistics by type")
            suggestions.append("Analyze bus voltage distribution")
            suggestions.append("Calculate system loading statistics")
            
        if any(term in query_lower for term in ["violation", "violations"]):
            suggestions.append("Show statistics on all violations")
            suggestions.append("Analyze violation patterns over time")
            
        if any(term in query_lower for term in ["voltage", "voltages"]):
            suggestions.append("Calculate voltage statistics by area")
            suggestions.append("Show voltage violation frequency")
            
        if any(term in query_lower for term in ["line", "branch", "flow"]):
            suggestions.append("Show statistics on branch loadings")
            suggestions.append("Analyze most congested corridors")
            
        # Add some general suggestions if no specific ones were found
        if not suggestions:
            suggestions = [
                "Explain the difference between SLR and DLR",
                "Show the most constrained lines",
                "Analyze the worst contingency",
                "Show voltage violations across the system"
            ]
            
        # Return 2-3 suggestions
        return suggestions[:3]


# Factory function to get the appropriate assistant
def get_assistant(db_path: str, use_mock_llm: bool = False, use_llama: bool = False):
    """
    Get the appropriate assistant based on availability and settings.
    
    Args:
        db_path: Path to the database
        use_mock_llm: Whether to use mock LLM even if real LLM is available
        use_llama: Whether to use Llama instead of OpenAI API
        
    Returns:
        The appropriate assistant instance
    """
    import os
    
    # Check for Llama first if requested
    if use_llama:
        try:
            from llama_assistant import LlamaEnhancedAssistant
            
            # Check if API URL is available
            llama_api_url = os.environ.get("LLAMA_API_URL")
            llama_api_key = os.environ.get("LLAMA_API_KEY")
            
            if llama_api_url:
                llama_model = os.environ.get("LLAMA_MODEL", "llama-3-70b-chat")
                logger.info(f"Using Llama Enhanced Assistant with model {llama_model}")
                return LlamaEnhancedAssistant(db_path, api_url=llama_api_url, api_key=llama_api_key, model=llama_model)
        except ImportError:
            logger.warning("Llama assistant module not available")
    
    # Try to import OpenAI LLM assistant if Llama is not used or not available
    if not use_llama:
        try:
            from llm_assistant import LLMEnhancedAssistant
            
            # Check if API key is available and mock is not requested
            if os.environ.get("OPENAI_API_KEY") and not use_mock_llm:
                return LLMEnhancedAssistant(db_path)
        except ImportError:
            pass
    
    # Use mock LLM if requested
    if use_mock_llm:
        return MockLLMAssistant(db_path)
    
    # Fall back to base assistant
    return ConversationalAIAssistant(db_path)


# Test function
if __name__ == "__main__":
    import sys
    
    # Get database path from command line or use default
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        # Default path
        db_path = "C:/Projects/dlr-database-project/data.db"
    
    print(f"Testing Mock LLM Assistant with database: {db_path}")
    assistant = MockLLMAssistant(db_path)
    
    # Create a test session
    session_id = assistant.create_session("test_client", "intermediate")
    
    # Test queries
    test_queries = [
        "How many buses are in the system?",
        "Explain the difference between SLR and DLR",
        "Show me a single line diagram of the system",
        "Create a heatmap visualization of line loading",
        "What is a contingency analysis?",
        "Generate a time-series plot for bus voltages",
        "Show me congestion in the system"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        response = assistant.process_query(session_id, query)
        print(f"Response: {response['response']}")
        
        # Check if visualization
        if "visualization_type" in response:
            print(f"Visualization type: {response['visualization_type']}")
        
        # Check suggestions
        if "suggestions" in response:
            print(f"Suggestions: {response['suggestions']}")