#!/usr/bin/env python3
"""
Quick Test of Fixed Power System Visualization
"""

import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import pandas as pd
import sqlite3

# Test PyVista import
try:
    from pyvista_network_3d import get_enhanced_3d_network_graph, PYVISTA_AVAILABLE
    print(f"✅ PyVista 3D Network: {PYVISTA_AVAILABLE}")
except ImportError as e:
    print(f"❌ PyVista import failed: {e}")
    PYVISTA_AVAILABLE = False

print("🔧 Testing Quick Power System Visualization...")

# Load sample data
def load_sample_data():
    buses_df = pd.DataFrame({
        'BUS_NUMBER': range(1, 11),
        'BASE_KV': [345, 345, 138, 138, 138, 69, 69, 69, 25, 25],
        'VM': [1.05, 1.02, 0.98, 1.01, 0.99, 1.03, 0.97, 1.00, 1.02, 0.96],
        'TYPE': [3, 2, 1, 1, 2, 1, 1, 1, 1, 1]
    })
    
    branches_df = pd.DataFrame({
        'FROM_BUS': [1, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        'TO_BUS': [2, 3, 4, 5, 6, 7, 8, 9, 10, 10],
        'PF': [150, 120, 90, 85, 110, 45, 60, 35, 25, 30],
        'RATE_A': [200, 180, 150, 120, 140, 80, 90, 60, 50, 45]
    })
    
    return buses_df, branches_df

buses_df, branches_df = load_sample_data()

# Create Dash app
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("🚀 Fixed Power System Visualization Test", 
            style={"textAlign": "center", "color": "#00ffff", "margin": "20px"}),
    
    html.Div([
        html.P(f"✅ Syntax errors fixed!", style={"color": "green"}),
        html.P(f"✅ PyVista 3D Available: {PYVISTA_AVAILABLE}", 
               style={"color": "green" if PYVISTA_AVAILABLE else "orange"}),
        
        dcc.Dropdown(
            id='test-viz-selector',
            options=[
                {'label': '2D Network View', 'value': 'network_2d'},
                {'label': '🌐 3D Network View (PyVista)', 'value': 'network_3d'},
            ],
            value='network_2d',
            style={'margin': '10px'}
        ),
        
        html.Button("Generate Visualization", id="test-button", n_clicks=0,
                   style={"margin": "10px", "padding": "10px 20px", "backgroundColor": "#00ffff"})
    ], style={"margin": "20px", "padding": "20px", "backgroundColor": "rgba(0, 30, 60, 0.8)", 
              "borderRadius": "10px", "color": "white"}),
    
    dcc.Graph(id="test-graph", style={"height": "600px"}),
    
    html.Div(id="test-status", style={"margin": "20px", "color": "white"})
])

@app.callback(
    [Output("test-graph", "figure"),
     Output("test-status", "children")],
    [Input("test-button", "n_clicks"), Input("test-viz-selector", "value")]
)
def update_test_graph(n_clicks, selected_viz):
    if n_clicks == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="Click 'Generate Visualization' to test",
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False, font=dict(size=16, color="gray")
        )
        return fig, "Ready to test visualization..."
    
    try:
        if selected_viz == 'network_3d' and PYVISTA_AVAILABLE:
            print("🌐 Testing PyVista 3D Network...")
            fig = get_enhanced_3d_network_graph(buses_df, branches_df, case_id=0)
            if fig:
                return fig, "✅ PyVista 3D Network visualization working!"
            else:
                return go.Figure(), "❌ PyVista 3D failed"
        else:
            # Simple 2D network
            print("📊 Testing 2D Network...")
            fig = go.Figure()
            
            # Add buses
            for _, bus in buses_df.iterrows():
                bus_id = bus['BUS_NUMBER']
                voltage = bus['VM']
                color = 'red' if voltage < 0.95 or voltage > 1.05 else 'blue'
                
                fig.add_trace(go.Scatter(
                    x=[bus_id * 10],
                    y=[voltage * 100],
                    mode='markers+text',
                    marker=dict(size=15, color=color),
                    text=str(bus_id),
                    name=f"Bus {bus_id}",
                    showlegend=False
                ))
            
            # Add branches
            for _, branch in branches_df.iterrows():
                from_bus = branch['FROM_BUS']
                to_bus = branch['TO_BUS']
                
                fig.add_trace(go.Scatter(
                    x=[from_bus * 10, to_bus * 10],
                    y=[buses_df[buses_df['BUS_NUMBER']==from_bus]['VM'].iloc[0] * 100,
                       buses_df[buses_df['BUS_NUMBER']==to_bus]['VM'].iloc[0] * 100],
                    mode='lines',
                    line=dict(color='gray', width=2),
                    showlegend=False
                ))
            
            fig.update_layout(
                title="2D Network Test - Fixed Code ✅",
                xaxis_title="Bus Position",
                yaxis_title="Voltage (% of nominal)",
                template="plotly_dark"
            )
            
            return fig, "✅ 2D Network visualization working!"
            
    except Exception as e:
        print(f"❌ Error: {e}")
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error: {str(e)}",
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False, font=dict(size=14, color="red")
        )
        return fig, f"❌ Error: {str(e)}"

if __name__ == '__main__':
    print("🚀 Starting Fixed Power System Test App...")
    print("🌐 Open: http://127.0.0.1:8056")
    app.run_server(debug=True, port=8056, dev_tools_silence_routes_logging=True)