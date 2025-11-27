"""
RAG-Enhanced Floating Chat Interface
===================================

This module provides an enhanced floating chat interface that integrates
the RAG-based power system assistant with the existing Dash application.
It combines the power of LangChain RAG with Llama models to provide
intelligent, context-aware responses about power system data.

Key Features:
- Real-time database querying and analysis
- Vector-based document retrieval for context
- Power system domain expertise
- Statistical analysis and insights
- Interactive query suggestions
- Context-aware conversations
- Lazy loading for fast app startup

Integration:
- Seamlessly integrates with existing Dash application
- Maintains conversation history and context
- Provides visual feedback and typing indicators
- Supports follow-up questions and clarifications
- Loads AI models only when first used

Author: Power System Analysis Team
Date: September 2025
Version: 1.1 - Lazy Loading Optimization
"""

import dash
from dash import dcc, html, Input, Output, State, callback, clientside_callback
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading

# Global variables for lazy loading
_rag_assistant = None
_rag_loading = False
_rag_error = None

def create_lazy_rag_chat_component():
    """Create RAG chat component with lazy loading for performance"""
    return html.Div([
        # Chat interface that shows loading state initially
        html.Div(id='rag-chat-container', children=[
            html.Div([
                html.H5("🤖 Power System AI Assistant", className="mb-3"),
                html.P("RAG-enhanced assistant ready. Click to start!", 
                       className="text-muted"),
                dbc.Button("🚀 Initialize AI Assistant", 
                          id="init-rag-btn", 
                          color="primary", 
                          className="mb-3")
            ], className="text-center p-4")
        ]),
        
        # Hidden div to trigger lazy loading
        html.Div(id='rag-lazy-trigger', style={'display': 'none'}),
        
        # Store for chat state
        dcc.Store(id='rag-chat-history', data=[]),
        dcc.Store(id='rag-assistant-loaded', data=False),
    ])

# Import the RAG assistant lazily
def get_rag_assistant():
    """Lazy load the RAG assistant"""
    global _rag_assistant, _rag_loading, _rag_error
    
    if _rag_assistant is not None:
        return _rag_assistant
    
    if _rag_loading:
        return None
    
    if _rag_error:
        raise _rag_error
    
    try:
        _rag_loading = True
        print("🔄 Loading RAG assistant (lazy initialization)...")
        from rag_enhanced_chat_assistant import PowerSystemRAGAssistant, create_rag_assistant
        _rag_assistant = create_rag_assistant()
        print("✅ RAG assistant loaded successfully!")
        return _rag_assistant
    except Exception as e:
        _rag_error = e
        print(f"❌ Failed to load RAG assistant: {e}")
        raise e
    finally:
        _rag_loading = False

# Original RAG loading (kept for backward compatibility)
try:
    from rag_enhanced_chat_assistant import PowerSystemRAGAssistant, create_rag_assistant
    RAG_AVAILABLE = True
    print("✅ RAG assistant modules available (lazy loading enabled)")
except ImportError as e:
    print(f"⚠️ RAG assistant not available: {e}")
    print("🔄 Using fallback mode without RAG capabilities...")
    PowerSystemRAGAssistant = None
    create_rag_assistant = None
    RAG_AVAILABLE = False

# Import fallback components
try:
    from floating_chat import create_floating_chat_component
    FALLBACK_CHAT_AVAILABLE = True
    print("✅ Fallback chat component available")
