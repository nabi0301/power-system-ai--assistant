import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

# Simple test app to check tabs
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    html.H1("Simple Tab Test", style={"textAlign": "center", "marginBottom": "20px"}),
    
    dbc.Tabs(
        id="test-tabs",
        active_tab="tab1",
        children=[
            dbc.Tab(
                label="Network Visualization",
                tab_id="tab1",
                children=[
                    html.Div([
                        html.H3("Network Tab Content"),
                        html.P("This is the network visualization tab.")
                    ], style={"padding": "20px"})
                ]
            ),
            dbc.Tab(
                label="AI Assistant",
                tab_id="tab2",
                children=[
                    html.Div([
                        html.H3("AI Assistant Tab Content"),
                        html.P("This is the AI assistant tab.")
                    ], style={"padding": "20px"})
                ]
            ),
        ]
    )
], fluid=True)

if __name__ == "__main__":
    print("Starting simple tab test on port 8051...")
    app.run(debug=True, port=8051)