#!/usr/bin/env python3
"""
Lightweight Power System Visualization with Real Database Integration
Minimal dependencies version that reads from SQLite database.
"""

import dash
from dash import dcc, html, Input, Output, State, callback_context
import plotly.graph_objects as go
import sqlite3
import json

# AI Integration with PNNL AI Incubator API
def get_ai_response(user_message):
    """
    AI response function with PNNL AI Incubator API and enhanced fallback
    """
    
    # Primary: PNNL AI Incubator API
    try:
        from openai import OpenAI
        
        # Initialize client with PNNL AI Incubator settings
        API_KEY = "sk-4UJCbpRTNTx-lvO_4bxNdQ"
        BASE_URL = "https://ai-incubator-api.pnnl.gov"
        MODEL = "claude-3-7-sonnet-20250219-v1-birthright"
        
        client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
        
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are an expert power systems engineer with deep knowledge of electrical grids, transmission lines, DLR/SLR analysis, and power system operations."},
                {"role": "user", "content": user_message}
            ],
            stream=False
        )
        return f"🤖 {response.choices[0].message.content.strip()}"
    except Exception as e:
        print(f"AI API error: {e}")
    
    # Fallback: Enhanced contextual responses
    message_lower = user_message.lower()
    
    power_keywords = {
        'load': "Power system loading refers to the electrical demand on the network. Higher loads require more transmission capacity.",
        'dlr': "Dynamic Line Rating (DLR) uses real-time weather data to safely increase transmission capacity beyond static limits.",
        'slr': "Static Line Rating (SLR) uses conservative fixed limits based on worst-case weather conditions.",
        'contingency': "Contingency analysis studies system response when equipment fails, crucial for reliability.",
        'voltage': "Voltage levels must be maintained within acceptable ranges for proper equipment operation.",
        'database': "Our database contains IEEE 118-bus system data with base cases, contingency analysis, and SLR/DLR comparisons.",
        'bus': "Buses are nodes in the power system where generation, load, and transmission lines connect.",
        'branch': "Branches are transmission lines connecting buses, carrying power flows between nodes.",
        'mva': "MVA (Mega Volt-Ampere) represents apparent power flow through transmission lines.",
        'violation': "Violations occur when system parameters exceed safe operating limits."
    }
    
    for keyword, response in power_keywords.items():
        if keyword in message_lower:
            return f"💡 {response}"
    
    return f"🔧 I understand you're asking about '{user_message}'. The visualization shows real IEEE 118-bus system data from our database."

def load_database_data():
    """Load real power system data from SQLite database"""
    try:
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        # Load base case bus data
        cursor.execute("""
        SELECT BUS_NUMBER, VM, VA, BASE_KV, PG, QG, PD, QD
        FROM BaseBusData 
        WHERE base_case_id = 0
        ORDER BY BUS_NUMBER
        """)
        bus_data = cursor.fetchall()
        
        # Load base case branch data  
        cursor.execute("""
        SELECT branch_number, From_Bus, To_Bus, PF, QF, MVA, RATE, VIO
        FROM BaseBranchData 
        WHERE base_case_id = 0
        ORDER BY branch_number
        """)
        branch_data = cursor.fetchall()
        
        # Load SLR data for comparison
        cursor.execute("""
        SELECT From_Bus, To_Bus, MVA, RATE, VIO
        FROM SLR_Branches 
        WHERE base_case_id = 42 AND contingency_case_id = 123
        ORDER BY branch_number
        LIMIT 50
        """)
        slr_data = cursor.fetchall()
        
        # Load DLR data for comparison
        cursor.execute("""
        SELECT From_Bus, To_Bus, MVA, RATE, VIO
        FROM DLR_Branches 
        WHERE base_case_id = 42 AND contingency_case_id = 123
        ORDER BY branch_number  
        LIMIT 50
        """)
        dlr_data = cursor.fetchall()
        
        conn.close()
        
        print(f"Loaded {len(bus_data)} buses, {len(branch_data)} branches")
        print(f"SLR data: {len(slr_data)} cases, DLR data: {len(dlr_data)} cases")
        
        return bus_data, branch_data, slr_data, dlr_data
        
    except Exception as e:
        print(f"Database error: {e}")
        return [], [], [], []