except ImportError as e:
    print(f"⚠️ Fallback chat also not available: {e}")
    FALLBACK_CHAT_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGEnhancedFloatingChat:
    """
    Enhanced floating chat interface with RAG capabilities.
    
    This class provides a sophisticated chat interface that combines
    the power of retrieval-augmented generation with domain-specific
    knowledge about power systems.
    """
    
    def __init__(self, app: dash.Dash, db_path: str = "data.db"):
        """
        Initialize the RAG-enhanced chat interface.
        
        Args:
            app: Dash application instance
            db_path: Path to the power system database
        """
        self.app = app
        self.db_path = db_path
        self.rag_assistant = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Initialize RAG assistant
        self._initialize_rag_assistant()
        
        # Register callbacks
        self._register_callbacks()
        
        # Conversation history
        self.conversation_history = []
        
        logger.info("RAG-enhanced floating chat initialized")
    
    def _initialize_rag_assistant(self):
        """Initialize the RAG assistant with error handling and timeout."""
        try:
            if create_rag_assistant:
                logger.info("Starting RAG assistant initialization...")
                # Use a separate thread with timeout to avoid blocking
                def init_rag():
                    return create_rag_assistant(self.db_path)
                
                # Try to initialize with a timeout
                future = self.executor.submit(init_rag)
                try:
                    self.rag_assistant = future.result(timeout=30)  # 30 second timeout
                    logger.info("RAG assistant initialized successfully")
                except Exception as timeout_error:
                    logger.warning(f"RAG initialization timed out or failed: {timeout_error}")
                    self.rag_assistant = None
            else:
                logger.warning("RAG assistant not available - using fallback mode")
                self.rag_assistant = None
        except Exception as e:
            logger.error(f"Failed to initialize RAG assistant: {e}")
            self.rag_assistant = None

# Export the main class and function even if RAG is not available
if not RAG_AVAILABLE:
    class RAGEnhancedFloatingChat:
        """Fallback class when RAG is not available"""
        def __init__(self, app, db_path):
            self.app = app
            self.db_path = db_path
            print("⚠️ RAG not available - using basic fallback")
        
        def get_chat_layout(self):
            """Return a simple chat interface"""
            return html.Div([
                html.H4("AI Assistant (Fallback Mode)", className="mb-3"),
                html.P("RAG features unavailable. Basic functionality active.", 
                       className="text-muted mb-3"),
                dbc.Card([
                    dbc.CardBody([
                        dcc.Textarea(
                            id="fallback-chat-input",
                            placeholder="Ask about your power system data...",
                            style={"width": "100%", "height": "100px", "resize": "vertical"}
                        ),
                        dbc.Button("Send", id="fallback-chat-send", className="mt-2"),
                        html.Div(id="fallback-chat-output", className="mt-3")
                    ])
                ])
            ], style={"position": "fixed", "bottom": "20px", "right": "20px", 
                      "width": "350px", "z-index": "1000"})

