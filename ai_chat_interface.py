"""
Dash Integration for Conversational AI Assistant
===============================================

This module integrates the conversational AI assistant into the existing Dash application
for power system analysis, providing a chat interface alongside the visualization dashboard.

Features:
- Chat interface integrated with main dashboard
- Real-time conversation with AI assistant  
- Context sharing with current analysis state
- Export conversation history
- Adjustable expertise level settings
- LLM-enhanced responses and visualization detection

Author: Power System Analysis Team
Date: September 2025
"""

import dash
from dash import dcc, html, Input, Output, State, callback, no_update
import dash_bootstrap_components as dbc
from datetime import datetime
import json
import uuid
import os
from typing import Dict, List, Optional, Union
import logging

# Import our AI assistant (with fallback handling)
try:
    from ai_assistant import ConversationalAIAssistant, QueryType
    AI_ASSISTANT_AVAILABLE = True
    print("✅ Base AI assistant available")
    
    # Try to import LLM enhanced version
    try:
        from llm_assistant import LLMEnhancedAssistant
        LLM_AVAILABLE = True
        print("✅ OpenAI LLM Enhanced Assistant available")
    except ImportError as e:
        LLM_AVAILABLE = False
        print(f"⚠️ OpenAI LLM Enhanced Assistant not available: {e}")
    
    # Try to import Llama enhanced version
    try:
        from llama_assistant import LlamaEnhancedAssistant
        LLAMA_AVAILABLE = True
        print("✅ Llama Enhanced Assistant available")
    except ImportError as e:
        LLAMA_AVAILABLE = False
        print(f"⚠️ Llama Enhanced Assistant not available: {e}")
    
    # Try to import intelligent chat engine
    try:
        from intelligent_chat_engine import PowerSystemIntelligentAssistant
        INTELLIGENT_CHAT_AVAILABLE = True
        print("✅ Intelligent Chat Engine available")
    except ImportError as e:
        INTELLIGENT_CHAT_AVAILABLE = False
        print(f"⚠️ Intelligent Chat Engine not available: {e}")
        
except ImportError as e:
    AI_ASSISTANT_AVAILABLE = False
    LLM_AVAILABLE = False
    LLAMA_AVAILABLE = False
    INTELLIGENT_CHAT_AVAILABLE = False
    print(f"❌ No AI assistant modules available: {e}")
    
    # Create fallback classes
    class ConversationalAIAssistant:
        def __init__(self, *args, **kwargs):
            self.responses = ["AI Assistant not available. Please check your installation."]
        
        def generate_response(self, query, *args, **kwargs):
            return "AI Assistant is not properly configured."
    
    class QueryType:
        ANALYSIS = "analysis"
        EXPLANATION = "explanation"
        GENERAL = "general"

# Try to import mock LLM version (independently of other assistants)
try:
    from mock_llm import MockLLMAssistant, get_assistant
    MOCK_LLM_AVAILABLE = True
    print("✅ Mock LLM Assistant available")
except ImportError as e:
    MOCK_LLM_AVAILABLE = False
    print(f"⚠️ Mock LLM Assistant not available: {e}")
    
    # Create fallback mock classes if needed
    class MockLLMAssistant:
        def __init__(self, *args, **kwargs):
            self.responses = ["Mock LLM Assistant not available."]
        
        def generate_response(self, query, *args, **kwargs):
            return "Mock LLM Assistant is not properly configured."
        
        def set_expertise_level(self, level):
            pass

# Determine overall AI availability
AI_AVAILABLE = AI_ASSISTANT_AVAILABLE or MOCK_LLM_AVAILABLE

logger = logging.getLogger(__name__)


