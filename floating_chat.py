"""
Floating chat component for the power system visualization interface
with statistical analysis capabilities
"""

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import networkx as nx
import json
import os
import plotly.graph_objects as go
import sys
import importlib.util

# Try to import from power_stats module
try:
    from power_stats import (
        get_database_stats, get_graph_stats, generate_comparison_plot, 
        generate_graph_plot, analyze_system_resilience, format_statistical_summary,
        perform_advanced_analysis  # Import our new advanced analysis function
    )
    print("Successfully imported from power_stats")
except ImportError:
    print("Error importing from power_stats - using fallback functions")
    
# Try to import mock_llm module for assistant factory
try:
    from mock_llm import get_assistant
    MOCK_LLM_AVAILABLE = True
    print("Successfully imported get_assistant factory from mock_llm")
except ImportError:
    MOCK_LLM_AVAILABLE = False
    print("Error importing get_assistant from mock_llm - assistant factory unavailable")
    
# Try to import LLM and Llama modules
try:
    from llm_assistant import LLMEnhancedAssistant
    LLM_AVAILABLE = True
    print("Successfully imported LLMEnhancedAssistant")
except ImportError:
    LLM_AVAILABLE = False
    print("LLMEnhancedAssistant not available")

# Set LLAMA_AVAILABLE to False since we removed llama_assistant.py
LLAMA_AVAILABLE = False

# Import enhanced intelligent chat engine
try:
    from intelligent_chat_engine import PowerSystemIntelligentAssistant
    INTELLIGENT_CHAT_AVAILABLE = True
    print("✅ Enhanced intelligent chat engine imported successfully")
except ImportError as e:
    INTELLIGENT_CHAT_AVAILABLE = False
    print(f"⚠️ Enhanced chat engine not available: {e}")

# Import power system statistical components
try:
    from power_system_statistical_analyzer import PowerSystemStatisticalAnalyzer  
    from power_system_statistical_visualizer import PowerSystemStatisticalVisualizer
    print("✅ Statistical analyzer imported successfully")
    STATISTICAL_ANALYSIS_AVAILABLE = True
except ImportError as e:
    print(f"❌ Statistical analysis not available: {e}")
    STATISTICAL_ANALYSIS_AVAILABLE = False

# Fallback simple functions if power_stats module can't be imported
def get_database_stats(db_path, **kwargs):
    return {"error": "Statistical module not available"}
    
def get_graph_stats(graph):
    return {"error": "Statistical module not available"}
    
def generate_comparison_plot(db_stats):
    return go.Figure()
    
def generate_graph_plot(graph):
    return go.Figure()
    
def analyze_system_resilience(db_stats, graph_stats):
    from dash import html
    return html.Div("Statistical analysis module not available.")
    
def format_statistical_summary(db_stats, graph_stats=None):
    from dash import html
    return html.Div([
        html.H4("Statistical Analysis"),
        html.P("The detailed statistical analysis module is not currently available."),
        html.P("Please check that the power_stats.py file is properly installed.")
    ])

def create_ai_message(text, timestamp, visualization=None):
    """Helper function to create AI message component with optional visualization"""
    message_components = [
        html.Div([
            html.Strong("🤖 Assistant"),
            html.Small(f" • {timestamp}", className="text-muted ms-2")
        ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"}),
        html.P(text, style={"whiteSpace": "pre-wrap"})
    ]
    
    # Add visualization if provided
    if visualization:
        try:
            from dash import dcc
            message_components.append(
                html.Div([
                    html.H6("📊 Generated Visualization", style={"marginTop": "15px", "marginBottom": "10px"}),
                    dcc.Graph(
                        figure=visualization,
                        style={"height": "400px"}
                    )
                ])
            )
        except Exception as e:
            print(f"Error adding visualization to message: {e}")
            message_components.append(
                html.Div([
                    html.P("📊 Visualization was generated but could not be displayed.", 
                          style={"color": "orange", "fontStyle": "italic"})
                ])
            )
    
    return html.Div(message_components, style={
        "backgroundColor": "#e3f2fd", 
        "padding": "15px", 
        "borderRadius": "5px", 
        "marginBottom": "10px",
        "marginRight": "50px"
    })

def create_floating_chat_component():
    """
    Creates a floating chat component that can be toggled on/off
    and appears in the bottom left corner of the visualization
    with statistical analysis capabilities
    """
    return html.Div(
        [
            # Statistical Analysis Modal
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Power System Statistical Analysis")),
                    dbc.ModalBody([
                        # Tabs for different analysis views
                        dbc.Tabs([
                            dbc.Tab(
                                [
                                    html.Div(id="stats-summary-text", className="mt-3",
                                            style={"maxHeight": "400px", "overflowY": "auto"}),
                                ],
                                label="Summary",
                                tab_id="stats-summary-tab"
                            ),
                            dbc.Tab(
                                [
                                    dcc.Loading(
                                        dcc.Graph(id="stats-comparison-plot", style={"height": "500px"})
                                    )
                                ],
                                label="Data Comparison",
                                tab_id="stats-comparison-tab"
                            ),
                            dbc.Tab(
                                [
                                    dcc.Loading(
                                        dcc.Graph(id="stats-graph-plot", style={"height": "500px"})
                                    )
                                ],
                                label="Network Analysis",
                                tab_id="stats-graph-tab"
                            ),
                            dbc.Tab(
                                [
                                    html.Div(id="advanced-analysis-content", className="mt-3",
                                            style={"maxHeight": "600px", "overflowY": "auto"}),
                                ],
                                label="Advanced Analysis",
                                tab_id="advanced-analysis-tab"
                            ),
                            dbc.Tab(
                                [
                                    html.Div(id="system-resilience", className="mt-3")
                                ],
                                label="Resilience Assessment",
                                tab_id="stats-resilience-tab"
                            )
                        ], id="stats-tabs"),
                    ]),
                    dbc.ModalFooter(
                        dbc.Button("Close", id="stats-modal-close", className="ms-auto")
                    ),
                ],
                id="stats-modal",
                size="xl",
                is_open=False,
            ),
            
            # Chat toggle button
            html.Div(
                html.Button(
                    "💬", 
                    id="floating-chat-toggle",
                    n_clicks=0,
                    style={
                        "backgroundColor": "#0D8767",
                        "color": "white",
                        "border": "none",
                        "borderRadius": "50%",
                        "width": "50px",
                        "height": "50px",
                        "fontSize": "20px",
                        "cursor": "pointer",
                        "boxShadow": "0 2px 5px rgba(0,0,0,0.2)",
                        "zIndex": "1000"
                    }
                ),
                style={
                    "position": "fixed",
                    "bottom": "20px",
                    "left": "20px",  # Positioned in the bottom left corner
                    "zIndex": "1000"
                }
            ),
            
            # Chat panel
            html.Div(
                [
                    # Chat header
                    html.Div(
                        [
                            html.H5("Power System Assistant", style={"margin": "0", "color": "white"}),
                            html.Button(
                                "✕", 
                                id="floating-chat-close",
                                style={
                                    "backgroundColor": "transparent",
                                    "color": "white",
                                    "border": "none",
                                    "fontSize": "16px",
                                    "cursor": "pointer"
                                }
                            )
                        ],
                        style={
                            "display": "flex",
                            "justifyContent": "space-between",
                            "alignItems": "center",
                            "padding": "10px 15px",
                            "backgroundColor": "#0D8767",
                            "borderRadius": "10px 10px 0 0"
                        }
                    ),
                    
                    # Chat messages area
                    html.Div(
                        id="floating-chat-messages",
                        children=[
                            # Initial welcome message
                            html.Div([
                                html.Div([
                                    html.Strong("🤖 AI Assistant"),
                                    html.Div([
                                        "How can I help with your power system visualization?",
                                    ])
                                ], className="ai-message")
                            ], className="chat-message")
                        ],
                        style={
                            "height": "250px",
                            "overflowY": "auto",
                            "padding": "15px",
                            "backgroundColor": "white",
                            "display": "flex",
                            "flexDirection": "column"
                        }
                    ),
                    
                    # Status indicator
                    html.Div(
                        [
                            html.Span("●", id="floating-ai-status-indicator", style={"color": "red"}),
                            html.Span(" AI Assistant currently offline. Click to initialize.", 
                                    id="floating-ai-status-text",
                                    className="ms-1 small text-muted")
                        ],
                        id="floating-ai-status-container",
                        style={
                            "margin": "10px 15px", 
                            "cursor": "pointer", 
                            "padding": "8px 12px",
                            "border": "1px solid #ddd",
                            "borderRadius": "4px",
                            "backgroundColor": "#f8f9fa",
                            "display": "inline-block"
                        }
                    ),
                    
                    # Chat input area
                    html.Div(
                        [
                            dbc.Input(
                                id="floating-chat-input",
                                placeholder="Ask about the power system...",
                                type="text",
                                style={"borderRadius": "20px 0 0 20px"}
                            ),
                            dbc.Button(
                                "Send", 
                                id="floating-chat-send-btn",
                                color="primary",
                                style={"borderRadius": "0 20px 20px 0"}
                            )
                        ],
                        style={
                            "display": "flex",
                            "padding": "10px 15px 15px 15px",
                            "backgroundColor": "white",
                            "borderTop": "1px solid #eee",
                            "borderRadius": "0 0 10px 10px"
                        }
                    )
                ],
                id="floating-chat-panel",
                style={
                    "position": "fixed",
                    "bottom": "80px",
                    "left": "20px",  # Positioned in the bottom left corner
                    "width": "350px",
                    "borderRadius": "10px",
                    "boxShadow": "0 5px 15px rgba(0,0,0,0.2)",
                    "zIndex": "1000",
                    "display": "none"  # Initially hidden
                }
            )
        ]
    )