def create_rag_assistant(db_path="data.db"):
    """
    Create a RAG assistant instance with fallback.
    
    Args:
        db_path: Path to the database
        
    Returns:
        PowerSystemRAGAssistant instance or None
    """
    if RAG_AVAILABLE and PowerSystemRAGAssistant:
        try:
            return PowerSystemRAGAssistant(db_path)
        except Exception as e:
            print(f"⚠️ Failed to create RAG assistant: {e}")
            return None
    else:
        print("⚠️ RAG assistant not available")
        return None
    
    def get_chat_layout(self) -> html.Div:
        """
        Create the enhanced chat interface layout.
        
        Returns:
            Dash HTML component containing the chat interface
        """
        return html.Div([
            # Chat Toggle Button
            dbc.Button(
                [
                    html.I(className="fas fa-comments me-2"),
                    "AI Assistant"
                ],
                id="chat-toggle-btn",
                className="position-fixed chat-toggle-button",
                style={
                    'bottom': '20px',
                    'right': '20px',
                    'z-index': '9999',  # Increased z-index
                    'border-radius': '25px',
                    'box-shadow': '0 4px 12px rgba(0,0,0,0.15)',
                    'position': 'fixed',  # Ensure it's fixed position
                    'display': 'block',    # Ensure it's visible
                    'cursor': 'pointer',   # Ensure cursor changes
                    'min-width': '140px',  # Ensure minimum width
                    'pointer-events': 'auto'  # Ensure it can be clicked
                },
                color="primary",
                size="lg",
                n_clicks=0  # Initialize click count
            ),
            
            # Enhanced Chat Window
            dbc.Card([
                # Chat Header
                dbc.CardHeader([
                    html.Div([
                        html.H5([
                            html.I(className="fas fa-robot me-2"),
                            "Power System AI Assistant"
                        ], className="mb-0 text-white"),
                        html.Small("RAG-Enhanced Analysis", className="text-white-50")
                    ], className="d-flex justify-content-between align-items-center"),
                    dbc.Button(
                        html.I(className="fas fa-times"),
                        id="chat-close-btn",
                        size="sm",
                        color="link",
                        className="text-white p-1"
                    )
                ], className="bg-primary"),
                
                # Chat Messages Area
                dbc.CardBody([
                    html.Div(
                        id="chat-messages",
                        style={
                            'height': '400px',
                            'overflow-y': 'auto',
                            'border': '1px solid #dee2e6',
                            'border-radius': '8px',
                            'padding': '15px',
                            'background-color': '#f8f9fa'
                        }
                    ),
                    
                    # System Status
                    dbc.Alert(
                        id="chat-status",
                        children="RAG system ready for intelligent analysis",
                        color="success",
                        className="mt-2 mb-2",
                        style={'padding': '8px 12px', 'font-size': '0.875rem'}
                    ),
                    
                    # Quick Action Buttons
                    html.Div([
                        dbc.ButtonGroup([
                            dbc.Button(
                                "System Stats",
                                id="btn-system-stats",
                                size="sm",
                                outline=True,
                                color="info"
                            ),
                            dbc.Button(
                                "Voltage Analysis", 
                                id="btn-voltage-analysis",
                                size="sm",
                                outline=True,
                                color="warning"
                            ),
                            dbc.Button(
                                "Thermal Analysis",
                                id="btn-thermal-analysis", 
                                size="sm",
                                outline=True,
                                color="danger"
                            ),
                            dbc.Button(
                                "Suggestions",
                                id="btn-suggestions",
                                size="sm", 
                                outline=True,
                                color="secondary"
                            )
                        ], size="sm", className="w-100")
                    ], className="mb-3"),
                    
                    # Chat Input Area
                    dbc.InputGroup([
                        dbc.Input(
                            id="chat-input",
                            placeholder="Ask about power system analysis...",
                            type="text",
                            className="chat-input"
                        ),
                        dbc.Button(
                            html.I(className="fas fa-paper-plane"),
                            id="chat-send-btn",
                            color="primary",
                            n_clicks=0
                        )
                    ])
                ])
            ], 
            id="chat-window",
            className="position-fixed chat-window d-none",
            style={
                'bottom': '80px',
                'right': '20px',
                'width': '450px',
                'z-index': '999',
                'box-shadow': '0 8px 32px rgba(0,0,0,0.2)',
                'border-radius': '12px'
            }),
            
            # Hidden components for state management
            dcc.Store(id="chat-history-store", data=[]),
            dcc.Store(id="rag-context-store", data={}),
            dcc.Interval(id="typing-indicator-interval", interval=500, disabled=True),
            
        ], id="chat-container")
    
    def _register_callbacks(self):
        """Register all chat-related callbacks."""
        
        @self.app.callback(
            Output("chat-window", "className"),
            [Input("chat-toggle-btn", "n_clicks"),
             Input("chat-close-btn", "n_clicks")],
            [State("chat-window", "className")]
        )
        def toggle_chat_window(toggle_clicks, close_clicks, current_class):
            """Toggle chat window visibility."""
            ctx = dash.callback_context
            if not ctx.triggered:
                return current_class or "position-fixed chat-window d-none"
            
            # Add debug logging
            trigger_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None
            logger.info(f"Chat toggle triggered by: {trigger_id}, toggle_clicks: {toggle_clicks}, close_clicks: {close_clicks}")
            logger.info(f"Current class: {current_class}")
                
            # Ensure we have a proper current_class
            if not current_class:
                current_class = "position-fixed chat-window d-none"
                
            if "d-none" in current_class:
                new_class = "position-fixed chat-window"
            else:
                new_class = "position-fixed chat-window d-none"
            
            logger.info(f"New class: {new_class}")
            return new_class
        
        @self.app.callback(
            [Output("chat-messages", "children"),
             Output("chat-history-store", "data"),
             Output("chat-status", "children"),
             Output("chat-status", "color"),
             Output("chat-input", "value")],
            [Input("chat-send-btn", "n_clicks"),
             Input("btn-system-stats", "n_clicks"),
             Input("btn-voltage-analysis", "n_clicks"), 
             Input("btn-thermal-analysis", "n_clicks"),
             Input("btn-suggestions", "n_clicks")],
            [State("chat-input", "value"),
             State("chat-history-store", "data")]
        )
        def handle_chat_interaction(send_clicks, stats_clicks, voltage_clicks, 
                                  thermal_clicks, suggestions_clicks, 
                                  input_value, chat_history):
            """Handle all chat interactions and generate responses."""
            ctx = dash.callback_context
            if not ctx.triggered:
                return self._get_welcome_messages(), [], "Ready", "success", ""
            
            trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
            
            # Determine the query based on trigger
            query = ""
            if trigger_id == "chat-send-btn" and input_value:
                query = input_value
            elif trigger_id == "btn-system-stats":
                query = "Show me comprehensive system statistics and overview"
            elif trigger_id == "btn-voltage-analysis":
                query = "Analyze voltage violations and provide voltage profile insights"
            elif trigger_id == "btn-thermal-analysis": 
                query = "Analyze thermal violations and line loading conditions"
            elif trigger_id == "btn-suggestions":
                query = "What are some useful analysis questions I can ask?"
            
            if not query:
                return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
            
            # Add user message to history
            chat_history = chat_history or []
            chat_history.append({
                "type": "user",
                "content": query,
                "timestamp": datetime.now().isoformat()
            })
            
            # Generate response
            try:
                response_data = self._generate_rag_response(query)
                
                # Add assistant response to history
                chat_history.append({
                    "type": "assistant",
                    "content": response_data["response"],
                    "metadata": response_data.get("metadata", {}),
                    "timestamp": datetime.now().isoformat()
                })
                
                # Generate messages display
                messages = self._format_chat_messages(chat_history)
                status = "Response generated successfully"
                status_color = "success"
                
            except Exception as e:
                logger.error(f"Error generating response: {e}")
                chat_history.append({
                    "type": "error",
                    "content": "I encountered an error processing your request. Please try again.",
                    "timestamp": datetime.now().isoformat()
                })
                messages = self._format_chat_messages(chat_history)
                status = f"Error: {str(e)}"
                status_color = "danger"
            
            return messages, chat_history, status, status_color, ""
        
        # Enable Enter key for sending messages
        clientside_callback(
            """
            function(n_intervals) {
                document.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter' && document.activeElement.id === 'chat-input') {
                        document.getElementById('chat-send-btn').click();
                    }
                });
                return '';
            }
            """,
            Output("chat-input", "className"),
            Input("typing-indicator-interval", "n_intervals")
        )
    
    def _generate_rag_response(self, query: str) -> Dict[str, Any]:
        """
        Generate response using RAG assistant.
        
        Args:
            query: User's question
            
        Returns:
            Dictionary containing response and metadata
        """
        if self.rag_assistant:
            try:
                response = self.rag_assistant.chat(query)
                return {
                    "response": response.get("response", "I couldn't generate a response."),
                    "metadata": {
                        "context_sources": response.get("context_sources", []),
                        "statistics": response.get("statistics"),
                        "timestamp": response.get("timestamp")
                    }
                }
            except Exception as e:
                logger.error(f"RAG assistant error: {e}")
                return {"response": "I encountered an error with the AI system. Please try again."}
        else:
            # Fallback response when RAG is not available
            return self._generate_fallback_response(query)
    
    def _generate_fallback_response(self, query: str) -> Dict[str, Any]:
        """
        Generate fallback response when RAG system is not available.
        
        Args:
            query: User's question
            
        Returns:
            Dictionary containing fallback response
        """
        fallback_responses = {
            "statistics": "I can provide system statistics, but the RAG system is currently unavailable. Please check the setup.",
            "voltage": "For voltage analysis, you can query the BaseBusData table for voltage magnitudes (VM column).",
            "thermal": "For thermal analysis, check the BaseBranchData table comparing MVA flows with RATE limits.",
            "default": "I'm currently running in fallback mode. The RAG system needs to be properly configured for advanced analysis."
        }
        
        query_lower = query.lower()
        if "statistic" in query_lower or "overview" in query_lower:
            response = fallback_responses["statistics"]
        elif "voltage" in query_lower:
            response = fallback_responses["voltage"]
        elif "thermal" in query_lower or "line" in query_lower:
            response = fallback_responses["thermal"]
        else:
            response = fallback_responses["default"]
            
        return {"response": response, "metadata": {}}
    
    def _format_chat_messages(self, chat_history: List[Dict]) -> List[html.Div]:
        """
        Format chat history into displayable messages.
        
        Args:
            chat_history: List of message dictionaries
            
        Returns:
            List of HTML components for display
        """
        messages = []
        
        for msg in chat_history:
            if msg["type"] == "user":
                messages.append(
                    html.Div([
                        html.Div([
                            html.Strong("You: "),
                            html.Span(msg["content"])
                        ], className="user-message p-3 mb-2 bg-primary text-white rounded")
                    ], className="text-end")
                )
            elif msg["type"] == "assistant":
                # Format assistant message with metadata if available
                content_parts = [
                    html.Div([
                        html.I(className="fas fa-robot me-2"),
                        html.Strong("AI Assistant: ")
                    ]),
                    html.P(msg["content"], className="mb-2")
                ]
                
                # Add statistics if available
                metadata = msg.get("metadata", {})
                if metadata.get("statistics"):
                    content_parts.append(self._format_statistics_display(metadata["statistics"]))
                
                messages.append(
                    html.Div([
                        html.Div(content_parts, 
                               className="assistant-message p-3 mb-2 bg-light rounded border-start border-primary border-4")
                    ])
                )
            elif msg["type"] == "error":
                messages.append(
                    html.Div([
                        html.Div([
                            html.I(className="fas fa-exclamation-triangle me-2"),
                            html.Strong("Error: "),
                            html.Span(msg["content"])
                        ], className="error-message p-3 mb-2 bg-danger text-white rounded")
                    ])
                )
        
        return messages
    
    def _format_statistics_display(self, statistics: Dict[str, Any]) -> html.Div:
        """
        Format statistics data for display.
        
        Args:
            statistics: Dictionary containing system statistics
            
        Returns:
            HTML component displaying statistics
        """
        stat_cards = []
        
        for category, stats in statistics.items():
            if stats:  # Only show non-empty statistics
                card_content = []
                for key, value in stats.items():
                    if isinstance(value, (int, float)):
                        if isinstance(value, float):
                            value = f"{value:.2f}"
                        card_content.append(
                            html.Li([html.Strong(f"{key.replace('_', ' ').title()}: "), str(value)])
                        )
                
                if card_content:
                    stat_cards.append(
                        dbc.Card([
                            dbc.CardHeader(html.H6(category.replace('_', ' ').title(), className="mb-0")),
                            dbc.CardBody(html.Ul(card_content, className="mb-0"))
                        ], className="mb-2")
                    )
        
        if stat_cards:
            return html.Div([
                html.Hr(),
                html.H6("System Statistics:", className="text-muted"),
                html.Div(stat_cards)
            ])
        else:
            return html.Div()
    
    def _get_welcome_messages(self) -> List[html.Div]:
        """
        Get welcome messages for the chat interface.
        
        Returns:
            List of welcome message components
        """
        return [
            html.Div([
                html.Div([
                    html.I(className="fas fa-robot me-2"),
                    html.Strong("AI Assistant: "),
                    html.P([
                        "Welcome to the Power System AI Assistant! I'm powered by RAG technology and have deep knowledge of power systems analysis. ",
                        html.Br(), html.Br(),
                        "I can help you with:",
                        html.Ul([
                            html.Li("System statistics and overviews"),
                            html.Li("Voltage analysis and violations"),
                            html.Li("Thermal analysis and line loading"),
                            html.Li("Contingency analysis results"),
                            html.Li("SLR and DLR analysis insights"),
                            html.Li("Database queries and explanations")
                        ]),
                        "Try the quick action buttons above or ask me anything about your power system data!"
                    ], className="mb-0")
                ], className="assistant-message p-3 mb-2 bg-light rounded border-start border-primary border-4")
            ])
        ]


