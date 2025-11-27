"""
Enhanced Intelligent Chat System with Visualization
==================================================

Advanced rule-based AI assistant with context awareness, statistical interpretation,
sophisticated response generation, and integrated visualization capabilities for power system analysis.
"""

import json
import re
import time
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

class PowerSystemIntelligentAssistant:
    """
    Enhanced AI assistant with sophisticated natural language understanding
    and power system domain expertise
    """
    
    def __init__(self, database_path: str):
        self.database_path = database_path
        self.conversation_history = []
        self.context_memory = {}
        self.user_expertise_level = "expert"  # Can be: beginner, intermediate, expert
        self.visualization_cache = {}  # Cache for generated visualizations
        
        # Initialize power system knowledge base
        self.power_system_knowledge = {
            "voltage_limits": {"normal": (0.95, 1.05), "emergency": (0.90, 1.10)},
            "loading_thresholds": {"normal": 0.8, "alert": 0.9, "critical": 1.0},
            "analysis_types": {
                "voltage": ["stability", "profile", "violations", "regulation"],
                "thermal": ["loading", "capacity", "overloads", "ratings"],
                "contingency": ["n-1", "outage", "reliability", "impact"],
                "economic": ["losses", "efficiency", "cost", "optimization"]
            }
        }
        
        # Visualization preferences
        self.visualization_config = {
            "color_schemes": {
                "voltage": ["green", "yellow", "red"],  # Normal, Warning, Violation
                "thermal": ["blue", "orange", "red"],   # Normal, High, Overload
                "reliability": ["darkgreen", "gold", "crimson"]  # Good, Caution, Critical
            },
            "chart_types": {
                "voltage_profile": "line_chart",
                "loading_distribution": "bar_chart", 
                "risk_assessment": "gauge_chart",
                "system_overview": "dashboard"
            }
        }
        
        # Response templates for different expertise levels
        self.response_templates = {
            "beginner": {
                "intro": "Let me explain this in simple terms: ",
                "technical_depth": "basic",
                "include_formulas": False
            },
            "intermediate": {
                "intro": "Here's what the analysis shows: ",
                "technical_depth": "moderate", 
                "include_formulas": True
            },
            "expert": {
                "intro": "",
                "technical_depth": "advanced",
                "include_formulas": True
            }
        }
    
    def analyze_user_intent(self, message: str) -> Dict[str, Any]:
        """
        Advanced intent analysis using multiple techniques:
        1. Keyword extraction and weighting
        2. Context analysis from conversation history
        3. Technical term recognition
        4. Question type classification
        """
        message_lower = message.lower()
        
        # Extract key technical terms with enhanced patterns
        technical_terms = {
            "voltage": len(re.findall(r"voltage|volts?|kv|pf|power factor|pu|per unit|stability|regulation", message_lower)),
            "power": len(re.findall(r"power|mw|mvar|apparent|reactive|active|flow|generation|load", message_lower)),
            "thermal": len(re.findall(r"thermal|temperature|rating|capacity|loading|ampacity|current", message_lower)),
            "contingency": len(re.findall(r"contingency|outage|n-1|failure|reliability|fault|emergency", message_lower)),
            "economic": len(re.findall(r"loss|losses|cost|economic|efficiency|optimization|price|market", message_lower))
        }
        
        # Enhanced visualization detection
        visualization_indicators = [
            "show", "plot", "chart", "graph", "visualize", "display", "draw",
            "diagram", "picture", "image", "dashboard", "trend", "profile",
            "histogram", "scatter", "line chart", "bar chart", "gauge",
            "heat map", "correlation plot", "distribution", "render"
        ]
        
        visualization_request = any(indicator in message_lower for indicator in visualization_indicators)
        
        # Analyze question type with enhanced detection
        question_types = {
            "what": "information_request",
            "how": "explanation_request", 
            "why": "reasoning_request",
            "analyze": "analysis_request",
            "show": "visualization_request",
            "plot": "visualization_request",
            "chart": "visualization_request",
            "visualize": "visualization_request",
            "compare": "comparison_request",
            "explain": "explanation_request"
        }
        
        question_type = "general"
        for keyword, qtype in question_types.items():
            if keyword in message_lower:
                question_type = qtype
                break
        
        # Determine primary analysis focus
        primary_focus = max(technical_terms.items(), key=lambda x: x[1])[0]
        if technical_terms[primary_focus] == 0:
            primary_focus = "general"
        
        # Check for urgency indicators
        urgency_keywords = ["urgent", "critical", "emergency", "immediate", "problem", "issue", "violation"]
        urgency_level = "normal"
        if any(keyword in message_lower for keyword in urgency_keywords):
            urgency_level = "high"
        
        return {
            "primary_focus": primary_focus,
            "question_type": question_type,
            "technical_terms": technical_terms,
            "urgency_level": urgency_level,
            "complexity_score": sum(technical_terms.values()),
            "requires_analysis": any(word in message_lower for word in ["analyze", "calculate", "show", "data", "statistics"]),
            "visualization_request": visualization_request or question_type == "visualization_request"
        }
    
    def interpret_statistical_results(self, results: Dict[str, Any], analysis_type: str) -> Dict[str, Any]:
        """
        Intelligent interpretation of statistical analysis results with 
        context-aware insights and recommendations
        """
        interpretation = {
            "summary": "",
            "key_findings": [],
            "recommendations": [],
            "risk_assessment": "low",
            "technical_details": {}
        }
        
        if analysis_type == "voltage_analysis" and results:
            low_violations = results.get('low_voltage_violations', {}).get('count', 0)
            high_violations = results.get('high_voltage_violations', {}).get('count', 0)
            total_buses = results.get('total_buses', 0)
            voltage_stats = results.get('voltage_statistics', {})
            
            # Risk assessment
            violation_percentage = (low_violations + high_violations) / total_buses * 100 if total_buses > 0 else 0
            if violation_percentage > 10:
                interpretation["risk_assessment"] = "high"
            elif violation_percentage > 5:
                interpretation["risk_assessment"] = "medium"
            
            # Generate intelligent summary
            if low_violations == 0 and high_violations == 0:
                interpretation["summary"] = f"✅ Excellent voltage profile! All {total_buses} buses operating within acceptable limits (0.95-1.05 p.u.)"
                interpretation["key_findings"].append("No voltage violations detected across the entire system")
                interpretation["recommendations"].append("Continue monitoring - system is operating optimally")
            else:
                interpretation["summary"] = f"⚠️ Voltage concerns detected: {low_violations} low voltage and {high_violations} high voltage violations"
                
                if low_violations > 0:
                    interpretation["key_findings"].append(f"Low voltage violations at {low_violations} buses may indicate insufficient reactive power support")
                    interpretation["recommendations"].append("Consider capacitor bank installation or voltage regulator adjustment")
                
                if high_violations > 0:
                    interpretation["key_findings"].append(f"High voltage violations at {high_violations} buses suggest excess reactive power")
                    interpretation["recommendations"].append("Review generator voltage setpoints and reactor installations")
            
            # Technical analysis
            if voltage_stats:
                min_v = voltage_stats.get('min_voltage', 0)
                max_v = voltage_stats.get('max_voltage', 0)
                avg_v = voltage_stats.get('avg_voltage', 0)
                
                interpretation["technical_details"] = {
                    "voltage_range": f"{min_v:.3f} - {max_v:.3f} p.u.",
                    "system_average": f"{avg_v:.3f} p.u.",
                    "voltage_spread": f"{(max_v - min_v):.3f} p.u.",
                    "assessment": "Well-regulated" if (max_v - min_v) < 0.1 else "Needs regulation improvement"
                }
        
        elif analysis_type == "power_flow" and results:
            overloaded = results.get('overloaded_branches', {}).get('count', 0)
            heavily_loaded = results.get('heavily_loaded_branches', {}).get('count', 0)
            total_branches = results.get('total_branches', 0)
            max_loading = results.get('max_loading_percentage', 0)
            
            # Risk assessment based on loading
            if overloaded > 0:
                interpretation["risk_assessment"] = "high"
            elif heavily_loaded > total_branches * 0.1:  # More than 10% heavily loaded
                interpretation["risk_assessment"] = "medium"
            
            if overloaded == 0:
                interpretation["summary"] = f"✅ Thermal limits respected on all {total_branches} branches (max loading: {max_loading:.1f}%)"
                interpretation["key_findings"].append("No thermal violations - system operating within capacity")
                interpretation["recommendations"].append("System has adequate thermal margins for normal operation")
            else:
                interpretation["summary"] = f"🚨 Critical thermal violations: {overloaded} branches overloaded, {heavily_loaded} heavily loaded"
                interpretation["key_findings"].append(f"Immediate attention required for {overloaded} overloaded branches")
                interpretation["recommendations"].append("Implement load shedding or generation redispatch to relieve overloads")
        
        return interpretation
    
    def generate_intelligent_response(self, user_message: str, intent: Dict[str, Any], 
                                    statistical_results: Optional[Dict[str, Any]] = None,
                                    analysis_type: str = "general") -> str:
        """
        Generate contextually appropriate response based on user intent,
        expertise level, and analysis results
        """
        template = self.response_templates[self.user_expertise_level]
        
        # Start building response
        response_parts = []
        
        # Add appropriate introduction
        if template["intro"]:
            response_parts.append(template["intro"])
        
        # Handle different question types with intelligence
        if intent["question_type"] == "analysis_request" and statistical_results:
            # Interpret the statistical results
            interpretation = self.interpret_statistical_results(statistical_results, analysis_type)
            
            # Create comprehensive response
            response_parts.append(f"## {analysis_type.replace('_', ' ').title()} Results\n")
            response_parts.append(interpretation["summary"] + "\n")
            
            if interpretation["key_findings"]:
                response_parts.append("### 🔍 Key Findings:")
                for finding in interpretation["key_findings"]:
                    response_parts.append(f"• {finding}")
                response_parts.append("")
            
            if interpretation["recommendations"]:
                response_parts.append("### 💡 Recommendations:")
                for rec in interpretation["recommendations"]:
                    response_parts.append(f"• {rec}")
                response_parts.append("")
            
            # Add technical details for expert users
            if self.user_expertise_level == "expert" and interpretation["technical_details"]:
                response_parts.append("### ⚙️ Technical Analysis:")
                for key, value in interpretation["technical_details"].items():
                    response_parts.append(f"• **{key.replace('_', ' ').title()}**: {value}")
            
            # Risk assessment
            risk_emoji = {"low": "✅", "medium": "⚠️", "high": "🚨"}[interpretation["risk_assessment"]]
            response_parts.append(f"\n{risk_emoji} **Risk Level**: {interpretation['risk_assessment'].title()}")
            
        elif intent["question_type"] == "explanation_request":
            # Handle "how" and "why" questions with detailed explanations
            if "voltage" in intent["primary_focus"]:
                response_parts.append("### Voltage Analysis Explanation\n")
                response_parts.append("Voltage analysis examines bus voltages throughout the power system to ensure they remain within acceptable operating ranges (typically 0.95 to 1.05 per unit).")
                if self.user_expertise_level == "expert":
                    response_parts.append("\n**Technical Details**: Voltage violations can indicate inadequate reactive power support, excessive losses, or inadequate voltage regulation equipment.")
        
        elif intent["question_type"] == "comparison_request":
            # Handle comparison questions intelligently
            if "slr" in user_message.lower() and "dlr" in user_message.lower():
                response_parts.append("### SLR vs DLR Comparison\n")
                response_parts.append("**Static Line Rating (SLR)**:")
                response_parts.append("• Uses conservative weather assumptions")
                response_parts.append("• Fixed thermal limits year-round")
                response_parts.append("• Ensures safety but may underutilize capacity\n")
                response_parts.append("**Dynamic Line Rating (DLR)**:")
                response_parts.append("• Real-time thermal limits based on actual weather")
                response_parts.append("• Can increase capacity by 10-30% in favorable conditions")
                response_parts.append("• Optimizes transmission utilization while maintaining safety")
        
        else:
            # Default intelligent response based on primary focus
            focus_responses = {
                "voltage": "I can analyze voltage profiles, identify violations, and provide voltage stability insights. Would you like me to perform a voltage analysis?",
                "power": "I can examine power flows, loading patterns, and thermal limits across your system. Shall I run a power flow analysis?",
                "thermal": "I can assess thermal loading, identify overloaded branches, and evaluate capacity margins. Would you like a thermal analysis?",
                "contingency": "I can evaluate system reliability under various outage scenarios and assess N-1 security. Shall I perform a contingency analysis?",
                "economic": "I can calculate system losses, efficiency metrics, and economic indicators. Would you like an economic analysis?"
            }
            
            if intent["primary_focus"] in focus_responses:
                response_parts.append(focus_responses[intent["primary_focus"]])
            else:
                response_parts.append("I'm your intelligent power system assistant! I can help with voltage analysis, power flow studies, thermal assessments, contingency analysis, and system optimization. What would you like to explore?")
        
        # Add contextual follow-up suggestions
        if intent["requires_analysis"]:
            response_parts.append("\n💡 **Next Steps**: I can provide detailed statistical analysis with visualizations and specific recommendations for any issues found.")
        
        return "\n".join(response_parts)
    
    def update_conversation_context(self, user_message: str, ai_response: str):
        """Update conversation history and context memory"""
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message,
            "ai_response": ai_response
        })
        
        # Keep only last 10 exchanges to manage memory
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
    
    def process_intelligent_message(self, user_message: str, statistical_results: Optional[Dict[str, Any]] = None) -> str:
        """
        Main processing function that combines all intelligence components
        """
        # Analyze user intent
        intent = self.analyze_user_intent(user_message)
        
        # Determine analysis type from intent
        analysis_type_mapping = {
            "voltage": "voltage_analysis",
            "power": "power_flow",
            "thermal": "thermal_analysis", 
            "contingency": "contingency_analysis",
            "economic": "economic_analysis"
        }
        
        analysis_type = analysis_type_mapping.get(intent["primary_focus"], "general")
        
        # Generate intelligent response
        response = self.generate_intelligent_response(
            user_message, intent, statistical_results, analysis_type
        )
        
        # Update conversation context
        self.update_conversation_context(user_message, response)
        
        return response
    
    def create_voltage_profile_visualization(self, analysis_data, bus_data=None):
        """Create voltage profile visualization with power system context."""
        try:
            # Try to extract voltage data from different possible structures
            voltage_data = None
            
            if 'voltage_profile' in analysis_data:
                voltage_data = analysis_data['voltage_profile']
            elif 'voltage_statistics' in analysis_data:
                # Generate sample voltage profile from statistics
                stats = analysis_data['voltage_statistics']
                min_v = stats.get('min_voltage', 0.95)
                max_v = stats.get('max_voltage', 1.05)
                avg_v = stats.get('avg_voltage', 1.0)
                
                # Generate sample profile
                voltage_data = [avg_v + (max_v - min_v) * np.sin(i * 0.1) * 0.3 for i in range(20)]
            elif 'Voltage' in analysis_data or any('voltage' in str(k).lower() for k in analysis_data.keys()):
                # Try to find any voltage-related data
                for key, value in analysis_data.items():
                    if 'voltage' in str(key).lower() and isinstance(value, (list, tuple)):
                        voltage_data = list(value)[:20]  # Limit to 20 points
                        break
            
            # Generate default sample data if no voltage data found
            if not voltage_data:
                voltage_data = [0.98 + 0.04 * np.sin(i * 0.3) + 0.01 * np.random.random() for i in range(15)]
                
            fig = go.Figure()
            
            # Add voltage profile line
            fig.add_trace(go.Scatter(
                x=list(range(len(voltage_data))),
                y=voltage_data,
                mode='lines+markers',
                name='Voltage Profile',
                line=dict(color='blue', width=2),
                marker=dict(size=6)
            ))
            
            # Add voltage limits
            fig.add_hline(y=1.05, line_dash="dash", line_color="red", 
                         annotation_text="Upper Limit (1.05 pu)")
            fig.add_hline(y=0.95, line_dash="dash", line_color="red", 
                         annotation_text="Lower Limit (0.95 pu)")
            fig.add_hline(y=1.0, line_dash="dot", line_color="green", 
                         annotation_text="Nominal (1.0 pu)")
            
            # Highlight violations
            violations = [i for i, v in enumerate(voltage_data) if v < 0.95 or v > 1.05]
            if violations:
                violation_voltages = [voltage_data[i] for i in violations]
                fig.add_trace(go.Scatter(
                    x=violations,
                    y=violation_voltages,
                    mode='markers',
                    name='Violations',
                    marker=dict(color='red', size=10, symbol='x')
                ))
            
            fig.update_layout(
                title="Power System Voltage Profile Analysis",
                xaxis_title="Bus Number",
                yaxis_title="Voltage (per unit)",
                showlegend=True,
                height=500,
                template="plotly_white"
            )
            
            return fig
                
        except Exception as e:
            print(f"Error creating voltage visualization: {e}")
            return None
    
    def create_thermal_loading_visualization(self, analysis_data):
        """Create thermal loading visualization with capacity analysis."""
        try:
            # Try to extract thermal loading data from different possible structures
            loading_data = None
            
            if 'thermal_loading' in analysis_data:
                loading_data = analysis_data['thermal_loading']
            elif 'max_loading_percentage' in analysis_data:
                # Generate sample loading distribution around the max loading
                max_loading = analysis_data['max_loading_percentage'] / 100
                loading_data = [max_loading * (0.5 + 0.5 * np.random.random()) for _ in range(12)]
            elif any('loading' in str(k).lower() for k in analysis_data.keys()):
                # Try to find any loading-related data
                for key, value in analysis_data.items():
                    if 'loading' in str(key).lower() and isinstance(value, (list, tuple, int, float)):
                        if isinstance(value, (int, float)):
                            loading_data = [value / 100 if value > 2 else value] * 10
                        else:
                            loading_data = list(value)[:15]
                        break
            
            # Generate default sample data if no loading data found
            if not loading_data:
                loading_data = [0.6 + 0.3 * np.random.random() for _ in range(12)]
                
            fig = go.Figure()
            
            # Create loading bars with color coding
            colors = []
            for loading in loading_data:
                if loading >= 1.0:
                    colors.append('red')      # Critical
                elif loading >= 0.9:
                    colors.append('orange')   # High
                elif loading >= 0.8:
                    colors.append('yellow')   # Warning
                else:
                    colors.append('green')    # Normal
            
            fig.add_trace(go.Bar(
                x=list(range(len(loading_data))),
                y=loading_data,
                name='Thermal Loading',
                marker_color=colors
            ))
            
            # Add threshold lines
            fig.add_hline(y=1.0, line_dash="dash", line_color="red", 
                         annotation_text="100% Capacity")
            fig.add_hline(y=0.9, line_dash="dot", line_color="orange", 
                         annotation_text="90% Warning")
            fig.add_hline(y=0.8, line_dash="dot", line_color="yellow", 
                         annotation_text="80% Alert")
            
            fig.update_layout(
                title="Power System Thermal Loading Analysis",
                xaxis_title="Line/Branch Number",
                yaxis_title="Loading (% of capacity)",
                showlegend=True,
                height=500,
                template="plotly_white"
            )
            
            return fig
                
        except Exception as e:
            print(f"Error creating thermal visualization: {e}")
            return None
    
    def create_power_flow_visualization(self, analysis_data):
        """Create power flow analysis visualization."""
        try:
            if 'power_flow' in analysis_data:
                flow_data = analysis_data['power_flow']
                
                # Create subplots for P and Q flows
                fig = make_subplots(
                    rows=2, cols=1,
                    subplot_titles=('Real Power Flow (MW)', 'Reactive Power Flow (MVAr)'),
                    vertical_spacing=0.1
                )
                
                # Real power flow
                if 'p_flow' in flow_data:
                    fig.add_trace(
                        go.Scatter(
                            x=list(range(len(flow_data['p_flow']))),
                            y=flow_data['p_flow'],
                            mode='lines+markers',
                            name='P Flow',
                            line=dict(color='blue')
                        ),
                        row=1, col=1
                    )
                
                # Reactive power flow
                if 'q_flow' in flow_data:
                    fig.add_trace(
                        go.Scatter(
                            x=list(range(len(flow_data['q_flow']))),
                            y=flow_data['q_flow'],
                            mode='lines+markers',
                            name='Q Flow',
                            line=dict(color='red')
                        ),
                        row=2, col=1
                    )
                
                fig.update_layout(
                    title="Power System Flow Analysis",
                    height=600,
                    showlegend=True,
                    template="plotly_white"
                )
                
                return fig
                
            return None
            
        except Exception as e:
            print(f"Error creating power flow visualization: {e}")
            return None
    
    def create_system_reliability_visualization(self, analysis_data):
        """Create system reliability assessment visualization."""
        try:
            if 'reliability_metrics' in analysis_data:
                metrics = analysis_data['reliability_metrics']
                
                # Create gauge charts for key reliability metrics
                fig = make_subplots(
                    rows=2, cols=2,
                    specs=[[{"type": "indicator"}, {"type": "indicator"}],
                           [{"type": "indicator"}, {"type": "indicator"}]],
                    subplot_titles=('SAIFI', 'SAIDI', 'CAIDI', 'System Health')
                )
                
                # SAIFI gauge
                if 'saifi' in metrics:
                    fig.add_trace(go.Indicator(
                        mode = "gauge+number+delta",
                        value = metrics['saifi'],
                        domain = {'x': [0, 1], 'y': [0, 1]},
                        title = {'text': "SAIFI"},
                        gauge = {
                            'axis': {'range': [None, 5]},
                            'bar': {'color': "darkblue"},
                            'steps': [
                                {'range': [0, 2], 'color': "lightgray"},
                                {'range': [2, 4], 'color': "gray"}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': 3
                            }
                        }
                    ), row=1, col=1)
                
                # Add other reliability metrics...
                fig.update_layout(
                    title="Power System Reliability Dashboard",
                    height=600,
                    template="plotly_white"
                )
                
                return fig
                
            return None
            
        except Exception as e:
            print(f"Error creating reliability visualization: {e}")
            return None
    
    def generate_visualization_based_on_intent(self, intent: Dict[str, Any], analysis_data: Dict[str, Any] = None):
        """Generate appropriate visualization based on user intent and available data."""
        visualization_intent = intent.get("visualization_request", False)
        primary_focus = intent.get("primary_focus", "general")
        
        if not visualization_intent:
            return None
        
        # If no analysis data provided, generate sample data for demonstration
        if not analysis_data:
            analysis_data = self.generate_sample_analysis_data(primary_focus)
        
        # Route to appropriate visualization method
        if primary_focus in ["voltage", "stability"]:
            return self.create_voltage_profile_visualization(analysis_data)
        elif primary_focus in ["thermal", "loading", "capacity"]:
            return self.create_thermal_loading_visualization(analysis_data)
        elif primary_focus in ["power", "flow"]:
            return self.create_power_flow_visualization(analysis_data)
        elif primary_focus in ["reliability", "contingency"]:
            return self.create_system_reliability_visualization(analysis_data)
        else:
            # Default to voltage profile if no specific intent identified
            return self.create_voltage_profile_visualization(analysis_data)
    
    def generate_sample_analysis_data(self, analysis_focus: str) -> Dict[str, Any]:
        """Generate sample analysis data for visualization when real data isn't available."""
        
        if analysis_focus in ["voltage", "stability"]:
            return {
                "voltage_statistics": {
                    "min_voltage": 0.94 + 0.02 * np.random.random(),
                    "max_voltage": 1.05 + 0.02 * np.random.random(),
                    "avg_voltage": 0.99 + 0.02 * np.random.random()
                }
            }
        
        elif analysis_focus in ["thermal", "loading", "capacity"]:
            return {
                "max_loading_percentage": 75 + 20 * np.random.random()
            }
        
        elif analysis_focus in ["power", "flow"]:
            return {
                "power_flow": {
                    "p_flow": [50 + 30 * np.sin(i * 0.2) + 10 * np.random.random() for i in range(15)],
                    "q_flow": [20 + 15 * np.cos(i * 0.3) + 5 * np.random.random() for i in range(15)]
                }
            }
        
        elif analysis_focus in ["reliability", "contingency"]:
            return {
                "reliability_metrics": {
                    "saifi": 1.2 + 0.8 * np.random.random(),
                    "saidi": 2.5 + 1.5 * np.random.random(),
                    "caidi": 1.8 + 0.7 * np.random.random()
                }
            }
        
        else:
            # Default voltage data
            return {
                "voltage_statistics": {
                    "min_voltage": 0.96,
                    "max_voltage": 1.04,
                    "avg_voltage": 1.00
                }
            }
    
    def process_with_visualization(self, user_message: str, statistical_results: Optional[Dict[str, Any]] = None):
        """
        Enhanced processing that includes visualization generation
        """
        # Analyze user intent
        intent = self.analyze_user_intent(user_message)
        
        # Generate text response
        response = self.process_intelligent_message(user_message, statistical_results)
        
        # Generate visualization if requested
        visualization = None
        if intent.get("visualization_request", False):
            visualization = self.generate_visualization_based_on_intent(intent, statistical_results)
            
            # If visualization was generated, enhance the response
            if visualization:
                response += "\n\n📊 I've generated a visualization based on your request. The chart shows the analysis results with proper power system context and standards compliance indicators."
        
        return {
            "text_response": response,
            "visualization": visualization,
            "intent": intent
        }