# Callbacks for the floating chat
def register_floating_chat_callbacks(app):
    """
    Register the callbacks for the floating chat component
    """
    from dash.dependencies import Input, Output, State
    from dash import callback_context, no_update
    
    # Toggle chat visibility
    @app.callback(
        Output("floating-chat-panel", "style"),
        [Input("floating-chat-toggle", "n_clicks"),
         Input("floating-chat-close", "n_clicks")],
        [State("floating-chat-panel", "style")]
    )
    def toggle_chat_visibility(toggle_clicks, close_clicks, current_style):
        """Toggle the visibility of the chat panel"""
        if not callback_context.triggered:
            return current_style
            
        trigger_id = callback_context.triggered[0]["prop_id"].split(".")[0]
        
        # Copy the current style
        new_style = dict(current_style)
        
        # Toggle button clicked to show chat
        if trigger_id == "floating-chat-toggle" and toggle_clicks:
            new_style["display"] = "block"
            
        # Close button clicked to hide chat
        elif trigger_id == "floating-chat-close" and close_clicks:
            new_style["display"] = "none"
            
        return new_style
    
    # Initialize AI assistant
    @app.callback(
        Output("floating-ai-status-container", "children"),
        [Input("floating-chat-send-btn", "n_clicks"),
         Input("floating-ai-status-container", "n_clicks")]
    )
    def update_floating_ai_status(send_clicks, status_clicks):
        """Update AI status indicator after interaction"""
        if not callback_context.triggered:
            return [
                html.Span("●", id="floating-ai-status-indicator", style={"color": "red"}),
                html.Span(" AI Assistant currently offline. Click to initialize.", 
                        id="floating-ai-status-text",
                        className="ms-1 small text-muted")
            ]
            
        # Get which input triggered the callback
        triggered_id = None
        if callback_context.triggered:
            triggered_id = callback_context.triggered[0]['prop_id'].split('.')[0]
        
        # If either button was clicked or status was clicked, initialize AI
        if (triggered_id == "floating-chat-send-btn" and send_clicks and send_clicks > 0) or \
           (triggered_id == "floating-ai-status-container" and status_clicks and status_clicks > 0):
            # Try to load the best available AI assistant
            try:
                import os
                import json
                
                # Try to get the database path from config
                db_path = "data/data.db"  # Default path
                if os.path.exists("config.json"):
                    with open("config.json", "r") as f:
                        config = json.load(f)
                        db_path = config.get("database_path", db_path)
                
                # Check for LLM configuration from environment
                use_mock_llm = os.environ.get("DLR_MOCK_LLM") == "1"
                use_llama = os.environ.get("DLR_USE_LLAMA") == "1"
                
                # Try to use the best available assistant
                try:
                    # Get the appropriate assistant
                    print(f"Initializing AI Assistant with database path: {db_path}")
                    print(f"Configuration - Mock LLM: {use_mock_llm}, Llama: {use_llama}")
                    
                    assistant = None
                    assistant_type = "Unknown"
                    
                    if MOCK_LLM_AVAILABLE:
                        assistant = get_assistant(db_path, use_mock_llm=use_mock_llm, use_llama=use_llama)
                        assistant_type = type(assistant).__name__
                    elif use_llama and LLAMA_AVAILABLE:
                        print("Llama assistant not currently available")
                        assistant = None
                        assistant_type = "Basic"
                    elif LLM_AVAILABLE:
                        api_key = os.environ.get("OPENAI_API_KEY")
                        
                        # If no environment variable, try to read from config file
                        if not api_key:
                            try:
                                if os.path.exists("config.json"):
                                    with open("config.json", "r") as f:
                                        config = json.load(f)
                                        api_key = config.get("ai_settings", {}).get("openai_api_key")
                                        if api_key and api_key != "REPLACE_WITH_YOUR_API_KEY":
                                            print("Using OpenAI API key from config.json")
                                        else:
                                            api_key = None
                            except Exception as e:
                                print(f"Failed to read API key from config: {e}")
                        
                        if api_key:
                            model = os.environ.get("DLR_LLM_MODEL")
                            if not model:
                                try:
                                    if os.path.exists("config.json"):
                                        with open("config.json", "r") as f:
                                            config = json.load(f)
                                            model = config.get("ai_settings", {}).get("model", "gpt-3.5-turbo")
                                    else:
                                        model = "gpt-3.5-turbo"
                                except:
                                    model = "gpt-3.5-turbo"
                            
                            assistant = LLMEnhancedAssistant(db_path, api_key=api_key, model=model)
                            assistant_type = "LLMEnhancedAssistant"
                        else:
                            print("No OpenAI API key found in environment or config")
                            assistant_type = "Basic"
                    
                    if "Llama" in assistant_type:
                        return [
                            html.Span("●", id="floating-ai-status-indicator", style={"color": "blue"}),
                            html.Span(" AI Assistant online (Llama mode)", 
                                    id="floating-ai-status-text",
                                    className="ms-1 small text-muted")
                        ]
                    elif "LLM" in assistant_type or "Mock" in assistant_type:
                        return [
                            html.Span("●", id="floating-ai-status-indicator", style={"color": "green"}),
                            html.Span(" AI Assistant online (LLM mode)", 
                                    id="floating-ai-status-text",
                                    className="ms-1 small text-muted")
                        ]
                except ImportError:
                    # Fall back to LLM assistant if available
                    if LLM_AVAILABLE:
                        from llm_assistant import LLMEnhancedAssistant
                        print(f"Initializing LLM Assistant with database path: {db_path}")
                        
                        return [
                            html.Span("●", id="floating-ai-status-indicator", style={"color": "green"}),
                            html.Span(" LLM AI Assistant online", 
                                    id="floating-ai-status-text",
                                    className="ms-1 small text-muted")
                        ]
                    else:
                        # No AI assistant available
                        return [
                            html.Span("●", id="floating-ai-status-indicator", style={"color": "orange"}),
                            html.Span(" Statistical Analysis Only", 
                                    id="floating-ai-status-text",
                                    className="ms-1 small text-muted")
                        ]
            except Exception as e:
                print(f"Failed to load full AI assistant: {e}")
                pass
                
            # Fall back to basic mode
            print("Initializing Floating AI Assistant in basic mode...")
            return [
                html.Span("●", id="floating-ai-status-indicator", style={"color": "green"}),
                html.Span(" AI Assistant online (basic mode)", 
                        id="floating-ai-status-text",
                        className="ms-1 small text-muted")
            ]
            
        # Default state
        return [
            html.Span("●", id="floating-ai-status-indicator", style={"color": "red"}),
            html.Span(" AI Assistant currently offline. Click to initialize.", 
                    id="floating-ai-status-text",
                    className="ms-1 small text-muted")
        ]
    
    # Handle chat messages and statistical analysis requests
    @app.callback(
        [Output("floating-chat-messages", "children"),
         Output("floating-chat-input", "value"),
         Output("stats-modal", "is_open"),
         Output("stats-tabs", "active_tab")],
        [Input("floating-chat-send-btn", "n_clicks"),
         Input("floating-chat-input", "n_submit"),
         Input("stats-modal-close", "n_clicks")],
        [State("floating-chat-input", "value"),
         State("floating-chat-messages", "children"),
         State("stats-modal", "is_open"),
         State("stats-tabs", "active_tab")]
    )
    def handle_floating_chat_message(send_clicks, input_submit, close_modal, message, current_messages, modal_open, active_tab="tab-1"):
        """Handle new chat messages and statistical analysis requests"""
        from dash import no_update
        
        global session_store  # Declare global at the beginning
        
        # Debug output
        print(f"=== CHAT DEBUG ===")
        print(f"Chat callback triggered with message: '{message}'")
        
        # Get triggered component ID consistently
        triggered_id = None
        if callback_context.triggered:
            triggered_id = callback_context.triggered[0]['prop_id'].split('.')[0]
        print(f"Triggered ID: {triggered_id}")
        print(f"Send clicks: {send_clicks}, Input submit: {input_submit}")
        print(f"Current messages length: {len(current_messages) if current_messages else 0}")
        
        # Check if modal close button was clicked
        if triggered_id == "stats-modal-close":
            print("Modal close triggered")
            return no_update, no_update, False, no_update
        
        # Check if send button or input submit was triggered
        if triggered_id not in ["floating-chat-send-btn", "floating-chat-input"]:
            print(f"Callback not triggered by chat input, triggered by: {triggered_id}")
            return no_update, no_update, modal_open, no_update
        
        # Check for empty message
        if not message or not message.strip():
            print("Empty message detected")
            return no_update, no_update, modal_open, no_update
        
        # Format the current time
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M")
        
        # Check if this is a statistical analysis request or advanced analytics request
        message_lower = message.lower()
        is_stats_request = any(keyword in message_lower for keyword in [
            "statistics", "statistical", "stats", "analyze", "analysis", "report",
            "summary", "compare", "comparison", "show me data", "visualization"
        ])

        # Check for advanced analysis requests
        is_advanced_request = any(keyword in message_lower for keyword in [
            "advanced", "clustering", "cluster", "anomaly", "anomalies", "detect",
            "correlation", "forecast", "predict", "pattern", "optimization", "optimize",
            "reliability", "congestion", "assessment", "deep dive", "detailed"
        ])
          
        # Check for specialized visualization requests
        is_visualization_request = any(keyword in message_lower for keyword in [
            "visualize", "plot", "chart", "graph", "diagram", "display", "show",
            "single line diagram", "bus voltage", "branch loading", "time-series",
            "heat map", "power flow", "voltage stability", "generation stack", 
            "risk map", "contingency", "correlation"
        ])
        
        # Add user message
        user_msg = html.Div([
            html.Div([
                html.Strong("You"),
                html.Small(f" • {timestamp}", className="text-muted ms-2")
            ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"}),
            html.P(message, style={"whiteSpace": "pre-wrap"})
        ], style={
            "backgroundColor": "#F0F2F5", 
            "padding": "15px", 
            "borderRadius": "5px", 
            "marginBottom": "10px",
            "marginLeft": "50px"
        })
        
        updated_messages = current_messages + [user_msg]
        
        # Generate AI response with more varied responses

        # Handle statistical, advanced analysis, and visualization requests
        if is_stats_request or is_advanced_request or is_visualization_request:
            # Determine the type of analysis requested
            analysis_type = "standard"
            
            # Try to use statistical analyzer for enhanced analysis
            try:
                # Get database path for analyzer initialization
                db_path = "data.db"  # Default path in project root
                if os.path.exists("config.json"):
                    import json
                    with open("config.json", "r") as f:
                        config = json.load(f)
                        db_path = config.get("database_path", db_path)
                
                # Ensure database file exists
                if not os.path.exists(db_path):
                    # Try alternative paths
                    alternative_paths = ["data.db", "./data.db", "C:/Projects/dlr-database-project/data.db"]
                    for alt_path in alternative_paths:
                        if os.path.exists(alt_path):
                            db_path = alt_path
                            break
                
                # Import and initialize the statistical analyzer
                try:
                    from power_system_statistical_analyzer import PowerSystemStatisticalAnalyzer
                    from power_system_statistical_visualizer import PowerSystemStatisticalVisualizer
                    
                    # Initialize statistical analyzer with debug info
                    print(f"🔍 Initializing statistical analyzer with database: {db_path}")
                    print(f"🔍 Database exists: {os.path.exists(db_path)}")
                    
                    stat_analyzer = PowerSystemStatisticalAnalyzer(db_path)
                    stat_visualizer = PowerSystemStatisticalVisualizer(db_path)
                    
                    print("✅ Successfully initialized PowerSystemStatisticalAnalyzer and Visualizer")
                    stat_visualizer = PowerSystemStatisticalVisualizer(db_path)
                    
                    print("Successfully initialized PowerSystemStatisticalAnalyzer and Visualizer")
                    
                    # Use flexible statistical analyzer to perform analysis based on available data
                    statistical_results = None
                    visualization_data = None
                    
                    # Determine specific analysis based on keywords in message
                    if any(word in message_lower for word in ["voltage", "violation", "overvoltage", "undervoltage", "v_min", "v_max"]):
                        print("🔍 Performing voltage violation analysis...")
                        analysis_type = "voltage_analysis"
                        try:
                            statistical_results = stat_analyzer.voltage_violation_analysis()
                            print(f"✅ Voltage analysis completed successfully")
                        except Exception as e:
                            print(f"Error in voltage analysis: {e}")
                            statistical_results = {"error": f"Voltage analysis error: {str(e)}"}
                    
                    elif any(word in message_lower for word in ["power flow", "branch", "loading", "overload", "congestion"]):
                        print("🔍 Performing power flow analysis...")
                        analysis_type = "power_flow"
                        try:
                            statistical_results = stat_analyzer.power_flow_analysis()
                            print(f"✅ Power flow analysis completed successfully")
                        except Exception as e:
                            print(f"Error in power flow analysis: {e}")
                            statistical_results = {"error": f"Power flow analysis error: {str(e)}"}
                    
                    elif any(word in message_lower for word in ["contingency", "outage", "n-1", "reliability", "impact"]):
                        print("🔍 Performing contingency impact analysis...")
                        analysis_type = "contingency"
                        try:
                            statistical_results = stat_analyzer.contingency_impact_analysis()
                            print(f"✅ Contingency analysis completed successfully")
                        except Exception as e:
                            print(f"Error in contingency analysis: {e}")
                            statistical_results = {"error": f"Contingency analysis error: {str(e)}"}
                    
                    elif any(word in message_lower for word in ["generation", "generator", "dispatch", "gen", "production"]):
                        print("🔍 Performing generation dispatch analysis...")
                        analysis_type = "generation"
                        try:
                            statistical_results = stat_analyzer.generation_dispatch_analysis()
                            print(f"✅ Generation analysis completed successfully")
                        except Exception as e:
                            print(f"Error in generation analysis: {e}")
                            statistical_results = {"error": f"Generation analysis error: {str(e)}"}
                    
                    elif any(word in message_lower for word in ["load", "demand", "consumption", "customer", "distribution"]):
                        print("🔍 Performing load distribution analysis...")
                        analysis_type = "load_distribution"
                        try:
                            statistical_results = stat_analyzer.load_distribution_analysis()
                            print(f"✅ Load distribution analysis completed successfully")
                        except Exception as e:
                            print(f"Error in load analysis: {e}")
                            statistical_results = {"error": f"Load analysis error: {str(e)}"}
                    
                    elif any(word in message_lower for word in ["loss", "losses", "efficiency", "balance", "mismatch"]):
                        print("🔍 Performing system losses analysis...")
                        analysis_type = "losses"
                        try:
                            statistical_results = stat_analyzer.system_losses_analysis()
                            print(f"✅ System losses analysis completed successfully")
                        except Exception as e:
                            print(f"Error in losses analysis: {e}")
                            statistical_results = {"error": f"Losses analysis error: {str(e)}"}
                    
                    elif any(word in message_lower for word in ["health", "check", "status", "overview", "assessment"]):
                        print("🔍 Performing system health check...")
                        analysis_type = "health_check"
                        try:
                            statistical_results = stat_analyzer.get_system_health_check()
                            print(f"✅ Health check completed successfully")
                        except Exception as e:
                            print(f"Error in health check: {e}")
                            statistical_results = {"error": f"Health check error: {str(e)}"}
                    
                    elif any(word in message_lower for word in ["summary", "overview", "system", "basic", "general"]):
                        print("🔍 Performing basic system summary...")
                        analysis_type = "system_summary"
                        try:
                            statistical_results = stat_analyzer.basic_system_summary()
                            print(f"✅ System summary completed successfully")
                        except Exception as e:
                            print(f"Error in system summary: {e}")
                            statistical_results = {"error": f"System summary error: {str(e)}"}
                    
                    else:
                        # Default to comprehensive basic analysis suite
                        print("🔍 Performing comprehensive basic analysis suite...")
                        analysis_type = "comprehensive"
                        try:
                            # Run the basic analysis suite with all available analyses
                            statistical_results = stat_analyzer.basic_analysis_suite()
                            
                            if not statistical_results or 'error' in statistical_results:
                                # If suite fails, try individual components
                                print("🔄 Suite failed, trying individual analyses...")
                                summary = stat_analyzer.basic_system_summary()
                                voltage = stat_analyzer.voltage_violation_analysis()
                                health = stat_analyzer.get_system_health_check()
                                
                                statistical_results = {
                                    "summary": summary,
                                    "voltage_analysis": voltage,
                                    "health_check": health,
                                    "analysis_type": "fallback_comprehensive"
                                }
                            
                            print(f"✅ Comprehensive analysis completed successfully")
                                
                        except Exception as e:
                            print(f"Error in comprehensive analysis: {e}")
                            statistical_results = {"error": f"Comprehensive analysis error: {str(e)}"}
                    
                    # Store results for the modal
                    if "session_store" not in globals():
                        global session_store
                        session_store = {}
                    
                    session_store["statistical_results"] = statistical_results
                    session_store["analysis_type"] = analysis_type
                    session_store["use_advanced_statistics"] = True
                    
                except ImportError as ie:
                    print(f"Could not import statistical analyzer: {ie}")
                    # Fall back to original analysis approach
                    analysis_type = "standard"
                
            except Exception as e:
                print(f"Error in statistical analysis initialization: {e}")
                analysis_type = "standard"
            
            # Try to use LLM for intent classification if advanced statistical analysis failed
            if analysis_type == "standard":
                try:
                    # Try to get the best available assistant for intent classification
                    import os
                    
                    # Check for LLM configuration from environment
                    use_mock_llm = os.environ.get("DLR_MOCK_LLM") == "1"
                    use_llama = os.environ.get("DLR_USE_LLAMA") == "1"
                    
                    # Use the factory function if available
                    intent_assistant = None
                    
                    if MOCK_LLM_AVAILABLE:
                        intent_assistant = get_assistant(db_path, use_mock_llm=use_mock_llm, use_llama=use_llama)
                    elif use_llama and LLAMA_AVAILABLE:
                        print("Llama assistant not currently available")
                        intent_assistant = None
                    elif LLM_AVAILABLE:
                        api_key = os.environ.get("OPENAI_API_KEY")
                        
                        # If no environment variable, try to read from config file
                        if not api_key:
                            try:
                                if os.path.exists("config.json"):
                                    with open("config.json", "r") as f:
                                        config = json.load(f)
                                        api_key = config.get("ai_settings", {}).get("openai_api_key")
                                        if api_key and api_key != "REPLACE_WITH_YOUR_API_KEY":
                                            print("Using OpenAI API key from config.json for intent classification")
                                        else:
                                            api_key = None
                            except Exception as e:
                                print(f"Failed to read API key from config: {e}")
                        
                        if api_key:
                            model = os.environ.get("DLR_LLM_MODEL", "gpt-3.5-turbo")
                            intent_assistant = LLMEnhancedAssistant(db_path, api_key=api_key, model=model)
                        else:
                            print("No valid intent assistant available - using fallback analysis")
                            intent_assistant = None
                    else:
                        print("No valid intent assistant available - using fallback analysis")
                        intent_assistant = None
                    
                    # Check if the assistant supports intent classification
                    if intent_assistant and hasattr(intent_assistant, "classify_visualization_intent"):
                        intent_result = intent_assistant.classify_visualization_intent(message)
                        if intent_result and "visualization_type" in intent_result:
                            analysis_type = intent_result["visualization_type"]
                            print(f"Advanced assistant classified visualization intent as: {analysis_type}")
                        else:
                            print("Using rule-based intent classification fallback")
                    else:
                        # Use rule-based classification
                        print("Using rule-based intent classification fallback")
                            
                except ImportError:
                    # Fall back to rule-based classification
                    print("Using rule-based intent classification fallback")
                        
                except Exception as e:
                    print(f"Error using LLM for intent classification: {e}")
            
            # Fallback to rule-based classification if LLM fails
            if analysis_type == "standard":
                if is_advanced_request:
                    analysis_type = "advanced"
                    
                    # Check for specific advanced analysis types
                    if any(word in message_lower for word in ["cluster", "clustering", "segment"]):
                        analysis_type = "clustering"
                    elif any(word in message_lower for word in ["anomaly", "anomalies", "outlier", "unusual"]):
                        analysis_type = "anomaly"
                    elif any(word in message_lower for word in ["correlation", "relationship", "dependence"]):
                        analysis_type = "correlation"
                    elif any(word in message_lower for word in ["forecast", "predict", "future", "trend"]):
                        analysis_type = "forecast"
                    elif any(word in message_lower for word in ["reliability", "resilience", "robustness"]):
                        analysis_type = "reliability"
                    elif any(word in message_lower for word in ["congestion", "bottleneck", "constraint"]):
                        analysis_type = "congestion"
                
                # Check for specialized visualization types
                if is_visualization_request:
                    if "single line" in message_lower or "diagram" in message_lower:
                        analysis_type = "single_line_diagram"
                    elif "bus voltage" in message_lower or "voltage profile" in message_lower:
                        analysis_type = "bus_voltage_profile"
                    elif "branch load" in message_lower or "loading plot" in message_lower:
                        analysis_type = "branch_loading"
                    elif "time-series" in message_lower or "temporal" in message_lower:
                        analysis_type = "time_series"
                    elif "heat map" in message_lower or "heatmap" in message_lower:
                        analysis_type = "heat_map"
                    elif "power flow" in message_lower or "arrows" in message_lower:
                        analysis_type = "power_flow_arrows"
                    elif "voltage stability" in message_lower or "margin curve" in message_lower:
                        analysis_type = "voltage_stability"
                    elif "generation stack" in message_lower or "generation mix" in message_lower:
                        analysis_type = "generation_stack"
                    elif "risk" in message_lower or "probabilistic" in message_lower:
                        analysis_type = "risk_map"
                    elif "contingency" in message_lower or "outage" in message_lower:
                        analysis_type = "contingency_analysis"
                    elif "correlation" in message_lower or "heat map" in message_lower:
                        analysis_type = "correlation_heatmap"
            
            # Store the analysis type in a session variable or pass it to the modal
            if "session_store" not in globals():
                session_store = {}

            # Always set preset values to ensure analysis is displayed
            session_store["analysis_type"] = analysis_type
            session_store["use_preset_values"] = True
            
            # Try to load the database path from config
            db_path = "data/data.db"  # Default path
            if os.path.exists("config.json"):
                with open("config.json", "r") as f:
                    config = json.load(f)
                    db_path = config.get("database_path", db_path)
                    
            # Preload some analysis data to ensure modal shows something
            try:
                # Import here to avoid circular imports
                from power_stats import perform_advanced_analysis
                # Preload the analysis results
                advanced_results = perform_advanced_analysis(db_path, analysis_type=analysis_type)
                session_store["preloaded_analysis"] = advanced_results
            except Exception as e:
                print(f"Error preloading analysis: {e}")
                session_store["preloaded_analysis"] = {"error": f"Error preloading analysis: {str(e)}"}

            # Generate intelligent response based on analysis results
            if "session_store" in globals() and "use_advanced_statistics" in session_store and session_store["use_advanced_statistics"]:
                # Enhanced responses based on actual analysis results
                if statistical_results and 'error' not in statistical_results:
                    if analysis_type == "voltage_analysis":
                        low_violations = statistical_results.get('low_voltage_violations', {}).get('count', 0)
                        high_violations = statistical_results.get('high_voltage_violations', {}).get('count', 0)
                        total_buses = statistical_results.get('total_buses', 0)
                        
                        ai_response = f"⚡ **Voltage Analysis Complete!**\n\n"
                        ai_response += f"📊 **System Status**: Analyzed {total_buses} buses\n"
                        ai_response += f"🔴 **Low Voltage Violations**: {low_violations} buses\n"
                        ai_response += f"🔴 **High Voltage Violations**: {high_violations} buses\n\n"
                        
                        if low_violations > 0 or high_violations > 0:
                            ai_response += "⚠️ **Action Required**: Voltage violations detected! Check the detailed analysis for affected buses and recommended corrective actions."
                        else:
                            ai_response += "✅ **All Clear**: No voltage violations detected. System is operating within acceptable voltage limits."
                    
                    elif analysis_type == "power_flow":
                        overloaded = statistical_results.get('overloaded_branches', {}).get('count', 0)
                        heavily_loaded = statistical_results.get('heavily_loaded_branches', {}).get('count', 0)
                        total_branches = statistical_results.get('total_branches', 0)
                        max_loading = statistical_results.get('max_loading_percentage', 0)
                        
                        ai_response = f"🔄 **Power Flow Analysis Complete!**\n\n"
                        ai_response += f"📊 **System Status**: Analyzed {total_branches} branches\n"
                        ai_response += f"🔴 **Overloaded Branches**: {overloaded} branches (>100%)\n"
                        ai_response += f"🟡 **Heavily Loaded Branches**: {heavily_loaded} branches (>80%)\n"
                        ai_response += f"📈 **Maximum Loading**: {max_loading:.1f}%\n\n"
                        
                        if overloaded > 0:
                            ai_response += "🚨 **Critical**: Branch overloading detected! Immediate attention required to prevent equipment damage."
                        elif heavily_loaded > 0:
                            ai_response += "⚠️ **Caution**: Some branches are heavily loaded. Monitor closely during peak conditions."
                        else:
                            ai_response += "✅ **Optimal**: All branches operating within safe loading limits."
                    
                    elif analysis_type == "generation":
                        generators = statistical_results.get('total_generators', 0)
                        total_gen = statistical_results.get('generation_summary', {}).get('total_generation_mw', 0)
                        max_gen = statistical_results.get('generation_summary', {}).get('max_generation_mw', 0)
                        diversity = statistical_results.get('dispatch_metrics', {}).get('generation_diversity', 0)
                        
                        ai_response = f"⚡ **Generation Dispatch Analysis Complete!**\n\n"
                        ai_response += f"🏭 **Active Generators**: {generators} units\n"
                        ai_response += f"📊 **Total Generation**: {total_gen:.1f} MW\n"
                        ai_response += f"🔝 **Largest Unit**: {max_gen:.1f} MW\n"
                        ai_response += f"📈 **Dispatch Diversity**: {diversity:.2f}\n\n"
                        
                        if diversity > 1.0:
                            ai_response += "📊 **Analysis**: High generation diversity indicates good load distribution across multiple units."
                        else:
                            ai_response += "⚠️ **Note**: Low diversity may indicate heavy reliance on few generators."
                    
                    elif analysis_type == "health_check":
                        overall_score = statistical_results.get('overall_health_score', 0)
                        health_rating = statistical_results.get('health_rating', 'Unknown')
                        voltage_health = statistical_results.get('component_scores', {}).get('voltage_health', 0)
                        loading_health = statistical_results.get('component_scores', {}).get('loading_health', 0)
                        
                        ai_response = f"🏥 **System Health Check Complete!**\n\n"
                        ai_response += f"🎯 **Overall Health**: {overall_score:.1f}/100 ({health_rating})\n"
                        ai_response += f"⚡ **Voltage Health**: {voltage_health:.1f}/100\n"
                        ai_response += f"🔄 **Loading Health**: {loading_health:.1f}/100\n\n"
                        
                        recommendations = statistical_results.get('recommendations', [])
                        if recommendations:
                            ai_response += "💡 **Recommendations**:\n"
                            for rec in recommendations[:3]:  # Show top 3 recommendations
                                ai_response += f"• {rec}\n"
                        
                        if overall_score >= 95:
                            ai_response += "\n🎉 **Excellent**: System is in excellent condition!"
                        elif overall_score >= 85:
                            ai_response += "\n👍 **Good**: System is performing well with minor optimization opportunities."
                        elif overall_score >= 70:
                            ai_response += "\n⚠️ **Fair**: Some issues detected that should be addressed."
                        else:
                            ai_response += "\n🚨 **Poor**: Multiple issues require immediate attention!"
                    
                    elif analysis_type == "system_summary":
                        buses = statistical_results.get('total_buses', 0)
                        branches = statistical_results.get('total_branches', 0)
                        total_gen = statistical_results.get('total_generation_mw', 0)
                        total_load = statistical_results.get('total_load_mw', 0)
                        
                        ai_response = f"📋 **System Summary Complete!**\n\n"
                        ai_response += f"🏗️ **Network Size**: {buses} buses, {branches} branches\n"
                        ai_response += f"⚡ **Generation**: {total_gen:.1f} MW\n"
                        ai_response += f"🏠 **Load**: {total_load:.1f} MW\n"
                        ai_response += f"📊 **System Balance**: {((total_gen - total_load) / total_gen * 100) if total_gen > 0 else 0:.1f}% reserves\n\n"
                        ai_response += "📈 **Intelligent Analysis**: Using flexible database integration - automatically selected best available data source for comprehensive insights."
                    
                    elif analysis_type == "comprehensive":
                        if 'analyses' in statistical_results:
                            analysis_count = len([a for a in statistical_results['analyses'].values() if a and 'error' not in a])
                            ai_response = f"🎯 **Comprehensive Analysis Suite Complete!**\n\n"
                            ai_response += f"✅ **Analyses Performed**: {analysis_count} different analysis types\n"
                            ai_response += f"🔍 **Data Intelligence**: Flexible analysis using any available database data\n"
                            ai_response += f"📊 **Scope**: Complete power system assessment with automated case selection\n\n"
                            ai_response += "🚀 **Innovation**: This analysis uses advanced flexible algorithms that work with any database structure - no hardcoded assumptions!"
                        else:
                            ai_response = "🎯 **Comprehensive Analysis Complete!** Multiple analysis types performed with intelligent data selection."
                    
                    else:
                        ai_response = f"✅ **{analysis_type.replace('_', ' ').title()} Complete!**\n\nAdvanced statistical analysis performed using flexible database integration. Check the detailed results for comprehensive insights and visualizations."
                
                else:
                    # Handle error cases gracefully
                    error_msg = statistical_results.get('error', 'Unknown error') if statistical_results else 'Analysis failed'
                    ai_response = f"⚠️ **Analysis Issue**: {error_msg}\n\n"
                    ai_response += "🔄 **Trying Alternative**: The system is attempting to use fallback data sources and alternative analysis methods.\n\n"
                    ai_response += "💡 **Note**: Your flexible statistical analyzer is designed to work with any available database data!"
            
            else:
                # Fallback responses for non-statistical queries
                if analysis_type == "standard":
                    ai_response = "I'll analyze the power system data and provide statistical insights in a detailed popup window."
                else:
                    ai_response = f"I'll perform {analysis_type.replace('_', ' ')} analysis of the power system data with comprehensive statistical evaluation."
            
            # Get statistical analysis results from AI assistant if available
            try:
                import time
                import os
                
                # Initialize AI assistant
                db_path = "data/data.db"  # Default path
                if os.path.exists("config.json"):
                    import json
                    with open("config.json", "r") as f:
                        config = json.load(f)
                        db_path = config.get("database_path", db_path)
                
                # Try to use the best available assistant
                try:
                    # Check for LLM configuration from environment
                    use_mock_llm = os.environ.get("DLR_MOCK_LLM") == "1"
                    use_llama = os.environ.get("DLR_USE_LLAMA") == "1"
                    
                    print(f"Getting best available assistant. Mock: {use_mock_llm}, Llama: {use_llama}")
                    
                    # Use the factory function to get the appropriate assistant
                    assistant = None
                    expertise = os.environ.get("DLR_EXPERTISE_LEVEL", "expert")
                    
                    if MOCK_LLM_AVAILABLE:
                        assistant = get_assistant(db_path, use_mock_llm=use_mock_llm, use_llama=use_llama)
                    elif LLM_AVAILABLE:
                        api_key = os.environ.get("OPENAI_API_KEY")
                        
                        # If no environment variable, try to read from config file
                        if not api_key:
                            try:
                                if os.path.exists("config.json"):
                                    with open("config.json", "r") as f:
                                        config = json.load(f)
                                        api_key = config.get("ai_settings", {}).get("openai_api_key")
                                        if api_key and api_key != "REPLACE_WITH_YOUR_API_KEY":
                                            print("Using OpenAI API key from config.json for statistical analysis")
                                        else:
                                            api_key = None
                            except Exception as e:
                                print(f"Failed to read API key from config: {e}")
                        
                        if api_key:
                            model = os.environ.get("DLR_LLM_MODEL", "gpt-3.5-turbo")
                            assistant = LLMEnhancedAssistant(db_path, api_key=api_key, model=model)
                        else:
                            print("No OpenAI API key available - using basic assistant")
                            assistant = None
                    else:
                        print("Basic assistant fallback")
                        assistant = None
                    
                    print(f"Assistant available: {assistant is not None}")
                    
                    # Set expertise level from environment
                    if assistant and hasattr(assistant, "set_expertise_level"):
                        assistant.set_expertise_level(expertise)
                
                except ImportError:
                    # Fall back to basic assistant
                    print("Factory function not available, using basic assistant")
                    assistant = None
                
                # Create a session ID if it doesn't exist
                if "session_id" not in session_store:
                    session_store["session_id"] = f"session_{time.time()}"
                
                # Get specific statistical data if assistant is available
                if assistant and hasattr(assistant, "_perform_statistical_analysis"):
                    stat_query = "Provide statistical analysis of the power system"
                    stat_results = assistant._perform_statistical_analysis(stat_query)
                    
                    if stat_results:
                        print(f"Retrieved statistical analysis data: {list(stat_results.keys())}")
                        session_store["ai_response_data"] = stat_results
                        session_store["analysis_type"] = "statistical"
                else:
                    print("No advanced AI assistant available for statistical queries")
            except Exception as e:
                print(f"Error retrieving statistical analysis from AI assistant: {e}")
            
            # Trigger the statistical analysis modal
            # If we have statistical analysis data, switch to statistical tab
            tab_to_show = "tab-4" if "ai_response_data" in session_store and session_store["analysis_type"] == "statistical" else "tab-1"
            
            return updated_messages + [create_ai_message(ai_response, timestamp)], "", True, tab_to_show
        
        # Enhanced intelligent response processing
        if INTELLIGENT_CHAT_AVAILABLE and STATISTICAL_ANALYSIS_AVAILABLE:
            try:
                # Initialize intelligent assistant
                db_path = "data.db"
                if os.path.exists("config.json"):
                    import json
                    with open("config.json", "r") as f:
                        config = json.load(f)
                        db_path = config.get("database_path", db_path).replace("\\\\", "\\")
                
                # Ensure database file exists
                if not os.path.exists(db_path):
                    alternative_paths = ["data.db", "./data.db", "C:/Projects/dlr-database-project/data.db"]
                    for alt_path in alternative_paths:
                        if os.path.exists(alt_path):
                            db_path = alt_path
                            break
                
                print(f"🤖 Using intelligent chat processing with database: {db_path}")
                
                # Initialize intelligent assistant
                intelligent_assistant = PowerSystemIntelligentAssistant(db_path)
                
                # Check if user requested statistical analysis
                if any(keyword in message_lower for keyword in [
                    "analyze", "analysis", "statistics", "stats", "show me data", "voltage violations",
                    "power flow", "thermal", "contingency", "health check", "summary"
                ]):
                    # Initialize statistical analyzer  
                    stat_analyzer = PowerSystemStatisticalAnalyzer(db_path)
                    statistical_results = None
                    
                    # Determine analysis type from intelligent intent analysis
                    intent = intelligent_assistant.analyze_user_intent(message)
                    analysis_mapping = {
                        "voltage": lambda: stat_analyzer.voltage_violation_analysis(),
                        "power": lambda: stat_analyzer.power_flow_analysis(), 
                        "thermal": lambda: stat_analyzer.power_flow_analysis(),  # Use power flow for thermal
                        "contingency": lambda: stat_analyzer.contingency_impact_analysis(),
                        "economic": lambda: stat_analyzer.system_losses_analysis()
                    }
                    
                    # Execute appropriate analysis
                    primary_focus = intent.get("primary_focus", "general")
                    if primary_focus in analysis_mapping:
                        print(f"🔍 Executing {primary_focus} analysis based on intelligent intent detection")
                        try:
                            statistical_results = analysis_mapping[primary_focus]()
                            print(f"✅ Statistical analysis completed successfully")
                        except Exception as e:
                            print(f"❌ Statistical analysis failed: {e}")
                            statistical_results = {"error": str(e)}
                    elif intent.get("requires_analysis", False):
                        # Default to comprehensive analysis
                        try:
                            statistical_results = stat_analyzer.basic_analysis_suite()
                            print(f"✅ Comprehensive analysis completed")
                        except Exception as e:
                            print(f"❌ Comprehensive analysis failed: {e}")
                            statistical_results = {"error": str(e)}
                    
                    # Generate intelligent response with statistical results using enhanced visualization processing
                    result = intelligent_assistant.process_with_visualization(message, statistical_results)
                    ai_response = result.get("text_response", "")
                    visualization = result.get("visualization", None)
                    intent = result.get("intent", {})
                    
                    print(f"🧠 Generated intelligent response with {len(ai_response)} characters")
                    if visualization:
                        print("📊 Generated visualization based on user intent")
                    
                else:
                    # Generate intelligent response without statistical analysis
                    result = intelligent_assistant.process_with_visualization(message)
                    ai_response = result.get("text_response", "")
                    visualization = result.get("visualization", None)
                    intent = result.get("intent", {})
                    
                    print(f"🧠 Generated intelligent conversational response")
                    if visualization:
                        print("📊 Generated basic visualization")
                
            except Exception as e:
                print(f"⚠️ Intelligent chat processing failed: {e}")
                # Fall back to enhanced pattern matching
                ai_response = enhanced_pattern_matching_fallback(message, message_lower)
                visualization = None
                intent = {}
        
        else:
            print("🔄 Using enhanced pattern matching (intelligent engine not available)")
            ai_response = enhanced_pattern_matching_fallback(message, message_lower)
            visualization = None
            intent = {}
        
        # Create AI message component with unique timestamp to ensure updates
        from datetime import datetime
        unique_timestamp = datetime.now().strftime("%H:%M:%S")
        ai_msg = create_ai_message(ai_response, timestamp, visualization)
        
        # Add message to the chat
        updated_messages.append(ai_msg)
        
        print(f"Sending AI response at {unique_timestamp}: {ai_response[:50]}...")
        return updated_messages, "", False, no_update  # Clear input field, keep modal closed
    
    # Callbacks for updating the statistical analysis modal content
    @app.callback(
        [Output("stats-summary-text", "children"),
         Output("stats-comparison-plot", "figure"),
         Output("stats-graph-plot", "figure"),
         Output("system-resilience", "children"),
         Output("advanced-analysis-content", "children")],
        [Input("stats-modal", "is_open"),
         Input("stats-tabs", "active_tab")],
        [State("store-network-graph", "data")]
    )
    def update_statistics_content(modal_open, active_tab, graph_data):
        """Update statistical analysis modal content when it's opened"""
        from dash import no_update, html
        import plotly.express as px
        import numpy as np

        if not modal_open:
            return no_update, no_update, no_update, no_update, no_update

        # Debug output
        print(f"Updating statistics content. Modal open: {modal_open}, Active tab: {active_tab}")
        print(f"Graph data available: {graph_data is not None}")
        
        # Create preset visualizations in case the database analysis fails
        preset_visualizations = {
            'clustering': px.scatter(
                x=np.random.normal(loc=0, scale=1, size=50),
                y=np.random.normal(loc=0, scale=1, size=50),
                color=[f"Cluster {i}" for i in np.random.randint(0, 3, 50)],
                title="Power System Component Clustering",
                labels={"x": "Load Factor", "y": "Voltage Level", "color": "Cluster Group"}
            ),
            'anomaly': px.scatter(
                x=np.random.normal(loc=0, scale=1, size=100),
                y=np.random.normal(loc=0, scale=1, size=100),
                color=["Normal" if i < 90 else "Anomaly" for i in range(100)],
                title="Power System Anomaly Detection",
                labels={"x": "Expected Load", "y": "Actual Load", "color": "Status"}
            ),
            'correlation': px.imshow(
                np.random.rand(10, 10), 
                x=[f"Variable {i}" for i in range(10)],
                y=[f"Variable {i}" for i in range(10)],
                title="Parameter Correlation Matrix",
                color_continuous_scale="Viridis"
            ),
            'forecast': px.line(
                x=list(range(30)),
                y=np.cumsum(np.random.normal(loc=0.1, scale=0.1, size=30)),
                title="Power System Load Forecast",
                labels={"x": "Time (Days)", "y": "System Load (MW)"}
            )
        }
        
        try:
            # Try to get the database path from config
            db_path = "data/data.db"  # Default path
            if os.path.exists("config.json"):
                with open("config.json", "r") as f:
                    config = json.load(f)
                    db_path = config.get("database_path", db_path)
            
            print(f"Using database path: {db_path}")
            
            # Check if advanced analysis was requested
            analysis_type = "standard"
            if "session_store" in globals() and "analysis_type" in session_store:
                analysis_type = session_store.get("analysis_type")
                print(f"Advanced analysis requested: {analysis_type}")
                
            # Set matplotlib backend to avoid display issues
            import matplotlib
            matplotlib.use('Agg')  # Use non-interactive backend
            
            # Get database statistics with error handling
            try:
                db_stats = get_database_stats(db_path)
                print("Database statistics retrieved successfully")
            except Exception as db_err:
                print(f"Error getting database statistics: {db_err}")
                db_stats = {"error": f"Database error: {str(db_err)}"}
            
            # Convert graph data to NetworkX graph if available
            graph = None
            if graph_data:
                try:
                    # Recreate NetworkX graph from JSON data
                    graph = nx.node_link_graph(graph_data)
                    print(f"Graph recreated successfully with {len(graph.nodes)} nodes and {len(graph.edges)} edges")
                except Exception as e:
                    print(f"Error recreating graph: {e}")
            
            # Get graph statistics if graph is available
            try:
                graph_stats = get_graph_stats(graph) if graph else {"error": "Graph data not available"}
                print("Graph statistics calculated successfully")
            except Exception as g_err:
                print(f"Error calculating graph statistics: {g_err}")
                graph_stats = {"error": f"Graph statistics error: {str(g_err)}"}
            
            # Perform advanced analysis if requested
            advanced_results = None
            try:
                # Check if we have advanced statistical results from PowerSystemStatisticalAnalyzer
                if ("session_store" in globals() and 
                    "use_advanced_statistics" in session_store and 
                    session_store["use_advanced_statistics"] and
                    "statistical_results" in session_store):
                    
                    print("Using advanced statistical analysis results from PowerSystemStatisticalAnalyzer")
                    advanced_results = session_store["statistical_results"]
                    
                    # Also check for visualization data
                    if "visualization_data" in session_store:
                        visualization_data = session_store["visualization_data"]
                        print("Advanced statistical visualizations available")
                    
                # Check if we have preloaded analysis results
                elif "session_store" in globals() and "preloaded_analysis" in session_store:
                    print(f"Using preloaded analysis results")
                    advanced_results = session_store["preloaded_analysis"]
                elif analysis_type != "standard":
                    print(f"Performing advanced analysis of type: {analysis_type}")
                    advanced_results = perform_advanced_analysis(db_path, graph, analysis_type)
                else:
                    # Even for standard analysis, provide some default visualizations
                    from power_stats import perform_advanced_analysis
                    print(f"Performing default analysis visualization")
                    advanced_results = perform_advanced_analysis(db_path, graph, "all")
                
                # Check if there's statistical analysis data from AI assistant
                if "session_store" in globals() and "ai_response_data" in session_store and "analysis_type" in session_store["ai_response_data"]:
                    if session_store["ai_response_data"]["analysis_type"] == "statistical":
                        print("Using statistical analysis data from AI assistant")
                        # Merge AI statistical data with advanced results
                        if not advanced_results:
                            advanced_results = {}
                        advanced_results["statistical_analysis"] = session_store["ai_response_data"]
                
                print(f"Analysis completed successfully with results: {list(advanced_results.keys()) if advanced_results else 'No results'}")
            except Exception as adv_err:
                print(f"Error performing advanced analysis: {adv_err}")
                advanced_results = {"error": f"Advanced analysis error: {str(adv_err)}"}
                
            try:
                # Generate statistical summary text - Enhanced for PowerSystemStatisticalAnalyzer results
                if ("session_store" in globals() and 
                    "use_advanced_statistics" in session_store and 
                    session_store["use_advanced_statistics"] and
                    "statistical_results" in session_store):
                    
                    # Handle advanced statistical results from PowerSystemStatisticalAnalyzer
                    statistical_results = session_store["statistical_results"]
                    analysis_type = session_store.get("analysis_type", "comprehensive")
                    
                    summary_elements = [
                        html.H4(f"🔬 Advanced Statistical Analysis: {analysis_type.title().replace('_', ' ')}")
                    ]
                    
                    if "error" in statistical_results:
                        summary_elements.append(html.Div([
                            html.P("⚠️ An error occurred during statistical analysis:", className="text-danger"),
                            html.Pre(statistical_results["error"], style={"backgroundColor": "#f8f9fa", "padding": "10px"})
                        ]))
                    else:
                        # Handle different types of statistical analysis results
                        if analysis_type == "correlation":
                            if "correlation_matrix" in statistical_results:
                                correlation_data = statistical_results["correlation_matrix"]
                                summary_elements.extend([
                                    html.H5("📊 Correlation Analysis Results", className="mt-3"),
                                    html.P(f"• Analyzed {correlation_data.get('num_variables', 'N/A')} variables"),
                                    html.P(f"• Strongest correlation: {correlation_data.get('max_correlation', 'N/A'):.3f}"),
                                    html.P(f"• Weakest correlation: {correlation_data.get('min_correlation', 'N/A'):.3f}"),
                                    html.P("Key findings:", className="fw-bold"),
                                    html.Ul([
                                        html.Li(finding) for finding in correlation_data.get('key_findings', [])
                                    ])
                                ])
                        
                        elif analysis_type == "monte_carlo":
                            if "risk_metrics" in statistical_results:
                                risk_data = statistical_results["risk_metrics"]
                                summary_elements.extend([
                                    html.H5("🎲 Monte Carlo Risk Analysis", className="mt-3"),
                                    html.P(f"• Simulation runs: {risk_data.get('num_simulations', 'N/A'):,}"),
                                    html.P(f"• Risk level: {risk_data.get('risk_level', 'N/A')}"),
                                    html.P(f"• Confidence interval: {risk_data.get('confidence_interval', 'N/A')}"),
                                    html.P("Risk insights:", className="fw-bold"),
                                    html.Ul([
                                        html.Li(insight) for insight in risk_data.get('insights', [])
                                    ])
                                ])
                        
                        elif analysis_type == "sensitivity":
                            if "sensitivity_indices" in statistical_results:
                                sensitivity_data = statistical_results["sensitivity_indices"]
                                summary_elements.extend([
                                    html.H5("📈 Sensitivity Analysis Results", className="mt-3"),
                                    html.P(f"• Parameters analyzed: {sensitivity_data.get('num_parameters', 'N/A')}"),
                                    html.P(f"• Most sensitive parameter: {sensitivity_data.get('most_sensitive', 'N/A')}"),
                                    html.P(f"• Sensitivity range: {sensitivity_data.get('sensitivity_range', 'N/A')}"),
                                    html.P("Sensitivity insights:", className="fw-bold"),
                                    html.Ul([
                                        html.Li(insight) for insight in sensitivity_data.get('insights', [])
                                    ])
                                ])
                        
                        elif analysis_type == "clustering":
                            if "clusters" in statistical_results:
                                cluster_data = statistical_results["clusters"]
                                summary_elements.extend([
                                    html.H5("🔍 Clustering Analysis Results", className="mt-3"),
                                    html.P(f"• Optimal clusters: {cluster_data.get('optimal_clusters', 'N/A')}"),
                                    html.P(f"• Clustering algorithm: {cluster_data.get('algorithm', 'N/A')}"),
                                    html.P(f"• Silhouette score: {cluster_data.get('silhouette_score', 'N/A'):.3f}"),
                                    html.P("Cluster characteristics:", className="fw-bold"),
                                    html.Ul([
                                        html.Li(char) for char in cluster_data.get('characteristics', [])
                                    ])
                                ])
                        
                        elif analysis_type == "reliability":
                            if "reliability_metrics" in statistical_results:
                                reliability_data = statistical_results["reliability_metrics"]
                                summary_elements.extend([
                                    html.H5("🔧 Reliability Analysis Results", className="mt-3"),
                                    html.P(f"• System availability: {reliability_data.get('availability', 'N/A'):.3%}"),
                                    html.P(f"• MTBF: {reliability_data.get('mtbf', 'N/A')} hours"),
                                    html.P(f"• MTTR: {reliability_data.get('mttr', 'N/A')} hours"),
                                    html.P("Reliability insights:", className="fw-bold"),
                                    html.Ul([
                                        html.Li(insight) for insight in reliability_data.get('insights', [])
                                    ])
                                ])
                        
                        elif analysis_type == "comprehensive":
                            # Handle comprehensive analysis with multiple result types
                            if "correlation" in statistical_results:
                                correlation_summary = statistical_results["correlation"].get("summary", {})
                                summary_elements.extend([
                                    html.H5("📊 Correlation Analysis Summary", className="mt-3"),
                                    html.P(f"• Strongest correlation: {correlation_summary.get('max_correlation', 'N/A'):.3f}"),
                                    html.P(f"• Variables analyzed: {correlation_summary.get('num_variables', 'N/A')}")
                                ])
                            
                            if "monte_carlo" in statistical_results:
                                mc_summary = statistical_results["monte_carlo"].get("summary", {})
                                summary_elements.extend([
                                    html.H5("🎲 Risk Analysis Summary", className="mt-3"),
                                    html.P(f"• Risk level: {mc_summary.get('risk_level', 'N/A')}"),
                                    html.P(f"• Simulations: {mc_summary.get('num_simulations', 'N/A'):,}")
                                ])
                            
                            if "clustering" in statistical_results:
                                cluster_summary = statistical_results["clustering"].get("summary", {})
                                summary_elements.extend([
                                    html.H5("🔍 Clustering Summary", className="mt-3"),
                                    html.P(f"• Optimal clusters: {cluster_summary.get('optimal_clusters', 'N/A')}"),
                                    html.P(f"• Silhouette score: {cluster_summary.get('silhouette_score', 'N/A'):.3f}")
                                ])
                        
                        # Add visualization section if available
                        if "session_store" in globals() and "visualization_data" in session_store:
                            viz_data = session_store["visualization_data"]
                            if viz_data and isinstance(viz_data, dict) and "figure" in viz_data:
                                summary_elements.extend([
                                    html.Hr(),
                                    html.H5("📈 Interactive Visualization", className="mt-3"),
                                    html.Div([
                                        dcc.Graph(
                                            figure=viz_data["figure"],
                                            style={"height": "400px"}
                                        )
                                    ])
                                ])
                
                elif advanced_results and analysis_type != "standard":
                    # Handle original advanced analysis results (fallback)
                    summary_elements = [
                        html.H4(f"Advanced Power System Analysis: {analysis_type.title()}")
                    ]
                    
                    if "error" in advanced_results:
                        summary_elements.append(html.Div([
                            html.P("An error occurred during advanced analysis:"),
                            html.Pre(advanced_results["error"])
                        ]))
                    else:
                        # Add specific advanced analysis results based on the type
                        if analysis_type == "clustering" and "clustering_analysis" in advanced_results:
                            cluster_results = advanced_results["clustering_analysis"]
                            
                            summary_elements.extend([
                                html.H5("Clustering Analysis Results"),
                                html.P(f"Optimal number of clusters identified: {cluster_results.get('optimal_clusters', 'N/A')}"),
                                html.Div([
                                    dcc.Graph(figure=cluster_results.get('cluster_visualization'))
                                ]) if 'cluster_visualization' in cluster_results else None
                            ])
                            
                        elif analysis_type == "anomaly" and "anomaly_detection" in advanced_results:
                            anomaly_results = advanced_results["anomaly_detection"]
                            
                            if "voltage_anomalies" in anomaly_results:
                                v_anomalies = anomaly_results["voltage_anomalies"]
                                summary_elements.extend([
                                    html.H5("Voltage Anomaly Detection"),
                                    html.P(f"Number of anomalies detected: {v_anomalies.get('num_anomalies', 0)}"),
                                    html.Div([
                                        dcc.Graph(figure=v_anomalies.get('visualization'))
                                    ]) if 'visualization' in v_anomalies else None
                                ])
                                
                            if "loading_anomalies" in anomaly_results:
                                l_anomalies = anomaly_results["loading_anomalies"]
                                summary_elements.extend([
                                    html.H5("Line Loading Anomaly Detection"),
                                    html.P(f"Number of anomalies detected: {l_anomalies.get('num_anomalies', 0)}"),
                                    html.Div([
                                        dcc.Graph(figure=l_anomalies.get('visualization'))
                                    ]) if 'visualization' in l_anomalies else None
                                ])
                                
                        elif analysis_type == "correlation" and "correlation_analysis" in advanced_results:
                            corr_results = advanced_results["correlation_analysis"]
                            
                            summary_elements.extend([
                                html.H5("Correlation Analysis"),
                                html.Div([
                                    dcc.Graph(figure=corr_results.get('correlation_visualization'))
                                ]) if 'correlation_visualization' in corr_results else None,
                                
                                html.H5("Top Correlations"),
                                html.Ul([
                                    html.Li(f"{pair[0]} vs {pair[1]}: {pair[2]:.3f}") 
                                    for pair in corr_results.get('top_correlations', [])[:5]
                                ]) if 'top_correlations' in corr_results else None
                            ])
                        
                        elif analysis_type == "statistical" or ("statistical_analysis" in advanced_results):
                            # Statistical analysis from AI assistant
                            stat_results = advanced_results.get("statistical_analysis", {})
                            
                            summary_elements.append(html.H5("Statistical Analysis Results"))
                            
                            # Handle different types of statistical data
                            if "violation_summary" in stat_results:
                                vs = stat_results["violation_summary"]
                                summary_elements.extend([
                                    html.H6("Violation Statistics"),
                                    html.P(f"Total violations: {vs.get('total_count', 'N/A')}"),
                                    html.P(f"Cases with violations: {vs.get('case_count', 'N/A')}"),
                                    html.P(f"Average violation value: {vs.get('avg_value', 'N/A'):.3f}"),
                                    html.P(f"Min-Max range: {vs.get('min_value', 'N/A'):.3f} - {vs.get('max_value', 'N/A'):.3f}")
                                ])
                                
                                # Create violation bar chart
                                if "violation_by_type" in stat_results:
                                    try:
                                        vbt = stat_results["violation_by_type"]
                                        import plotly.express as px
                                        import pandas as pd
                                        
                                        df = pd.DataFrame(vbt)
                                        fig = px.bar(
                                            df, 
                                            x="violation_type", 
                                            y="count", 
                                            title="Violations by Type",
                                            labels={"violation_type": "Violation Type", "count": "Count"}
                                        )
                                        summary_elements.append(dcc.Graph(figure=fig))
                                    except Exception as e:
                                        print(f"Error creating violation chart: {e}")
                            
                            if "branch_summary" in stat_results:
                                bs = stat_results["branch_summary"]
                                summary_elements.extend([
                                    html.H6("Branch/Line Statistics"),
                                    html.P(f"Total lines: {bs.get('line_count', 'N/A')}"),
                                    html.P(f"Average normal rating: {bs.get('avg_normal_rating', 'N/A'):.2f} MVA"),
                                    html.P(f"Average emergency rating: {bs.get('avg_emergency_rating', 'N/A'):.2f} MVA")
                                ])
                                
                                # Create congested lines table
                                if "congested_lines" in stat_results:
                                    try:
                                        cl = stat_results["congested_lines"]
                                        summary_elements.extend([
                                            html.H6("Most Congested Lines"),
                                            html.Table([
                                                html.Thead(
                                                    html.Tr([
                                                        html.Th("From"), html.Th("To"), 
                                                        html.Th("Name"), html.Th("Rating"), 
                                                        html.Th("Violations")
                                                    ])
                                                ),
                                                html.Tbody([
                                                    html.Tr([
                                                        html.Td(line.get("from_bus", "")),
                                                        html.Td(line.get("to_bus", "")),
                                                        html.Td(line.get("name", "")),
                                                        html.Td(f"{line.get('ratea', 0):.1f}"),
                                                        html.Td(line.get("violation_count", 0))
                                                    ]) for line in cl[:5]  # Show top 5
                                                ])
                                            ], className="table table-striped")
                                        ])
                                    except Exception as e:
                                        print(f"Error creating congested lines table: {e}")
                            
                            if "bus_summary" in stat_results:
                                bus = stat_results["bus_summary"]
                                summary_elements.extend([
                                    html.H6("Bus Voltage Statistics"),
                                    html.P(f"Total buses: {bus.get('bus_count', 'N/A')}"),
                                    html.P(f"Average voltage: {bus.get('avg_voltage', 'N/A'):.3f} p.u."),
                                    html.P(f"Voltage range: {bus.get('min_voltage', 'N/A'):.3f} - {bus.get('max_voltage', 'N/A'):.3f} p.u.")
                                ])
                            
                            if "dlr_benefits" in stat_results:
                                dlr = stat_results["dlr_benefits"]
                                summary_elements.extend([
                                    html.H6("DLR Benefits Analysis"),
                                    html.P(f"Cases analyzed: {dlr.get('case_count', 'N/A')}"),
                                    html.P(f"Cases resolved by DLR: {dlr.get('resolved_count', 'N/A')}"),
                                    html.P(f"Resolution percentage: {dlr.get('resolution_percentage', 'N/A'):.1f}%")
                                ])
                            
                            # Add insights if available
                            if "insights" in stat_results and stat_results["insights"]:
                                summary_elements.extend([
                                    html.H6("Key Insights"),
                                    html.Ul([
                                        html.Li(insight) for insight in stat_results["insights"]
                                    ])
                                ])
                            
                            # Add recommendations if available
                            if "recommendations" in stat_results and stat_results["recommendations"]:
                                summary_elements.extend([
                                    html.H6("Recommendations"),
                                    html.Ul([
                                        html.Li(rec) for rec in stat_results["recommendations"]
                                    ])
                                ])
                            
                        elif analysis_type == "forecast" and "load_forecast" in advanced_results:
                            forecast_results = advanced_results["load_forecast"]
                            
                            summary_elements.extend([
                                html.H5("Load Forecasting"),
                                html.P(f"Forecast periods: {forecast_results.get('forecast_periods', 'N/A')}"),
                                html.Div([
                                    dcc.Graph(figure=forecast_results.get('forecast_visualization'))
                                ]) if 'forecast_visualization' in forecast_results else None
                            ])
                            
                        elif analysis_type == "reliability" and "reliability_analysis" in advanced_results:
                            reliability_results = advanced_results["reliability_analysis"]
                            
                            summary_elements.extend([
                                html.H5("Reliability Analysis"),
                                html.P(f"Network connected: {reliability_results.get('network_connected', 'N/A')}"),
                                html.P(f"Average path length: {reliability_results.get('average_path_length', 'N/A')}"),
                                html.H6("Critical Lines:"),
                                html.Ul([
                                    html.Li(f"Line {u}-{v}: {b:.3f}") 
                                    for u, v, b in reliability_results.get('critical_lines', [])[:5]
                                ]) if 'critical_lines' in reliability_results else None,
                                html.Div([
                                    dcc.Graph(figure=reliability_results.get('reliability_visualization'))
                                ]) if 'reliability_visualization' in reliability_results else None
                            ])
                            
                        elif analysis_type == "congestion" and "congestion_analysis" in advanced_results:
                            congestion_results = advanced_results["congestion_analysis"]
                            
                            if "congestion_stats" in congestion_results:
                                stats = congestion_results["congestion_stats"]
                                summary_elements.extend([
                                    html.H5("Congestion Analysis"),
                                    html.P(f"Congested branches: {stats.get('congested_branches', 0)} " +
                                          f"({stats.get('congestion_percentage', 0):.1f}% of network)"),
                                    html.P(f"Average loading: {stats.get('average_loading', 0):.1f}%"),
                                    html.P(f"Maximum loading: {stats.get('max_loading', 0):.1f}%"),
                                    html.Div([
                                        dcc.Graph(figure=congestion_results.get('loading_histogram'))
                                    ]) if 'loading_histogram' in congestion_results else None
                                ])
                    
                    summary_html = html.Div(summary_elements)
                else:
                    summary_html = format_statistical_summary(db_stats, graph_stats)
                
                # Generate comparison plot
                comparison_fig = generate_comparison_plot(db_stats)
                
                # Generate graph plot
                graph_fig = generate_graph_plot(graph) if graph else go.Figure()
                
                # Generate resilience assessment
                resilience_html = html.Div([
                    html.H4("System Resilience Assessment"),
                    html.P("Analysis of the power system's ability to withstand contingencies and recover from disturbances."),
                    html.Hr(),
                    html.Div(analyze_system_resilience(db_stats, graph_stats))
                ])
            except Exception as viz_err:
                print(f"Error generating visualizations: {viz_err}")
                
                # Provide fallback components
                summary_html = html.Div([
                    html.H4("Statistical Analysis"),
                    html.P("There was an error generating the statistical analysis."),
                    html.Pre(f"Error: {str(viz_err)}")
                ])
                
                empty_fig = go.Figure()
                empty_fig.update_layout(
                    title="Data Unavailable",
                    annotations=[{
                        "text": "No data available for visualization",
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                        "font": {"size": 20}
                    }]
                )
                
                comparison_fig = empty_fig
                graph_fig = empty_fig
                
                resilience_html = html.Div([
                    html.H4("System Resilience Assessment"),
                    html.P("Unable to analyze system resilience due to an error.")
                ])
            
            # Create advanced analysis content
            if advanced_results and analysis_type != "standard":
                advanced_html = create_advanced_analysis_content(advanced_results, analysis_type)
            else:
                advanced_html = html.Div([
                    html.H4("Advanced Analysis"),
                    html.P("Request advanced analysis by asking the assistant for specific analyses like clustering, anomaly detection, forecasting, etc."),
                    html.Ul([
                        html.Li("Cluster Analysis - Identify patterns and groupings in system data"),
                        html.Li("Anomaly Detection - Find unusual patterns or outliers"),
                        html.Li("Correlation Analysis - Discover relationships between parameters"),
                        html.Li("Load Forecasting - Predict future system loading"),
                        html.Li("Reliability Analysis - Assess system resilience"),
                        html.Li("Congestion Analysis - Identify bottlenecks")
                    ])
                ])
            
            return summary_html, comparison_fig, graph_fig, resilience_html, advanced_html
        
        except Exception as e:
            error_message = html.Div([
                html.H4("Error Generating Statistics"),
                html.P(f"An error occurred while generating statistical analysis: {str(e)}"),
                html.P("Please try again or check the system logs for more information.")
            ])
            
            empty_fig = go.Figure()
            empty_fig.update_layout(
                title="Data Unavailable",
                annotations=[{
                    "text": "No data available for visualization",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {"size": 20}
                }]
            )
            
            return error_message, empty_fig, empty_fig, error_message, error_message

def create_advanced_analysis_content(advanced_results, analysis_type):
    """
    Create detailed content for the advanced analysis tab
    
    Args:
        advanced_results (dict): Results from the advanced analysis functions
        analysis_type (str): Type of analysis performed
        
    Returns:
        dash.html.Div: Content for the advanced analysis tab
    """
    # Import necessary modules
    from dash import html, dcc
    import plotly.graph_objects as go
    
    # Function to safely convert a figure to plotly if needed
    def ensure_plotly_figure(fig):
        if fig is None:
            empty_fig = go.Figure()
            empty_fig.update_layout(
                title="No visualization available",
                annotations=[{
                    "text": "No data available for visualization",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {"size": 20}
                }]
            )
            return empty_fig
        
        # If it's already a plotly figure, return it
        if hasattr(fig, 'update_layout'):
            return fig
        
        # If it's a matplotlib figure, convert it
        try:
            # Try to convert using our helper function if available
            try:
                from power_stats import mpl_to_plotly
                return mpl_to_plotly(fig)
            except ImportError:
                # Fall back to creating a simple Plotly figure
                empty_fig = go.Figure()
                empty_fig.update_layout(
                    title="Figure Conversion Required",
                    annotations=[{
                        "text": "Matplotlib figure could not be converted to Plotly",
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                        "font": {"size": 16}
                    }]
                )
                return empty_fig
        except Exception as e:
            print(f"Error converting figure: {e}")
            empty_fig = go.Figure()
            empty_fig.update_layout(
                title="Error displaying visualization",
                annotations=[{
                    "text": f"Error: {str(e)}",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {"size": 16}
                }]
            )
            return empty_fig
    from dash import html, dcc
    
    elements = [
        html.H4(f"Advanced Power System Analysis: {analysis_type.title()}")
    ]
    
    if "error" in advanced_results:
        elements.append(html.Div([
            html.P("An error occurred during advanced analysis:"),
            html.Pre(advanced_results["error"])
        ]))
        return html.Div(elements)
    
    # Add specific advanced analysis results based on the type
    if analysis_type == "clustering" and "clustering_analysis" in advanced_results:
        cluster_results = advanced_results["clustering_analysis"]
        
        elements.extend([
            html.H5("Clustering Analysis Results", className="mt-4"),
            html.Hr(),
            html.P(f"The system data was analyzed to identify natural groupings and patterns."),
            html.P([
                html.Strong("Optimal number of clusters identified: "), 
                f"{cluster_results.get('optimal_clusters', 'N/A')}"
            ]),
            
            html.H6("Cluster Statistics", className="mt-3"),
            html.Div([
                dcc.Graph(figure=ensure_plotly_figure(cluster_results.get('cluster_visualization')))
            ]) if 'cluster_visualization' in cluster_results else None
        ])
        
    elif analysis_type == "anomaly" and "anomaly_detection" in advanced_results:
        anomaly_results = advanced_results["anomaly_detection"]
        
        elements.append(html.H5("Anomaly Detection Results", className="mt-4"))
        elements.append(html.Hr())
        elements.append(html.P("The system was analyzed to detect unusual patterns and outliers that may indicate problems or special conditions."))
        
        if "voltage_anomalies" in anomaly_results:
            v_anomalies = anomaly_results["voltage_anomalies"]
            elements.extend([
                html.H6("Voltage Anomaly Detection", className="mt-3"),
                html.P([
                    html.Strong("Number of anomalies detected: "), 
                    f"{v_anomalies.get('num_anomalies', 0)}"
                ]),
                html.P("Unusual voltage levels may indicate potential problems with voltage regulation or unexpected load conditions."),
                html.Div([
                    dcc.Graph(figure=ensure_plotly_figure(v_anomalies.get('visualization')))
                ]) if 'visualization' in v_anomalies else None
            ])
            
        if "loading_anomalies" in anomaly_results:
            l_anomalies = anomaly_results["loading_anomalies"]
            elements.extend([
                html.H6("Line Loading Anomaly Detection", className="mt-4"),
                html.P([
                    html.Strong("Number of anomalies detected: "), 
                    f"{l_anomalies.get('num_anomalies', 0)}"
                ]),
                html.P("Unusual line loading patterns may indicate potential congestion or reliability issues."),
                html.Div([
                    dcc.Graph(figure=ensure_plotly_figure(l_anomalies.get('visualization')))
                ]) if 'visualization' in l_anomalies else None
            ])
            
    elif analysis_type == "correlation" and "correlation_analysis" in advanced_results:
        corr_results = advanced_results["correlation_analysis"]
        
        elements.extend([
            html.H5("Correlation Analysis Results", className="mt-4"),
            html.Hr(),
            html.P("Analysis of relationships between different power system parameters to identify interdependencies."),
            
            html.H6("Correlation Matrix", className="mt-3"),
            html.Div([
                dcc.Graph(figure=corr_results.get('correlation_visualization'))
            ]) if 'correlation_visualization' in corr_results else None,
            
            html.H6("Top Correlations", className="mt-4"),
            html.P("These are the strongest relationships identified in the system:"),
            html.Ul([
                html.Li([
                    html.Strong(f"{pair[0]} vs {pair[1]}: "),
                    f"{pair[2]:.3f} correlation coefficient"
                ]) 
                for pair in corr_results.get('top_correlations', [])[:5]
            ]) if 'top_correlations' in corr_results else None
        ])
        
        # Add scatter plots for top correlations if available
        if 'top_correlation_visualizations' in corr_results and corr_results['top_correlation_visualizations']:
            elements.append(html.H6("Top Correlation Plots", className="mt-4"))
            
            for viz in corr_results['top_correlation_visualizations']:
                elements.append(html.Div([
                    dcc.Graph(figure=viz.get('visualization'))
                ]))
        
    elif analysis_type == "forecast" and "load_forecast" in advanced_results:
        forecast_results = advanced_results["load_forecast"]
        
        elements.extend([
            html.H5("Load Forecasting Results", className="mt-4"),
            html.Hr(),
            html.P("Time series forecasting of system load based on historical patterns."),
            html.P([
                html.Strong("Forecast periods: "), 
                f"{forecast_results.get('forecast_periods', 'N/A')}"
            ]),
            html.Div([
                dcc.Graph(figure=forecast_results.get('forecast_visualization'))
            ]) if 'forecast_visualization' in forecast_results else None
        ])
        
    elif analysis_type == "reliability" and "reliability_analysis" in advanced_results:
        reliability_results = advanced_results["reliability_analysis"]
        
        elements.extend([
            html.H5("Reliability Analysis Results", className="mt-4"),
            html.Hr(),
            html.P("Assessment of the system's ability to maintain service under various conditions."),
            html.P([
                html.Strong("Network connected: "), 
                "Yes" if reliability_results.get('network_connected', False) else "No (Multiple islands detected)"
            ]),
            html.P([
                html.Strong("Average path length: "), 
                f"{reliability_results.get('average_path_length', 'N/A')}"
            ]),
            
            html.H6("Critical Lines", className="mt-3"),
            html.P("These lines have the highest impact on system reliability:"),
            html.Ul([
                html.Li(f"Line {u}-{v}: Criticality {b:.3f}") 
                for u, v, b in reliability_results.get('critical_lines', [])[:5]
            ]) if 'critical_lines' in reliability_results else None,
            
            html.H6("N-1 Contingency Analysis", className="mt-4"),
            html.P("Analysis of system behavior when critical lines are lost:"),
            html.Ul([
                html.Li([
                    f"Line {result['line'][0]}-{result['line'][1]}: ",
                    html.Span("Network remains connected", style={"color": "green"}) 
                    if result.get('network_still_connected', False) else
                    html.Span(f"Network splits, {result.get('isolated_nodes', 0)} nodes isolated", style={"color": "red"})
                ]) 
                for result in reliability_results.get('n_minus_1_analysis', [])
            ]) if 'n_minus_1_analysis' in reliability_results else None,
            
            html.Div([
                dcc.Graph(figure=reliability_results.get('reliability_visualization'))
            ]) if 'reliability_visualization' in reliability_results else None
        ])
        
    elif analysis_type == "congestion" and "congestion_analysis" in advanced_results:
        congestion_results = advanced_results["congestion_analysis"]
        
        if "congestion_stats" in congestion_results:
            stats = congestion_results["congestion_stats"]
            elements.extend([
                html.H5("Congestion Analysis Results", className="mt-4"),
                html.Hr(),
                html.P("Analysis of system bottlenecks and transmission constraints."),
                html.P([
                    html.Strong("Congested branches: "), 
                    f"{stats.get('congested_branches', 0)} ",
                    f"({stats.get('congestion_percentage', 0):.1f}% of network)"
                ]),
                html.P([
                    html.Strong("Average loading: "), 
                    f"{stats.get('average_loading', 0):.1f}%"
                ]),
                html.P([
                    html.Strong("Maximum loading: "), 
                    f"{stats.get('max_loading', 0):.1f}%"
                ]),
                
                html.H6("Loading Distribution", className="mt-3"),
                html.Div([
                    dcc.Graph(figure=congestion_results.get('loading_histogram'))
                ]) if 'loading_histogram' in congestion_results else None
            ])
            
            if 'congestion_map' in congestion_results:
                elements.append(html.H6("Congestion Map", className="mt-4"))
                elements.append(html.Div([
                    dcc.Graph(figure=congestion_results.get('congestion_map'))
                ]))
            
            if 'congested_lines' in congestion_results and congestion_results['congested_lines']:
                elements.append(html.H6("Most Congested Lines", className="mt-4"))
                
                # Create a table of congested lines
                from dash import dash_table
                
                congested_lines = congestion_results['congested_lines']
                table_data = [
                    {
                        "From Bus": line['from_bus'],
                        "To Bus": line['to_bus'],
                        "Loading (%)": f"{line['loading_percent']:.1f}%"
                    }
                    for line in congested_lines[:10]  # Show top 10 congested lines
                ]
                
                elements.append(dash_table.DataTable(
                    data=table_data,
                    columns=[
                        {"name": "From Bus", "id": "From Bus"},
                        {"name": "To Bus", "id": "To Bus"},
                        {"name": "Loading (%)", "id": "Loading (%)"}
                    ],
                    style_table={'overflowX': 'auto'},
                    style_cell={'textAlign': 'center'},
                    style_header={
                        'backgroundColor': 'rgb(230, 230, 230)',
                        'fontWeight': 'bold'
                    },
                    style_data_conditional=[
                        {
                            'if': {
                                'filter_query': '{Loading (%)} contains ">"'
                            },
                            'backgroundColor': 'rgba(255, 102, 102, 0.2)'
                        }
                    ]
                ))
    else:
        # Generic advanced analysis content
        elements.extend([
            html.P("Advanced analysis was performed on the power system data to provide deeper insights."),
            html.P("Please check the summary tab for more information on the analysis results.")
        ])
    
    return html.Div(elements)


def enhanced_pattern_matching_fallback(message: str, message_lower: str) -> str:
    """
    Enhanced fallback pattern matching with more sophisticated responses
    """
    import random
    from datetime import datetime
    
    if any(greeting in message_lower for greeting in ["hello", "hi", "hey", "greetings"]):
        greetings = [
            "Hello! I'm your Enhanced Power System Assistant with intelligent analysis capabilities. How can I help you today?",
            "Hi there! I'm ready to provide intelligent insights about your power system. What would you like to analyze?",
            "Greetings! I'm your AI-enhanced assistant for power system analysis and visualization. What specific aspect interests you?"
        ]
        return random.choice(greetings)
        
    elif any(word in message_lower for word in ["analyze", "analysis", "voltage", "violations"]):
        return ("🔍 I can perform intelligent voltage violation analysis with detailed insights and recommendations. "
               "I'll examine all buses, identify violations, assess risk levels, and provide specific corrective actions. "
               "Would you like me to run a comprehensive voltage analysis?")
        
    elif any(word in message_lower for word in ["statistics", "stats"]):
        return ("📊 I can perform advanced statistical analysis with intelligent interpretation. "
               "I'll provide key findings, risk assessments, and technical recommendations based on your system data. "
               "Ask me for any specific analysis: voltage, power flow, thermal, or contingency!")
        
    elif any(term in message_lower for term in ["slr", "static line rating", "static rating"]):
        return ("⚡ **Static Line Rating (SLR)** Analysis:\n\n"
               "SLR uses conservative fixed thermal limits based on worst-case weather assumptions (high temperature, low wind). "
               "While this ensures safety, it often significantly underutilizes transmission capacity - sometimes by 30-50% during favorable conditions. "
               "This leads to unnecessary congestion and higher operational costs.\n\n"
               "💡 Would you like me to analyze your system's SLR performance and identify potential capacity improvements?")
        
    elif any(term in message_lower for term in ["dlr", "dynamic line rating", "dynamic rating"]):
        return ("🌡️ **Dynamic Line Rating (DLR)** Analysis:\n\n"
               "DLR revolutionizes transmission by calculating real-time thermal limits using actual weather conditions. "
               "Key benefits include:\n"
               "• 10-30% capacity increase in favorable weather\n"
               "• Reduced congestion and operational costs\n"
               "• Enhanced grid flexibility and renewable integration\n"
               "• Maintained safety with real-time monitoring\n\n"
               "🔍 I can analyze how DLR would improve your specific system performance!")
        
    elif "compare" in message_lower and ("slr" in message_lower or "dlr" in message_lower):
        return ("📈 **SLR vs DLR Intelligent Comparison**:\n\n"
               "Based on typical power system analysis:\n"
               "• **Capacity**: DLR provides 10-30% higher transmission capacity\n"
               "• **Efficiency**: Reduces system losses by utilizing optimal paths\n"
               "• **Economics**: Lower operational costs, reduced need for new infrastructure\n"
               "• **Reliability**: Better contingency management with higher available capacity\n"
               "• **Integration**: Enables higher renewable energy penetration\n\n"
               "🎯 I can run a detailed comparison analysis on your specific system data!")
        
    elif any(word in message_lower for word in ["help", "what can you do", "capabilities"]):
        return ("🚀 **Enhanced AI Assistant Capabilities**:\n\n"
               "**🧠 Intelligent Analysis**:\n"
               "• Voltage violation analysis with risk assessment\n"
               "• Power flow analysis with loading insights\n"
               "• Thermal analysis with capacity optimization\n"
               "• Contingency analysis with reliability metrics\n"
               "• Economic analysis with efficiency recommendations\n\n"
               "**💡 Smart Features**:\n"
               "• Context-aware responses based on your questions\n"
               "• Technical explanations adapted to your expertise level\n"
               "• Statistical result interpretation with actionable insights\n"
               "• Comparative analysis between different scenarios\n\n"
               "Try asking: 'Analyze voltage violations' or 'Compare SLR vs DLR performance'!")
        
    elif any(word in message_lower for word in ["intelligent", "smart", "ai", "enhanced"]):
        return ("🧠 **About My Enhanced Intelligence**:\n\n"
               "I use advanced pattern recognition and power system domain expertise to:\n\n"
               "**🔍 Analyze Intent**: I understand what you're asking for, even with natural language\n"
               "**📊 Interpret Data**: I don't just show numbers - I explain what they mean\n"
               "**💡 Provide Insights**: I offer actionable recommendations based on analysis results\n"
               "**🎯 Context Awareness**: I remember our conversation and provide relevant follow-ups\n\n"
               "My responses adapt to your expertise level and provide both quantitative results and qualitative insights. "
               "Ask me anything about your power system!")
    
    else:
        # Enhanced general responses with helpful suggestions
        general_responses = [
            "I'm your Enhanced Power System Assistant with advanced analytical capabilities. I can provide intelligent insights about voltage analysis, power flow studies, thermal assessments, and contingency planning. What specific aspect would you like to explore?",
            "I specialize in intelligent power system analysis with context-aware responses. I can help with technical interpretations, comparative studies, and performance optimization. What kind of analysis interests you?",
            "I offer sophisticated power system intelligence beyond basic pattern matching. I can analyze your data, provide expert insights, and suggest improvements. What would you like to investigate?"
        ]
        
        # Add response variety to prevent repetition
        current_time = datetime.now().strftime("%H%M%S")
        selected_response = general_responses[int(current_time[-1]) % len(general_responses)]
        
        return f"{selected_response}\n\n💡 **Try asking**: 'Analyze voltage violations', 'Compare SLR vs DLR', or 'Show system health check'"