# Integration function for existing applications
def add_rag_chat_to_app(app: dash.Dash, db_path: str = "data.db"):
    """
    Add RAG-enhanced chat functionality to existing Dash application with fallback support.
    
    Args:
        app: Dash application instance
        db_path: Path to power system database
        
    Returns:
        RAGEnhancedFloatingChat instance or fallback component
    """
    try:
        if RAG_AVAILABLE:
            # Use full RAG functionality
            chat_interface = RAGEnhancedFloatingChat(app, db_path)
            print("✅ RAG-enhanced chat interface added successfully")
            return chat_interface
        elif FALLBACK_CHAT_AVAILABLE:
            # Use basic floating chat as fallback
            from floating_chat import create_floating_chat_component
            chat_component = create_floating_chat_component()
            print("🔄 Using basic floating chat as fallback")
            return chat_component
        else:
            print("❌ No chat interface available - creating simple fallback")
            return SimpleRAGFallback(app, db_path)
            
    except Exception as e:
        print(f"⚠️ Error setting up chat interface: {e}")

# Lazy loading callback for RAG initialization
def register_lazy_rag_callbacks(app):
    """Register callbacks for lazy RAG loading"""
    
    @app.callback(
        [Output('rag-chat-container', 'children'),
         Output('rag-assistant-loaded', 'data')],
        [Input('init-rag-btn', 'n_clicks')],
        [State('rag-assistant-loaded', 'data')],
        prevent_initial_call=True
    )
    def initialize_rag_assistant(n_clicks, already_loaded):
        if n_clicks is None or already_loaded:
            return dash.no_update, dash.no_update
        
        try:
            # Show loading state
            loading_content = html.Div([
                html.H5("🤖 Power System AI Assistant", className="mb-3"),
                dbc.Spinner(html.Div([
                    html.P("Loading AI models...", className="mb-2"),
                    html.Small("This may take 10-20 seconds for first-time initialization", 
                              className="text-muted")
                ]), color="primary"),
            ], className="text-center p-4")
            
            # Initialize RAG assistant in background
            assistant = get_rag_assistant()
            
            # Create full chat interface
            full_chat_interface = create_full_rag_interface()
            
            return full_chat_interface, True
            
        except Exception as e:
            error_content = html.Div([
                html.H5("❌ AI Assistant Error", className="mb-3"),
                html.P(f"Failed to load: {str(e)}", className="text-danger"),
                dbc.Button("🔄 Try Again", id="init-rag-btn", color="warning")
            ], className="text-center p-4")
            
            return error_content, False

