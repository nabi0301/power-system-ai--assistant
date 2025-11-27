#!/usr/bin/env python3
"""
Test script for the minimizable database information section
"""

import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc

# Create test app
app = dash.Dash(__name__)

# Test layout with the minimizable database info section
app.layout = html.Div([
    html.H1("Database Info Toggle Test", style={"color": "#00ff88"}),
    
    # Minimizable Database Information Section
    html.Div([
        html.Div([
            html.H3("Database Information", style={
                "color": "#00ff88", 
                "textShadow": "0 0 5px rgba(0, 255, 136, 0.5)",
                "margin": "0",
                "display": "inline-block"
            }),
            html.Button("▼", 
                id="db-info-toggle",
                style={
                    "background": "none",
                    "border": "none",
                    "color": "#00ff88",
                    "fontSize": "16px",
                    "cursor": "pointer",
                    "float": "right",
                    "padding": "0",
                    "margin": "0"
                }
            )
        ], style={"marginBottom": "10px"}),
        html.Div([
            html.Ul([
                html.Li("✅ Total Buses: 118 (IEEE 118-bus system)", style={"color": "#e0e0e0"}),
                html.Li("✅ Total Branches: 186 transmission lines", style={"color": "#e0e0e0"}),
                html.Li("✅ Real-time data from SQLite database", style={"color": "#e0e0e0"}),
                html.Li("✅ Base case, contingency, and optimization results", style={"color": "#e0e0e0"})
            ])
        ], id="db-info-content", style={"display": "block"})
    ], style={
        "margin": "20px", 
        "padding": "20px", 
        "backgroundColor": "rgba(0, 50, 30, 0.8)", 
        "borderRadius": "10px",
        "border": "1px solid rgba(0, 255, 136, 0.3)",
        "boxShadow": "0 0 20px rgba(0, 255, 136, 0.2)"
    }),
    
    html.Div(id="status", style={"color": "#00ff88", "marginTop": "20px"})
], style={"backgroundColor": "#001122", "minHeight": "100vh", "padding": "20px"})

# Callback to toggle database information section
@app.callback(
    [Output("db-info-content", "style"),
     Output("db-info-toggle", "children"),
     Output("status", "children")],
    [Input("db-info-toggle", "n_clicks")],
    prevent_initial_call=True
)
def toggle_database_info(n_clicks):
    """Toggle the visibility of database information content"""
    if n_clicks is None:
        n_clicks = 0
    
    # If even number of clicks (including 0), show content
    if n_clicks % 2 == 0:
        return {"display": "block"}, "▼", f"Database info is visible (clicks: {n_clicks})"
    else:
        return {"display": "none"}, "▶", f"Database info is hidden (clicks: {n_clicks})"

if __name__ == "__main__":
    print("🧪 Testing minimizable database information section...")
    print("🌐 Open: http://127.0.0.1:8055")
    app.run(debug=True, port=8055)