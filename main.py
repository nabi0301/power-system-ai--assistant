#!/usr/bin/env python3
"""
IEEE 118-Bus Power System Analysis - Main Application
"""

# Core imports
import dash
from dash import dcc, html, Input, Output, State, callback_context
import plotly.graph_objects as go
import pandas as pd
import sqlite3
import json

# Import our modules
from simplified_network_graph import create_network_graph
from ieee118_prompt_templates import ieee118_prompts

# Initialize app
app = dash.Dash(__name__)

# Global data loading
def load_database_data():
    """Load data from database"""
    try:
        conn = sqlite3.connect('data.db')
        
        # Load bus data
        buses_query = "SELECT * FROM BaseBusData WHERE base_case_id = 0 ORDER BY BUS_NUMBER"
        buses_df = pd.read_sql_query(buses_query, conn)
        
        # Load branch data  
        branches_query = "SELECT * FROM BaseBranchData WHERE base_case_id = 0 ORDER BY branch_number"
        branches_df = pd.read_sql_query(branches_query, conn)
        
        conn.close()
        return buses_df, branches_df
        
    except Exception as e:
        print(f"Database error: {e}")
        # Return empty dataframes
        return pd.DataFrame(), pd.DataFrame()

# Load global data
buses_df, branches_df = load_database_data()

# Helper functions
def get_prompt_help():
    """Get prompt help"""
    return ieee118_prompts.generate_example_prompts()

def get_ai_response(user_message, current_viz_type='network_view'):
    """Simple AI response function"""
    message_lower = user_message.lower()
    
    # Help requests
    if any(keyword in message_lower for keyword in ['help', 'commands', 'what can you do']):
        return get_prompt_help(), None, None, None
    
    # Network requests
    if any(keyword in message_lower for keyword in ['network', 'topology', 'graph']):
        return "Showing network topology for IEEE 118 system", 'network_view', 0, None
    
    # Voltage requests
    if any(keyword in message_lower for keyword in ['voltage', 'bus voltage']):
        return "Analyzing voltage profile across all buses", 'voltage', 0, None
    
    # Loading requests
    if any(keyword in message_lower for keyword in ['loading', 'line loading', 'overload']):
        return "Checking transmission line loading", 'loading', 0, None
    
    # Default response
    suggestions = ieee118_prompts.get_contextual_suggestions(current_viz_type, [])
    response = f"I understand you're asking about '{user_message}'. Try asking about network graphs, voltage analysis, or loading checks."
    
    if suggestions:
        response += f"\n\n💡 **Suggestions:**\n" + "\n".join([f"• {s}" for s in suggestions])
    
    return response, None, None, None

def create_enhanced_chat_component():
    """Create chat component"""
    return html.Div([
        # Chat toggle button
        html.Button(
            "🤖",
            id="chat-toggle-btn",
            style={
                "position": "fixed",
                "left": "20px",
                "bottom": "20px", 
                "width": "60px",
                "height": "60px",
                "borderRadius": "50%",
                "backgroundColor": "#007bff",
                "color": "white",
                "border": "none",
                "fontSize": "24px",
                "cursor": "pointer",
                "zIndex": "1000",
                "boxShadow": "0 4px 12px rgba(0,0,0,0.3)"
            }
        ),
        
        # Chat interface
        html.Div([
            # Header
            html.Div([
                html.H4("🤖 IEEE 118 Bus AI Assistant", 
                       style={"margin": "0", "color": "#333", "fontSize": "16px"}),
                html.Button("✕", id="chat-close-btn", style={
                    "position": "absolute", "top": "10px", "right": "15px",
                    "background": "none", "border": "none", "fontSize": "20px", 
                    "cursor": "pointer"
                })
            ], style={"padding": "15px", "borderBottom": "1px solid #ddd", "position": "relative"}),
            
            # Messages
            html.Div(id="chat-messages", children=[
                html.Div("Welcome to IEEE 118 Bus System Analysis!", style={
                    "padding": "10px", "backgroundColor": "#f0f8ff", "margin": "5px", "borderRadius": "10px"
                })
            ], style={"height": "300px", "overflowY": "auto", "padding": "10px"}),
            
            # Input
            html.Div([
                dcc.Input(
                    id="chat-input",
                    type="text",
                    placeholder="Ask about power systems...",
                    style={"width": "85%", "padding": "10px", "border": "1px solid #ddd", "borderRadius": "5px"}
                ),
                html.Button("Send", id="chat-send-btn", style={
                    "width": "13%", "padding": "10px", "backgroundColor": "#007bff",
                    "color": "white", "border": "none", "borderRadius": "5px"
                })
            ], style={"padding": "10px", "display": "flex", "gap": "5px"})
            
        ], id="chat-interface", style={
            "position": "fixed",
            "left": "20px", 
            "bottom": "90px",
            "width": "350px",
            "height": "400px",
            "backgroundColor": "white",
            "border": "1px solid #ddd", 
            "borderRadius": "10px",
            "display": "none",
            "zIndex": "999"
        })
    ])

# Visualization functions
def create_voltage_plot():
    """Create voltage analysis plot"""
    if buses_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No bus data available", x=0.5, y=0.5, xref="paper", yref="paper")
        return fig
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=buses_df['BUS_NUMBER'],
        y=buses_df['VM'],
        mode='markers+lines',
        name='Voltage Profile'
    ))
    
    fig.update_layout(
        title="IEEE 118 Bus Voltage Profile",
        xaxis_title="Bus Number",
        yaxis_title="Voltage (p.u.)"
    )
    return fig