class ChatInterface:
    """Chat interface component for Dash application"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.ai_assistant = None
        self.active_sessions: Dict[str, str] = {}  # client_id -> session_id
        self.using_llm = False
        
        if AI_AVAILABLE:
            try:
                # Get expertise level from environment
                expertise = os.environ.get("DLR_EXPERTISE_LEVEL", "expert")
                
                # Check for mock LLM mode
                use_mock_llm = os.environ.get("DLR_MOCK_LLM") == "1"
                
                # Check for Llama mode
                use_llama = os.environ.get("DLR_USE_LLAMA") == "1"
                
                # Check if LLM should be disabled
                disable_llm = os.environ.get("DLR_DISABLE_LLM") == "1"
                
                if use_mock_llm and MOCK_LLM_AVAILABLE:
                    # Use mock LLM assistant
                    self.ai_assistant = MockLLMAssistant(db_path)
                    self.using_llm = True  # We treat it as if LLM is available
                    self.ai_assistant.set_expertise_level(expertise)
                    logger.info(f"Mock LLM-Enhanced AI Assistant initialized (rule-based enhancement) with {expertise} expertise level")
                
                # Try to initialize Llama assistant if requested
                elif use_llama and LLAMA_AVAILABLE and not disable_llm:
                    llama_api_url = os.environ.get("LLAMA_API_URL")
                    llama_api_key = os.environ.get("LLAMA_API_KEY")
                    llama_model = os.environ.get("LLAMA_MODEL", "llama-3-70b-chat")
                    
                    try:
                        self.ai_assistant = LlamaEnhancedAssistant(
                            db_path, 
                            api_url=llama_api_url,
                            api_key=llama_api_key,
                            model=llama_model
                        )
                        self.using_llm = True
                        self.ai_assistant.set_expertise_level(expertise)
                        logger.info(f"Llama-Enhanced AI Assistant initialized successfully with model {llama_model} and {expertise} expertise level")
                    except Exception as e:
                        logger.error(f"Failed to initialize Llama-Enhanced Assistant: {e}")
                        logger.info("Falling back to standard AI Assistant")
                        self.ai_assistant = ConversationalAIAssistant(db_path)
                
                # Try to initialize the OpenAI LLM-enhanced assistant if not in mock mode or Llama mode
                elif LLM_AVAILABLE and not disable_llm and not use_llama:
                    # Check if API key is available from environment or config
                    api_key = os.environ.get("OPENAI_API_KEY")
                    
                    # If no environment variable, try to read from config file
                    if not api_key:
                        try:
                            import json
                            if os.path.exists("config.json"):
                                with open("config.json", "r") as f:
                                    config = json.load(f)
                                    api_key = config.get("ai_settings", {}).get("openai_api_key")
                                    if api_key and api_key != "REPLACE_WITH_YOUR_API_KEY":
                                        logger.info("Using OpenAI API key from config.json")
                                    else:
                                        api_key = None
                        except Exception as e:
                            logger.warning(f"Failed to read API key from config: {e}")
                    
                    if api_key:
                        try:
                            # Get model from environment if available, otherwise from config, otherwise default
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
                            
                            self.ai_assistant = LLMEnhancedAssistant(db_path, api_key=api_key, model=model)
                            self.using_llm = True
                            self.ai_assistant.set_expertise_level(expertise)
                            logger.info(f"OpenAI LLM-Enhanced AI Assistant initialized successfully with model {model} and {expertise} expertise level")
                        except Exception as e:
                            logger.error(f"Failed to initialize OpenAI LLM-Enhanced Assistant: {e}")
                            logger.info("Falling back to standard AI Assistant")
                            self.ai_assistant = ConversationalAIAssistant(db_path)
                    else:
                        logger.info("No API key available for OpenAI LLM. Using standard AI Assistant")
                        self.ai_assistant = ConversationalAIAssistant(db_path)
                else:
                    # Use standard AI Assistant
                    self.ai_assistant = ConversationalAIAssistant(db_path)
                    self.ai_assistant.set_expertise_level(expertise)
                    logger.info(f"AI Assistant initialized successfully with {expertise} expertise level")
            except Exception as e:
                logger.error(f"Failed to initialize AI Assistant: {e}")
                self.ai_assistant = None
    
    def create_chat_layout(self) -> dbc.Card:
        """Create the chat interface layout"""
        
        # Header with settings
        header = dbc.CardHeader([
            dbc.Row([
                dbc.Col([
                    html.H5("🤖 AI Power System Assistant", className="mb-0"),
                    html.Small("Ask me anything about DLR, SLR, and power system analysis", 
                              className="text-muted")
                ], width=8),
                dbc.Col([
                    dbc.ButtonGroup([
                        dbc.Button("Settings", id="chat-settings-btn", size="sm", outline=True),
                        dbc.Button("Export", id="chat-export-btn", size="sm", outline=True),
                        dbc.Button("Clear", id="chat-clear-btn", size="sm", outline=True, color="warning")
                    ])
                ], width=4, className="text-end")
            ])
        ])
        
        # Chat messages area
        chat_area = html.Div(
            id="chat-messages",
            children=self._get_welcome_message(),
            style={
                "height": "400px",
                "overflowY": "auto",
                "padding": "10px",
                "backgroundColor": "#f8f9fa",
                "border": "1px solid #dee2e6",
                "borderRadius": "0.375rem"
            }
        )
        
        # Input area
        input_area = dbc.Row([
            dbc.Col([
                dbc.InputGroup([
                    dbc.Input(
                        id="chat-input",
                        placeholder="Ask me about DLR, SLR, contingency analysis, or any power system topic...",
                        type="text"
                    ),
                    dbc.Button(
                        "Send",
                        id="chat-send-btn",
                        color="primary",
                        n_clicks=0
                    )
                ])
            ], width=12)
        ], className="mt-2")
        
        # Settings modal
        settings_modal = dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("AI Assistant Settings")),
            dbc.ModalBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Expertise Level:"),
                        dcc.Dropdown(
                            id="expertise-dropdown",
                            options=[
                                {"label": "Beginner - Simple explanations", "value": "beginner"},
                                {"label": "Intermediate - Balanced detail", "value": "intermediate"},
                                {"label": "Expert - Technical precision", "value": "expert"}
                            ],
                            value=os.environ.get("DLR_EXPERTISE_LEVEL", "expert")
                        )
                    ], width=12),
                ], className="mb-3"),
                
                # LLM Settings (only shown if using_llm is True)
                dbc.Row([
                    dbc.Col([
                        dbc.Label("LLM Settings:", className="fw-bold"),
                        html.Hr(className="my-1")
                    ], width=12)
                ], className="mb-2", style={"display": "block" if self.using_llm else "none"}),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("LLM Model:"),
                        dcc.Dropdown(
                            id="llm-model-dropdown",
                            options=[
                                {"label": "GPT-3.5 Turbo (Fast)", "value": "gpt-3.5-turbo"},
                                {"label": "GPT-4 (Powerful)", "value": "gpt-4"},
                            ],
                            value="gpt-3.5-turbo",
                            disabled=not self.using_llm
                        )
                    ], width=12),
                ], className="mb-3", style={"display": "block" if self.using_llm else "none"}),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("LLM API Key:"),
                        dbc.Input(
                            id="api-key-input",
                            type="password",
                            placeholder="Enter API Key (will be saved in environment)",
                            disabled=not self.using_llm
                        ),
                        dbc.FormText("Leave blank to use the current API key"),
                    ], width=12),
                ], className="mb-3", style={"display": "block" if self.using_llm else "none"}),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Current Context:"),
                        html.Div(id="context-display", className="p-2 bg-light rounded")
                    ], width=12)
                ])
            ]),
            dbc.ModalFooter([
                dbc.Button("Save Settings", id="save-settings-btn", color="primary"),
                dbc.Button("Close", id="close-settings-btn", color="secondary")
            ])
        ], id="settings-modal", is_open=False)
        
        # Check if we're using mock LLM
        is_mock_llm = self.using_llm and os.environ.get("DLR_MOCK_LLM") == "1"
        
        # Status indicator
        status_indicator = html.Div([
            html.Span("●", id="ai-status-indicator", style={"color": "green" if AI_AVAILABLE else "red"}),
            html.Span(f" AI Assistant {'Online' if AI_AVAILABLE else 'Offline'}", 
                     className="ms-1 small text-muted"),
            html.Br() if self.using_llm else None,
            html.Span("●", id="llm-status-indicator", 
                     style={"color": "purple" if is_mock_llm else "blue" if self.using_llm else "gray"}) if AI_AVAILABLE else None,
            html.Span(f" {'Mock LLM' if is_mock_llm else 'LLM Enhanced'}", 
                    className="ms-1 small text-muted") if AI_AVAILABLE else None
        ])
        
        # Complete chat card
        chat_card = dbc.Card([
            header,
            dbc.CardBody([
                chat_area,
                input_area,
                status_indicator,
                settings_modal
            ])
        ], className="h-100")
        
        return chat_card
    
    def _get_welcome_message(self) -> List:
        """Get welcome message for new chat session"""
        # Check if we're using mock LLM
        is_mock_llm = self.using_llm and os.environ.get("DLR_MOCK_LLM") == "1"
        
        # Set appropriate enhancement text
        if self.using_llm:
            llm_enhancement = " (with Mock LLM)" if is_mock_llm else " (with LLM Enhancement)"
        else:
            llm_enhancement = ""
            
        return [
            html.Div([
                html.Div([
                    html.Strong(f"🤖 AI Assistant{llm_enhancement}"),
                    html.Small(" • Just now", className="text-muted ms-2")
                ], className="d-flex justify-content-between align-items-center"),
                html.P([
                    "Welcome! I'm your AI assistant for power system analysis. I can help you with:",
                    html.Br(),
                    "• Dynamic Line Rating (DLR) and Static Line Rating (SLR) analysis",
                    html.Br(), 
                    "• Contingency studies and risk assessment",
                    html.Br(),
                    "• Economic impact and optimization strategies",
                    html.Br(),
                    "• Data interpretation and technical explanations",
                    html.Br(),
                    "• " + ("Enhanced visualization detection and generation" if self.using_llm else 
                           "Visualization recommendations"),
                    html.Br(), html.Br(),
                    html.Strong("Try asking: "),
                    html.Em("\"Explain the difference between SLR and DLR\" or \"Show me a heatmap of congestion\"")
                ], className="mb-0")
            ], className="chat-message assistant-message p-3 mb-2 rounded", 
               style={"backgroundColor": "#e3f2fd" if not self.using_llm else 
                     ("#e3f8ff" if is_mock_llm else "#e3f5ff")})
        ]
    
    def register_callbacks(self, app: dash.Dash, base_case_state_id: str = "dropdown-contingency"):
        """Register chat callbacks with the Dash app"""
        
        @app.callback(
            [Output("chat-messages", "children"),
             Output("chat-input", "value")],
            [Input("chat-send-btn", "n_clicks"),
             Input("chat-input", "n_submit")],
            [State("chat-input", "value"),
             State("chat-messages", "children"),
             State("expertise-dropdown", "value"),
             State(base_case_state_id, "value")]
        )
        def handle_chat_message(send_clicks, input_submit, message, current_messages, 
                              expertise_level, current_base_case):
            """Handle new chat messages"""
            if not message or not message.strip():
                return no_update, no_update
            
            # Get or create client session
            client_id = self._get_client_id()
            session_id = self._get_or_create_session(client_id, expertise_level or "intermediate")
            
            # Add user message
            user_msg = self._create_message_div(message, "user")
            updated_messages = (current_messages or []) + [user_msg]
            
            # Generate AI response
            if self.ai_assistant:
                try:
                    # Update context with current dashboard state
                    if current_base_case:
                        base_case_id = self._extract_base_case_id(current_base_case)
                        self.ai_assistant.update_context(
                            session_id, 
                            base_case=base_case_id,
                            analysis_type="base"
                        )
                    
                    # Process query
                    response = self.ai_assistant.process_query(session_id, message)
                    ai_response = response.get("response", "I'm sorry, I couldn't process that request.")
                    
                    # Add suggestions if available
                    suggestions = response.get("suggestions", [])
                    
                except Exception as e:
                    logger.error(f"Error processing AI query: {e}")
                    ai_response = "I encountered an error processing your request. Please try rephrasing your question."
                    suggestions = []
            else:
                ai_response = "AI Assistant is currently unavailable. Please check the system configuration."
                suggestions = []
            
            # Add AI response message
            ai_msg = self._create_message_div(ai_response, "assistant", suggestions)
            updated_messages.append(ai_msg)
            
            return updated_messages, ""  # Clear input
        
        @app.callback(
            Output("settings-modal", "is_open"),
            [Input("chat-settings-btn", "n_clicks"),
             Input("close-settings-btn", "n_clicks"),
             Input("save-settings-btn", "n_clicks")],
            [State("settings-modal", "is_open")]
        )
        def toggle_settings_modal(settings_click, close_click, save_click, is_open):
            """Toggle settings modal"""
            if settings_click or close_click or save_click:
                return not is_open
            return is_open
        
        @app.callback(
            Output("context-display", "children"),
            [Input("settings-modal", "is_open")],
            [State(base_case_state_id, "value"),
             State("expertise-dropdown", "value"),
             State("llm-model-dropdown", "value")]
        )
        def update_context_display(is_open, current_case, expertise, llm_model):
            """Update context display in settings"""
            if not is_open:
                return no_update
            
            base_case_id = self._extract_base_case_id(current_case) if current_case else "Unknown"
            
            context_elements = [
                html.P([html.Strong("Base Case: "), f"{base_case_id}"]),
                html.P([html.Strong("Expertise Level: "), f"{expertise or 'intermediate'}"]),
                html.P([html.Strong("Session: "), "Active" if AI_AVAILABLE else "Offline"])
            ]
            
            # Add LLM info if available
            if self.using_llm:
                context_elements.extend([
                    html.Hr(),
                    html.P([html.Strong("LLM Integration: "), "Active"]),
                    html.P([html.Strong("Model: "), f"{llm_model or 'gpt-3.5-turbo'}"]),
                    html.P([html.Strong("API Status: "), "Connected"])
                ])
            
            return html.Div(context_elements)
            
        @app.callback(
            [Output("ai-status-indicator", "style"),
             Output("llm-status-indicator", "style") if AI_AVAILABLE else Output("chat-messages", "style"),
             Output("chat-messages", "children", allow_duplicate=True)],
            Input("save-settings-btn", "n_clicks"),
            [State("api-key-input", "value"),
             State("llm-model-dropdown", "value"),
             State("chat-messages", "children")],
            prevent_initial_call=True
        )
        def save_settings(n_clicks, api_key, model, current_messages):
            """Save settings and potentially update LLM configuration"""
            if not n_clicks:
                return no_update, no_update, no_update
                
            ai_status = {"color": "green" if AI_AVAILABLE else "red"}
            llm_status = {"color": "gray"}
            welcome_message = None
            
            # If we have an API key, try to update the LLM integration
            if api_key and api_key.strip() and AI_AVAILABLE and LLM_AVAILABLE:
                try:
                    # Set the environment variable
                    os.environ["OPENAI_API_KEY"] = api_key
                    
                    # Re-initialize with LLM if not already using it
                    if not self.using_llm:
                        try:
                            self.ai_assistant = LLMEnhancedAssistant(self.db_path, api_key=api_key, 
                                                                    model=model or "gpt-3.5-turbo")
                            self.using_llm = True
                            
                            # Update welcome message
                            welcome_message = self._get_welcome_message()
                            llm_status = {"color": "blue"}
                            
                            logger.info("Switched to LLM-enhanced assistant")
                        except Exception as e:
                            logger.error(f"Failed to switch to LLM assistant: {e}")
                    else:
                        # Update model if already using LLM
                        if model and hasattr(self.ai_assistant, "llm"):
                            self.ai_assistant.llm.model = model
                            logger.info(f"Updated LLM model to {model}")
                            
                        llm_status = {"color": "blue"}
                except Exception as e:
                    logger.error(f"Error updating LLM settings: {e}")
                    llm_status = {"color": "red"}
            
            # Return current welcome message if no change
            if welcome_message is None:
                return ai_status, llm_status, no_update
            else:
                # Return new welcome message if configuration changed
                return ai_status, llm_status, welcome_message
        
        @app.callback(
            Output("chat-messages", "children", allow_duplicate=True),
            Input("chat-clear-btn", "n_clicks"),
            prevent_initial_call=True
        )
        def clear_chat(n_clicks):
            """Clear chat messages"""
            if n_clicks:
                return self._get_welcome_message()
            return no_update
    
    def _get_client_id(self) -> str:
        """Get or generate client ID for session management"""
        # In a real application, this would use proper session management
        return "default_client"
    
    def _get_or_create_session(self, client_id: str, expertise_level: str) -> str:
        """Get existing session or create new one"""
        if client_id in self.active_sessions and self.ai_assistant:
            session_id = self.active_sessions[client_id]
            # Update expertise level
            self.ai_assistant.update_context(session_id, expertise_level=expertise_level)
            return session_id
        
        if self.ai_assistant:
            session_id = self.ai_assistant.create_session(client_id, expertise_level)
            self.active_sessions[client_id] = session_id
            return session_id
        
        # Fallback session ID if AI not available
        return f"fallback_{client_id}"
    
    def _extract_base_case_id(self, dropdown_value: str) -> int:
        """Extract base case ID from dropdown value"""
        try:
            if isinstance(dropdown_value, str) and "case" in dropdown_value.lower():
                # Extract number from strings like "Base 42 - Case 1"
                import re
                match = re.search(r"Base (\d+)", dropdown_value)
                if match:
                    return int(match.group(1))
            return int(dropdown_value)
        except:
            return 42  # Default fallback
    
    def _create_message_div(self, message: str, sender: str, suggestions: List[str] = None) -> html.Div:
        """Create a formatted message div"""
        timestamp = datetime.now().strftime("%H:%M")
        
        # Message styling
        if sender == "user":
            style = {"backgroundColor": "#e8f5e8", "marginLeft": "50px"}
            icon = "👤"
            sender_name = "You"
        else:
            style = {"backgroundColor": "#e3f2fd", "marginRight": "50px"}
            icon = "🤖"
            sender_name = "AI Assistant"
        
        # Create message content
        message_content = [
            html.Div([
                html.Strong(f"{icon} {sender_name}"),
                html.Small(f" • {timestamp}", className="text-muted ms-2")
            ], className="d-flex justify-content-between align-items-center"),
            html.P(message, className="mb-2", style={"whiteSpace": "pre-wrap"})
        ]
        
        # Add suggestions for AI messages
        if sender == "assistant" and suggestions:
            suggestion_badges = [
                dbc.Badge(
                    suggestion, 
                    color="light", 
                    className="me-1 mb-1",
                    style={"cursor": "pointer", "fontSize": "0.75em"}
                ) for suggestion in suggestions[:3]
            ]
            message_content.append(
                html.Div([
                    html.Small("💡 Suggestions: ", className="text-muted"),
                    html.Div(suggestion_badges)
                ])
            )
        
        return html.Div(
            message_content,
            className="chat-message p-3 mb-2 rounded",
            style=style
        )


def create_ai_assistant_tab(db_path: str) -> dbc.Tab:
    """Create AI Assistant tab for the main application"""
    
    chat_interface = ChatInterface(db_path)
    
    # Main layout
    layout = dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H3("🤖 Conversational AI Assistant", className="mb-3"),
                html.P([
                    "Interact with our advanced AI assistant powered by state-of-the-art language models. ",
                    "Get intelligent insights, explanations, and analysis for your power system data."
                ], className="text-muted mb-4")
            ], width=12)
        ]),
        dbc.Row([
            dbc.Col([
                chat_interface.create_chat_layout()
            ], width=12)
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Alert([
                    html.H6("🔧 AI Assistant Features:", className="alert-heading"),
                    html.Ul([
                        html.Li("Natural language queries about DLR/SLR analysis"),
                        html.Li("Contextual explanations adapted to your expertise level"),
                        html.Li("Integration with current dashboard analysis state"),
                        html.Li("Intelligent suggestions for follow-up questions"),
                        html.Li("Export conversation history for documentation"),
                        html.Li([
                            "LLM-enhanced capabilities: ",
                            html.Span("Available", className="text-success fw-bold") if chat_interface.using_llm else 
                            html.Span("Not Available", className="text-muted")
                        ]) if AI_AVAILABLE else None,
                        html.Li("Advanced visualization intent detection with LLM technology") if chat_interface.using_llm else None,
                        html.Li("Enhanced technical responses for complex power system queries") if chat_interface.using_llm else None
                    ])
                ], color="info", className="mt-4")
            ], width=12)
        ])
    ], fluid=True)
    
    return dbc.Tab(
        label="🤖 AI Assistant",
        tab_id="ai-assistant",
        children=layout
    ), chat_interface


# Integration function for existing app
def integrate_ai_assistant(app: dash.Dash, db_path: str, main_layout_children: List) -> List:
    """Integrate AI assistant into existing Dash application"""
    
    # Create AI assistant tab
    ai_tab, chat_interface = create_ai_assistant_tab(db_path)
    
    # Check if floating chat is being used (by looking for chat components)
    has_floating_chat = False
    for component in main_layout_children:
        if hasattr(component, 'id') and ('floating-chat' in str(component.id) or 'chat-container' in str(component.id) or 'chat-toggle-btn' in str(component.id)):
            has_floating_chat = True
            break
        elif hasattr(component, 'children'):
            # Recursively check children
            def check_for_floating_chat(children):
                if isinstance(children, list):
                    for child in children:
                        if hasattr(child, 'id') and ('floating-chat' in str(child.id) or 'chat-container' in str(child.id) or 'chat-toggle-btn' in str(child.id)):
                            return True
                        elif hasattr(child, 'children') and check_for_floating_chat(child.children):
                            return True
                return False
            
            if check_for_floating_chat(component.children):
                has_floating_chat = True
                break
    
    # Only register callbacks if floating chat is not being used
    if not has_floating_chat:
        # Register callbacks
        chat_interface.register_callbacks(app)
        print("AI Assistant callbacks registered (no floating chat detected)")
    else:
        print("Floating chat detected - skipping AI Assistant callback registration to avoid conflicts")
    
    # Find existing tabs component and add AI tab
    for i, component in enumerate(main_layout_children):
        if hasattr(component, 'children') and isinstance(component.children, list):
            # Look for dcc.Tabs or dbc.Tabs
            for j, child in enumerate(component.children):
                if hasattr(child, 'children') and hasattr(child, 'id'):
                    if 'tab' in str(child.id).lower():
                        # Add AI tab to existing tabs
                        if isinstance(child.children, list):
                            child.children.append(ai_tab)
                        break
    
    return main_layout_children


# Standalone demo application
def create_demo_app(db_path: str) -> dash.Dash:
    """Create a standalone demo of the AI assistant"""
    
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    
    ai_tab, chat_interface = create_ai_assistant_tab(db_path)
    
    app.layout = dbc.Container([
        html.H1("Power System AI Assistant Demo", className="text-center mb-4"),
        ai_tab.children
    ], fluid=True)
    
    chat_interface.register_callbacks(app)
    
    return app


if __name__ == "__main__":
    # Run demo application
    import os
    
    # Try to get database path from config
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    db_path = "C:/Projects/dlr-database-project/data.db"  # Default to correct database
    
    # Try to load from config if available
    if os.path.exists(config_path):
        try:
            import json
            with open(config_path, 'r') as f:
                config = json.load(f)
                if "database_path" in config:
                    db_path = config["database_path"]
        except Exception as e:
            print(f"Error loading config: {e}")
    
    print(f"Using database path: {db_path}")
    demo_app = create_demo_app(db_path)
    
    print("🚀 Starting AI Assistant Demo...")
    print("🌐 Navigate to http://127.0.0.1:8051")
    
    demo_app.run_server(debug=True, host="127.0.0.1", port=8051)