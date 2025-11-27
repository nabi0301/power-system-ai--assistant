#!/usr/bin/env python3
"""
Simple PyVista 3D Network Test Application
Demonstrates the working PyVista 3D network enhancement
"""

import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import pandas as pd
import sqlite3

# Import our PyVista 3D enhancement
from pyvista_network_3d import get_enhanced_3d_network_graph, PYVISTA_AVAILABLE

print(f"🌐 PyVista 3D Network Test Application")
print(f"PyVista Available: {PYVISTA_AVAILABLE}")

# Load sample data from database
def load_database_data():
    """Load data from the database"""
    try:
        conn = sqlite3.connect('data.db')
        
        # Load base case data (case 0)
        buses_query = "SELECT * FROM BaseBusData WHERE base_case_id = 0 LIMIT 50"  # Limit for faster testing
        branches_query = "SELECT * FROM BaseBranchData WHERE base_case_id = 0 LIMIT 100"
        
        buses_df = pd.read_sql_query(buses_query, conn)
        branches_df = pd.read_sql_query(branches_query, conn)
        
        conn.close()
        
        print(f"✅ Loaded {len(buses_df)} buses and {len(branches_df)} branches for testing")
        return buses_df, branches_df
        
    except Exception as e:
        print(f"❌ Error loading database: {e}")
        # Create sample data for testing
        buses_df = pd.DataFrame({
            'BUS_NUMBER': range(1, 21),
            'BASE_KV': [345] * 5 + [138] * 10 + [69] * 5,
            'VM': [1.05, 1.02, 0.98, 1.01, 0.99] * 4,
            'TYPE': [3, 2, 1, 1, 2] * 4
        })
        
        branches_df = pd.DataFrame({
            'FROM_BUS': [1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
            'TO_BUS': [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 20],
            'PF': [150, 120, 90, 85, 110, 45, 60, 35, 25, 30, 40, 55, 70, 80, 95, 105, 115, 125, 135, 145],
            'RATE_A': [200, 180, 150, 120, 140, 80, 90, 60, 50, 45, 65, 75, 85, 95, 105, 115, 125, 135, 145, 155]
        })
        
        print(f"✅ Using sample data: {len(buses_df)} buses and {len(branches_df)} branches")
        return buses_df, branches_df

# Load data
buses_df, branches_df = load_database_data()

# Create Dash app
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("🌐 PyVista 3D Network Test", 
            style={"textAlign": "center", "color": "#00ffff", "margin": "20px"}),
    
    html.Div([
        html.H3("Enhanced 3D Power System Network Visualization"),
        html.P(f"PyVista Available: {'✅ Yes' if PYVISTA_AVAILABLE else '❌ No'}", 
               style={"color": "green" if PYVISTA_AVAILABLE else "red"}),
        html.Button("Generate 3D Network", id="generate-button", n_clicks=0,
                   style={"margin": "10px", "padding": "10px 20px", "backgroundColor": "#00ffff"}),
    ], style={"margin": "20px", "padding": "20px", "backgroundColor": "rgba(0, 30, 60, 0.8)", 
              "borderRadius": "10px", "color": "white"}),
    
    dcc.Graph(id="network-graph", style={"height": "700px"}),
    
    html.Div(id="status-output", style={"margin": "20px", "color": "white"})
])

@app.callback(
    [Output("network-graph", "figure"),
     Output("status-output", "children")],
    [Input("generate-button", "n_clicks")]
)
def update_graph(n_clicks):
    if n_clicks == 0:
        # Initial empty graph
        fig = go.Figure()
        fig.add_annotation(
            text="Click 'Generate 3D Network' to create visualization",
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False, font=dict(size=16, color="gray")
        )
        fig.update_layout(
            title="Ready to Generate 3D Network",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        return fig, "Ready to generate 3D network visualization..."
    
    try:
        print(f"\n🔧 Generating 3D network (attempt {n_clicks})...")
        
        # Generate 3D network using our PyVista enhancement
        fig = get_enhanced_3d_network_graph(
            buses_df, 
            branches_df, 
            case_id=0, 
            contingency_id=None
        )
        
        if fig is not None:
            print(f"✅ Successfully generated 3D network visualization")
            status = f"✅ Successfully generated PyVista-enhanced 3D network! (Attempt {n_clicks})"
            if PYVISTA_AVAILABLE:
                status += " | Using PyVista algorithms for superior 3D layout"
            else:
                status += " | Using advanced Plotly 3D fallback"
        else:
            print(f"❌ 3D network generation returned None")
            # Create error figure
            fig = go.Figure()
            fig.add_annotation(
                text="3D Network Generation Failed",
                x=0.5, y=0.5, xref="paper", yref="paper",
                showarrow=False, font=dict(size=16, color="red")
            )
            fig.update_layout(title="3D Network Error")
            status = f"❌ 3D network generation failed (Attempt {n_clicks})"
            
    except Exception as e:
        print(f"❌ Error generating 3D network: {e}")
        # Create error figure
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error: {str(e)}",
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False, font=dict(size=14, color="red")
        )
        fig.update_layout(title="3D Network Error")
        status = f"❌ Error generating 3D network: {str(e)}"
    
    return fig, status

if __name__ == '__main__':
    print("🚀 Starting PyVista 3D Network Test Application...")
    print("🌐 Open: http://127.0.0.1:8055")
    app.run_server(debug=True, port=8055)