def create_loading_plot():
    """Create loading analysis plot"""
    if branches_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No branch data available", x=0.5, y=0.5, xref="paper", yref="paper")
        return fig
    
    # Calculate loading percentages
    loading_pct = (branches_df['MVA'] / branches_df['RATE'] * 100).fillna(0)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=branches_df.index,
        y=loading_pct,
        mode='markers',
        name='Loading %'
    ))
    
    fig.update_layout(
        title="Transmission Line Loading Analysis",
        xaxis_title="Branch Index",
        yaxis_title="Loading (%)"
    )
    return fig

# App layout
app.layout = html.Div([
    html.H1("IEEE 118-Bus Power System Analysis", style={"textAlign": "center", "margin": "20px"}),
    
    # Controls
    html.Div([
        html.H4("Visualization Selector:"),
        dcc.Dropdown(
            id='viz-selector',
            options=[
                {'label': '🌐 Network View', 'value': 'network_view'},
                {'label': '⚡ Voltage Analysis', 'value': 'voltage'},
                {'label': '📊 Loading Analysis', 'value': 'loading'}
            ],
            value='network_view'
        )
    ], style={"margin": "20px"}),
    
    # Visualization area
    dcc.Graph(id="dynamic-plot"),
    
    # Hidden stores
    html.Div(id="viz-command-store", style={"display": "none"}),
    html.Div(id="current-viz-type", children="network_view", style={"display": "none"}),
    dcc.Store(id="case-id-store", data=0),
    dcc.Store(id="contingency-id-store", data=None),
    
    # Chat component
    create_enhanced_chat_component()
])

# Callbacks
@app.callback(
    Output("dynamic-plot", "figure"),
    [Input("viz-selector", "value"), Input("case-id-store", "data"), Input("contingency-id-store", "data")]
)
def update_plot(selected_viz, case_id, contingency_id):
    """Update plot based on selection"""
    try:
        if selected_viz == 'network_view':
            return create_network_graph(case_id or 0, contingency_id)
        elif selected_viz == 'voltage':
            return create_voltage_plot()
        elif selected_viz == 'loading':
            return create_loading_plot()
        else:
            return create_network_graph(0, None)
    except Exception as e:
        fig = go.Figure()
        fig.add_annotation(text=f"Error: {str(e)}", x=0.5, y=0.5, xref="paper", yref="paper")
        return fig

@app.callback(
    Output("chat-interface", "style"),
    [Input("chat-toggle-btn", "n_clicks"), Input("chat-close-btn", "n_clicks")],
    [State("chat-interface", "style")]
)
def toggle_chat(toggle_clicks, close_clicks, current_style):
    """Toggle chat interface"""
    ctx = callback_context
    if not ctx.triggered:
        return current_style
        
    if current_style["display"] == "none":
        current_style["display"] = "block"
    else:
        current_style["display"] = "none"
    return current_style

@app.callback(
    [Output("chat-messages", "children"), Output("chat-input", "value"), Output("viz-command-store", "children")],
    [Input("chat-send-btn", "n_clicks")],
    [State("chat-input", "value"), State("chat-messages", "children"), State("current-viz-type", "children")]
)
def handle_chat(n_clicks, user_message, current_messages, current_viz_type):
    """Handle chat messages"""
    if not n_clicks or not user_message:
        return current_messages, "", ""
    
    # Add user message
    user_msg = html.Div(f"You: {user_message}", style={
        "padding": "8px", "backgroundColor": "#e3f2fd", "margin": "5px", "borderRadius": "10px"
    })
    
    # Get AI response
    ai_response, viz_command, case_id, contingency_id = get_ai_response(user_message, current_viz_type)
    
    ai_msg = html.Div(ai_response, style={
        "padding": "8px", "backgroundColor": "#f0f8ff", "margin": "5px", "borderRadius": "10px"
    })
    
    updated_messages = current_messages + [user_msg, ai_msg]
    
    # Handle viz command
    viz_info = {}
    if viz_command:
        viz_info["viz_command"] = viz_command
    if case_id is not None:
        viz_info["case_id"] = case_id
    
    return updated_messages, "", json.dumps(viz_info) if viz_info else ""

@app.callback(
    [Output("viz-selector", "value"), Output("current-viz-type", "children"), 
     Output("case-id-store", "data"), Output("contingency-id-store", "data")],
    [Input("viz-command-store", "children")],
    prevent_initial_call=True
)
def update_viz_from_chat(viz_command):
    """Update visualization from chat commands"""
    if not viz_command:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    try:
        viz_data = json.loads(viz_command)
        command = viz_data.get('viz_command', '')
        case_id = viz_data.get('case_id', 0)
        contingency_id = viz_data.get('contingency_id')
        
        if command in ['network_view', 'voltage', 'loading']:
            return command, command, case_id, contingency_id
    except:
        pass
    
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update

# Run app
if __name__ == "__main__":
    print("🚀 Starting IEEE 118-Bus Power System Analysis")
    print(f"📊 Loaded {len(buses_df)} buses, {len(branches_df)} branches")
    print("🌐 Opening: http://127.0.0.1:8054")
    
    try:
        app.run(debug=True, port=8054, host='127.0.0.1')
    except Exception as e:
        print(f"Error: {e}")
        print("Trying port 8055...")
        app.run(debug=True, port=8055, host='127.0.0.1')