def create_bus_plot(bus_data):
    """Create bus visualization"""
    if not bus_data:
        fig = go.Figure()
        fig.add_annotation(text="No bus data available", xref="paper", yref="paper", x=0.5, y=0.5)
        return fig
    
    fig = go.Figure()
    
    # Create coordinate system (simple grid)
    x_coords = []
    y_coords = []
    voltages = []
    loads = []
    bus_numbers = []
    
    for row in bus_data:
        bus_num, vm, va, base_kv, pg, qg, pd, qd = row
        x_coords.append((bus_num % 12) * 30)
        y_coords.append((bus_num // 12) * 25)
        voltages.append(vm)
        loads.append(pd)
        bus_numbers.append(bus_num)
    
    # Add bus points
    fig.add_trace(go.Scatter(
        x=x_coords,
        y=y_coords,
        mode='markers',
        marker=dict(
            size=[abs(load)/5 + 5 for load in loads],  # Size based on load
            color=voltages,  # Color based on voltage
            colorscale='RdYlGn',
            showscale=True,
            colorbar=dict(title="Voltage (p.u.)")
        ),
        text=[f"Bus {bus}<br>V: {v:.3f} p.u.<br>Load: {l:.1f} MW" 
              for bus, v, l in zip(bus_numbers, voltages, loads)],
        hovertemplate='%{text}<extra></extra>',
        name='Buses'
    ))
    
    fig.update_layout(
        title=f"IEEE 118-Bus System - {len(bus_data)} Buses from Database",
        xaxis_title="X Coordinate",
        yaxis_title="Y Coordinate",
        height=600,
        template="plotly_white"
    )
    
    return fig

def create_comparison_plot(slr_data, dlr_data):
    """Create SLR vs DLR comparison"""
    if not slr_data and not dlr_data:
        fig = go.Figure()
        fig.add_annotation(text="No SLR/DLR comparison data available", 
                          xref="paper", yref="paper", x=0.5, y=0.5)
        fig.update_layout(title="SLR vs DLR Comparison", height=400)
        return fig
    
    fig = go.Figure()
    
    # Plot SLR violations
    if slr_data:
        slr_violations = [row[4] for row in slr_data]  # VIO column
        slr_lines = [f"{row[0]}-{row[1]}" for row in slr_data]
        
        fig.add_trace(go.Scatter(
            x=list(range(len(slr_violations))),
            y=slr_violations,
            mode='markers',
            name='SLR Violations (%)',
            marker=dict(color='red', size=8),
            text=slr_lines,
            hovertemplate='Line: %{text}<br>SLR Violation: %{y:.1f}%<extra></extra>'
        ))
    
    # Plot DLR violations
    if dlr_data:
        dlr_violations = [row[4] for row in dlr_data]  # VIO column
        dlr_lines = [f"{row[0]}-{row[1]}" for row in dlr_data]
        
        fig.add_trace(go.Scatter(
            x=list(range(len(dlr_violations))),
            y=dlr_violations,
            mode='markers',
            name='DLR Violations (%)',
            marker=dict(color='blue', size=8),
            text=dlr_lines,
            hovertemplate='Line: %{text}<br>DLR Violation: %{y:.1f}%<extra></extra>'
        ))
    
    fig.update_layout(
        title=f"SLR vs DLR Violation Analysis - Database Comparison",
        xaxis_title="Line Index",
        yaxis_title="Violation Percentage (%)",
        height=500,
        template="plotly_white"
    )
    
    return fig

def create_chat_component():
    """Create chat interface"""
    return html.Div([
        html.Button("🤖", id="chat-toggle-btn", style={
            "position": "fixed", "left": "20px", "bottom": "20px",
            "width": "60px", "height": "60px", "borderRadius": "50%",
            "backgroundColor": "#007bff", "color": "white", "border": "none",
            "fontSize": "24px", "cursor": "pointer", "zIndex": "1000",
            "boxShadow": "0 4px 12px rgba(0,0,0,0.3)"
        }),
        
        html.Div([
            html.Div([
                html.H4("🤖 AI Assistant", style={"margin": "0", "color": "#333"}),
                html.Button("✕", id="chat-close-btn", style={
                    "position": "absolute", "top": "10px", "right": "15px",
                    "background": "none", "border": "none", "fontSize": "20px", "cursor": "pointer"
                })
            ], style={"padding": "15px", "borderBottom": "1px solid #ddd", "position": "relative"}),
            
            html.Div(id="chat-messages", children=[
                html.Div("👋 Ask me about the power system database, DLR/SLR analysis, or bus/branch data!", 
                        style={"padding": "10px", "backgroundColor": "#f0f8ff", "margin": "5px", "borderRadius": "10px"})
            ], style={"height": "300px", "overflowY": "auto", "padding": "10px"}),
            
            html.Div([
                dcc.Input(id="chat-input", type="text", placeholder="Ask about power systems...",
                         style={"width": "85%", "padding": "10px", "border": "1px solid #ddd", "borderRadius": "5px"}),
                html.Button("Send", id="chat-send-btn", style={
                    "width": "13%", "padding": "10px", "backgroundColor": "#007bff", 
                    "color": "white", "border": "none", "borderRadius": "5px", "cursor": "pointer"
                })
            ], style={"padding": "10px", "display": "flex", "gap": "5px"})
        ], id="chat-interface", style={
            "position": "fixed", "left": "20px", "bottom": "90px",
            "width": "350px", "height": "400px", "backgroundColor": "white",
            "border": "1px solid #ddd", "borderRadius": "10px",
            "boxShadow": "0 4px 20px rgba(0,0,0,0.2)", "display": "none", "zIndex": "999"
        })
    ])

# Initialize app and load data
app = dash.Dash(__name__)
print("Loading database data...")
bus_data, branch_data, slr_data, dlr_data = load_database_data()

# App layout
app.layout = html.Div([
    html.H1("Power System Database Visualization", style={"textAlign": "center", "margin": "20px"}),
    
    html.Div([
        html.H3("Real Database Integration"),
        html.P("This app reads actual IEEE 118-bus system data from the SQLite database."),
        html.P("🤖 Click the chat button (bottom-left) for AI assistance!"),
        html.P("📊 Visualizations show real voltage, load, and SLR/DLR comparison data."),
    ], style={"margin": "20px", "padding": "20px", "backgroundColor": "#f8f9fa", "borderRadius": "5px"}),
    
    dcc.Graph(id="bus-plot", figure=create_bus_plot(bus_data)),
    dcc.Graph(id="comparison-plot", figure=create_comparison_plot(slr_data, dlr_data)),
    
    html.Div([
        html.H3("Database Stats:"),
        html.Ul([
            html.Li(f"✅ Buses loaded: {len(bus_data)}"),
            html.Li(f"✅ Branches loaded: {len(branch_data)}"),
            html.Li(f"✅ SLR analysis cases: {len(slr_data)}"),
            html.Li(f"✅ DLR analysis cases: {len(dlr_data)}"),
            html.Li("✅ Real-time SQLite database connection"),
            html.Li("✅ AI chat with PNNL API integration")
        ])
    ], style={"margin": "20px", "padding": "20px", "backgroundColor": "#e8f5e8", "borderRadius": "5px"}),
    
    create_chat_component()
])

# Chat callbacks
@app.callback(
    Output("chat-interface", "style"),
    [Input("chat-toggle-btn", "n_clicks"), Input("chat-close-btn", "n_clicks")],
    [State("chat-interface", "style")]
)
def toggle_chat(toggle_clicks, close_clicks, current_style):
    ctx = callback_context
    if not ctx.triggered:
        return current_style
    
    if current_style["display"] == "none":
        current_style["display"] = "block"
    else:
        current_style["display"] = "none"
    return current_style

@app.callback(
    [Output("chat-messages", "children"), Output("chat-input", "value")],
    [Input("chat-send-btn", "n_clicks")],
    [State("chat-input", "value"), State("chat-messages", "children")]
)
def handle_chat_message(n_clicks, user_message, current_messages):
    if not n_clicks or not user_message:
        return current_messages, ""
    
    user_msg = html.Div(f"You: {user_message}", style={
        "padding": "8px", "backgroundColor": "#e3f2fd", "margin": "5px",
        "borderRadius": "10px", "textAlign": "right"
    })
    
    ai_response = get_ai_response(user_message)
    ai_msg = html.Div(ai_response, style={
        "padding": "8px", "backgroundColor": "#f0f8ff", "margin": "5px", "borderRadius": "10px"
    })
    
    return current_messages + [user_msg, ai_msg], ""

if __name__ == "__main__":
    print("🚀 Starting Lightweight Power System Visualization")
    print("📊 Database: Real IEEE 118-bus system data")
    print("🤖 AI: PNNL API with Claude-3.5 Sonnet")
    print("🌐 URL: http://127.0.0.1:8055")
    app.run(debug=True, port=8055)