def create_full_rag_interface():
    """Create the full RAG chat interface after models are loaded"""
    return html.Div([
        html.H5("🤖 Power System AI Assistant", className="mb-3"),
        html.Div(id="rag-chat-messages", className="chat-messages mb-3"),
        dbc.InputGroup([
            dbc.Input(id="rag-chat-input", placeholder="Ask about power system data...", 
                     type="text"),
            dbc.Button("Send", id="rag-send-btn", color="primary")
        ])
    ])


class SimpleRAGFallback:
    """Simple fallback when neither RAG nor floating chat is available"""
    def __init__(self, app, db_path):
        self.app = app
        self.db_path = db_path
        print("🔄 Using simple RAG fallback")
    
    def get_chat_layout(self):
        """Return a simple chat interface"""
        return html.Div([
            html.H4("AI Assistant (Fallback Mode)", className="mb-3"),
            html.P("Advanced features unavailable. Basic functionality active.", 
                   className="text-muted mb-3"),
            dbc.Card([
                dbc.CardBody([
                    dcc.Textarea(
                        id="fallback-chat-input",
                        placeholder="Ask about your power system data...",
                        style={"width": "100%", "height": "100px", "resize": "vertical"}
                    ),
                    dbc.Button("Send", id="fallback-chat-send", className="mt-2"),
                    html.Div(id="fallback-chat-output", className="mt-3")
                ])
            ])
        ], style={"position": "fixed", "bottom": "20px", "right": "20px", 
                  "width": "350px", "z-index": "1000"})


def test_rag_chat():
    """Test function for the RAG chat interface."""
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    
    # Add chat to app
    chat = add_rag_chat_to_app(app)
    
    # Simple test layout
    app.layout = html.Div([
        html.H1("Power System Analysis Dashboard"),
        html.P("This is a test layout with RAG-enhanced chat."),
        chat.get_chat_layout()
    ])
    
    return app


if __name__ == "__main__":
    test_app = test_rag_chat()
    test_app.run_server(debug=True, port=8055)