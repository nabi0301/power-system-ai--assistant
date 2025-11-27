"""
Minimal test app with working chat system
"""
import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import os

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

def create_minimal_chat_component():
    """Create a minimal chat component that always works"""
    return html.Div([
        # Chat toggle button
        html.Div(
            html.Button(
                "💬", 
                id="minimal-chat-toggle",
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
                "right": "20px",
                "zIndex": "1000"
            }
        ),
        # Minimal chat panel
        html.Div([
            html.Div([
                html.H4("💬 Local LLaMA Chat", style={"margin": "0", "color": "#0D8767"}),
                html.Button("×", id="minimal-chat-close", 
                           style={"background": "none", "border": "none", "float": "right", "fontSize": "20px"})
            ], style={"padding": "10px", "borderBottom": "1px solid #ddd"}),
            
            html.Div(id="minimal-chat-messages", 
                    style={"padding": "10px", "height": "200px", "overflowY": "auto", "backgroundColor": "#f8f9fa"}),
            
            html.Div([
                dcc.Input(
                    id="minimal-chat-input",
                    type="text",
                    placeholder="Ask about power systems...",
                    style={"width": "70%", "marginRight": "5px"}
                ),
                html.Button("Send", id="minimal-chat-send", 
                           style={"backgroundColor": "#0D8767", "color": "white", "border": "none", "padding": "5px 10px"})
            ], style={"padding": "10px"})
        ], 
        id="minimal-chat-panel",
        style={
            "position": "fixed",
            "bottom": "80px",
            "right": "20px",
            "width": "300px",
            "height": "300px",
            "backgroundColor": "white",
            "border": "1px solid #ddd",
            "borderRadius": "10px",
            "boxShadow": "0 4px 8px rgba(0,0,0,0.2)",
            "zIndex": "1000",
            "display": "none"
        })
    ])

# Layout
app.layout = html.Div([
    html.H1("Minimal Chat Test", style={"textAlign": "center"}),
    html.P("This is a test app to verify the chat button works."),
    create_minimal_chat_component()
])

# Chat toggle callback
@app.callback(
    Output("minimal-chat-panel", "style"),
    [Input("minimal-chat-toggle", "n_clicks"), Input("minimal-chat-close", "n_clicks")],
    [State("minimal-chat-panel", "style")],
    prevent_initial_call=True
)
def toggle_chat_panel(toggle_clicks, close_clicks, current_style):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update
    
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    # Create a copy of the current style
    new_style = current_style.copy() if current_style else {}
    
    if trigger_id == "minimal-chat-toggle":
        # Toggle display
        if new_style.get("display") == "none":
            new_style["display"] = "block"
        else:
            new_style["display"] = "none"
    elif trigger_id == "minimal-chat-close":
        # Always close
        new_style["display"] = "none"
    
    return new_style

# Chat message callback
@app.callback(
    Output("minimal-chat-messages", "children"),
    [Input("minimal-chat-send", "n_clicks"), Input("minimal-chat-input", "n_submit")],
    [State("minimal-chat-input", "value"), State("minimal-chat-messages", "children")],
    prevent_initial_call=True
)
def handle_chat_message(send_clicks, input_submit, message, current_messages):
    if not message or message.strip() == "":
        return current_messages or []
    
    # Get existing messages or start with empty list
    messages = current_messages or []
    
    # Add user message
    user_msg = html.Div([
        html.Strong("You: "),
        html.Span(message)
    ], style={"marginBottom": "5px", "padding": "5px", "backgroundColor": "#e9ecef", "borderRadius": "5px"})
    
    # Add bot response
    bot_msg = html.Div([
        html.Strong("Assistant: "),
        html.Span(f"I received your message: '{message}'. This is a test response!")
    ], style={"marginBottom": "5px", "padding": "5px", "backgroundColor": "#d4edda", "borderRadius": "5px"})
    
    messages.extend([user_msg, bot_msg])
    return messages

# Clear input callback
@app.callback(
    Output("minimal-chat-input", "value"),
    [Input("minimal-chat-send", "n_clicks"), Input("minimal-chat-input", "n_submit")],
    prevent_initial_call=True
)
def clear_input(send_clicks, input_submit):
    return ""

if __name__ == "__main__":
    print("🚀 Starting minimal chat test app...")
    print("🌐 Open http://127.0.0.1:8051 to test the chat")
    app.run(debug=True, port=8051)