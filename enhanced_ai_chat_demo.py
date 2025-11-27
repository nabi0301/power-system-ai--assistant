"""
Enhanced AI Chat Demo - Left Bottom Toggle
Tests the new AI-powered chat with Ollama integration
"""
import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import requests
import json

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

def get_ai_response(message):
    """Get AI response using Ollama or fallback to enhanced responses"""
    try:
        # Try to use Ollama for AI responses
        system_prompt = """You are an AI assistant specialized in electrical power systems engineering. 
        You help users understand power system concepts, analyze network data, and interpret results.
        Keep responses clear, concise, and technically accurate. Focus on practical explanations.
        If asked about specific data in the visualization, provide general power systems insights."""
        
        # Prepare the request for Ollama
        ollama_url = "http://localhost:11434/api/generate"
        
        payload = {
            "model": "llama3.2:3b",
            "prompt": f"System: {system_prompt}\n\nUser: {message}\n\nAssistant:",
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 200
            }
        }
        
        # Make request to Ollama
        response = requests.post(ollama_url, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result.get('response', '').strip()
            
            if ai_response:
                return f"🤖 {ai_response}"
        
    except Exception as e:
        print(f"AI response error: {e}")
    
    # Fallback to enhanced basic responses
    return get_enhanced_response(message)

def get_enhanced_response(message):
    """Enhanced response function with detailed power systems knowledge"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['voltage', 'volt', 'kv']):
        return "⚡ Voltage levels in power systems: Distribution (4-35kV), Sub-transmission (35-69kV), Transmission (69-800kV). Voltage regulation is critical for system stability."
    
    elif any(word in message_lower for word in ['power', 'mw', 'megawatt']):
        return "🔋 Active power (MW) is the real power that does actual work. Reactive power (MVAr) maintains voltage levels. Apparent power (MVA) = √(MW² + MVAr²)."
    
    elif any(word in message_lower for word in ['dlr', 'dynamic line rating']):
        return "🌤️ DLR uses real-time weather data (wind, temperature) to increase line capacity. Can boost transmission capability by 10-30% during favorable conditions."
    
    elif any(word in message_lower for word in ['contingency', 'n-1', 'outage']):
        return "⚠️ Contingency analysis studies system behavior when equipment fails. N-1 criterion ensures the system remains stable after any single component outage."
    
    elif any(word in message_lower for word in ['hello', 'hi', 'help']):
        return "👋 Hello! I'm your AI power systems assistant. I can help with: power flow analysis, contingency studies, line ratings, system stability, protection, and more. What would you like to explore?"
    
    else:
        return f"🔍 I can help with power systems analysis including voltage/current calculations, power flow studies, contingency analysis, line ratings (DLR/SLR), system stability, and protection. Could you be more specific about '{message}'?"

# Layout
app.layout = html.Div([
    html.Div([
        html.H1("🚀 AI Power Systems Assistant Demo", style={"textAlign": "center", "color": "#007BFF", "marginBottom": "30px"}),
        html.P("Click the AI button on the bottom-left to start chatting!", style={"textAlign": "center", "fontSize": "18px"}),
        html.Hr(),
        html.Div([
            html.H3("Demo Features:", style={"color": "#28a745"}),
            html.Ul([
                html.Li("🤖 AI-powered responses using local LLaMA (Ollama)"),
                html.Li("📍 Left-bottom toggle button"),
                html.Li("💬 Enhanced chat interface"),
                html.Li("⚡ Power systems expertise"),
                html.Li("🔄 Fallback responses when AI unavailable")
            ], style={"fontSize": "16px"})
        ], style={"margin": "20px", "padding": "20px", "backgroundColor": "#f8f9fa", "borderRadius": "10px"})
    ], style={"padding": "20px"}),
    
    # Enhanced AI Chat Component
    html.Div([
        # Chat toggle button - positioned on left bottom
        html.Div(
            html.Button(
                "🤖", 
                id="ai-chat-toggle",
                n_clicks=0,
                title="AI Assistant",
                style={
                    "backgroundColor": "#007BFF",
                    "color": "white",
                    "border": "none",
                    "borderRadius": "50%",
                    "width": "60px",
                    "height": "60px",
                    "fontSize": "24px",
                    "cursor": "pointer",
                    "boxShadow": "0 4px 8px rgba(0,0,0,0.3)",
                    "zIndex": "1000",
                    "transition": "all 0.3s ease",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center"
                }
            ),
            style={
                "position": "fixed",
                "bottom": "20px",
                "left": "20px",
                "zIndex": "1000"
            }
        ),
        # Enhanced chat panel
        html.Div([
            html.Div([
                html.H4("🤖 AI Power Systems Assistant", style={"margin": "0", "color": "#007BFF", "fontSize": "16px"}),
                html.Button("×", id="ai-chat-close", 
                           style={"background": "none", "border": "none", "float": "right", "fontSize": "20px", "cursor": "pointer"})
            ], style={"padding": "15px", "borderBottom": "1px solid #ddd", "backgroundColor": "#f8f9fa"}),
            
            html.Div(id="ai-chat-messages", 
                    children=[
                        html.Div([
                            html.Strong("🤖 AI Assistant: "),
                            html.Span("Hello! I'm your AI assistant for power system analysis. Ask me about voltage, power flow, contingency analysis, DLR, or any power systems topic!")
                        ], style={"marginBottom": "8px", "padding": "8px", "backgroundColor": "#e3f2fd", "borderRadius": "8px", "fontSize": "14px"}),
                    ],
                    style={"padding": "10px", "height": "300px", "overflowY": "auto", "backgroundColor": "white"}),
            
            html.Div([
                dcc.Input(
                    id="ai-chat-input",
                    type="text",
                    placeholder="Ask me about power systems...",
                    style={"width": "75%", "marginRight": "5px", "padding": "8px", "borderRadius": "4px", "border": "1px solid #ddd"}
                ),
                html.Button("Send", id="ai-chat-send", 
                           style={"backgroundColor": "#007BFF", "color": "white", "border": "none", "padding": "8px 15px", "borderRadius": "4px", "cursor": "pointer"})
            ], style={"padding": "15px", "backgroundColor": "#f8f9fa", "borderTop": "1px solid #ddd"})
        ], 
        id="ai-chat-panel",
        style={
            "position": "fixed",
            "bottom": "90px",
            "left": "20px",
            "width": "400px",
            "height": "450px",
            "backgroundColor": "white",
            "border": "1px solid #ddd",
            "borderRadius": "12px",
            "boxShadow": "0 8px 32px rgba(0,0,0,0.2)",
            "zIndex": "1000",
            "display": "none",
            "fontFamily": "Arial, sans-serif"
        })
    ])
])

# Chat toggle callback
@app.callback(
    Output("ai-chat-panel", "style"),
    [Input("ai-chat-toggle", "n_clicks"), Input("ai-chat-close", "n_clicks")],
    [State("ai-chat-panel", "style")],
    prevent_initial_call=True
)
def toggle_ai_chat(toggle_clicks, close_clicks, current_style):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update
    
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    # Default style
    default_style = {
        "position": "fixed",
        "bottom": "90px",
        "left": "20px",
        "width": "400px",
        "height": "450px",
        "backgroundColor": "white",
        "border": "1px solid #ddd",
        "borderRadius": "12px",
        "boxShadow": "0 8px 32px rgba(0,0,0,0.2)",
        "zIndex": "1000",
        "display": "none",
        "fontFamily": "Arial, sans-serif"
    }
    
    new_style = current_style.copy() if current_style else default_style
    
    if trigger_id == "ai-chat-toggle":
        # Toggle display
        if new_style.get("display") == "none":
            new_style["display"] = "block"
        else:
            new_style["display"] = "none"
    elif trigger_id == "ai-chat-close":
        # Always close
        new_style["display"] = "none"
    
    return new_style

# Chat message callback
@app.callback(
    [Output("ai-chat-messages", "children"),
     Output("ai-chat-input", "value")],
    [Input("ai-chat-send", "n_clicks"), Input("ai-chat-input", "n_submit")],
    [State("ai-chat-input", "value"), State("ai-chat-messages", "children")],
    prevent_initial_call=True
)
def handle_ai_chat(send_clicks, input_submit, message, current_messages):
    if not message or message.strip() == "":
        return no_update, no_update
    
    # Get AI response
    ai_response = get_ai_response(message)
    
    # Get existing messages or start with initial message
    messages = current_messages or []
    
    # User message
    user_msg = html.Div([
        html.Strong("You: ", style={"color": "#007BFF"}),
        html.Span(message)
    ], style={
        "marginBottom": "8px", 
        "padding": "8px", 
        "backgroundColor": "#f0f8ff", 
        "borderRadius": "8px",
        "fontSize": "14px"
    })
    
    # AI response
    ai_msg = html.Div([
        html.Span(ai_response)
    ], style={
        "marginBottom": "8px", 
        "padding": "8px", 
        "backgroundColor": "#f8fff8", 
        "borderRadius": "8px",
        "fontSize": "14px",
        "borderLeft": "3px solid #28a745"
    })
    
    messages.extend([user_msg, ai_msg])
    return messages, ""

if __name__ == "__main__":
    print("🤖 Starting AI Chat Demo...")
    print("🌐 Open http://127.0.0.1:8052 to test the enhanced AI chat")
    print("💡 Try asking about power systems topics!")
    app.run(debug=True, port=8052)