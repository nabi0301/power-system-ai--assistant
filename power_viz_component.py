"""
Power Visualization Integration Module for data_viz_fall.py
---------------------------------------------------------
This file integrates the power_viz_with_database.py functionality
as a tab in the data_viz_fall.py application.
"""

import dash
from dash import html, dcc, Input, Output, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import sqlite3
import os
import sys
import importlib.util
import numpy as np

# Import necessary functions and variables from power_viz_with_database.py
# We'll load the module dynamically to avoid import issues
def load_power_viz_module():
    """Dynamically load the power_viz_with_database.py module"""
    try:
        module_path = os.path.join(os.path.dirname(__file__), 'power_viz_with_database.py')
        spec = importlib.util.spec_from_file_location("power_viz_module", module_path)
        power_viz = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(power_viz)
        print("✅ Successfully loaded power_viz_with_database.py module")
        return power_viz
    except Exception as e:
        print(f"❌ Error loading power_viz_with_database.py: {e}")
        return None

# Load the power_viz module
power_viz = load_power_viz_module()

class PowerVizComponent:
    """
    A component class that encapsulates the power_viz_with_database.py functionality
    to be integrated into data_viz_fall.py as a tab
    """
    
    def __init__(self, database_path='data.db'):
        """Initialize the PowerVizComponent with the database path"""
        self.database_path = database_path
        
        # Load data from database
        self.buses_df, self.branches_df, self.comparison_df = self.load_database_data()
        
        # Set default visualization type
        self.current_viz_type = 'network'
        self.current_case_id = None
        self.current_contingency_id = None
        
    def load_database_data(self):
        """Load data from the database, similar to power_viz_with_database.py"""
        try:
            # Use the function from power_viz_with_database.py if available
            if power_viz and hasattr(power_viz, 'load_database_data'):
                return power_viz.load_database_data()
            
            # Otherwise, use our own implementation
            conn = sqlite3.connect(self.database_path)
            
            # Load base case bus data
            buses_query = """
            SELECT base_case_id, BUS_NUMBER, VM, VA, BASE_KV, PG, QG, PD, QD
            FROM BaseBusData 
            WHERE base_case_id = 0
            ORDER BY BUS_NUMBER
            """
            buses_df = pd.read_sql_query(buses_query, conn)
            
            # Load base case branch data
            branches_query = """
            SELECT base_case_id, branch_number, From_Bus, To_Bus, PF, QF, MVA, RATE, VIO
            FROM BaseBranchData 
            WHERE base_case_id = 0
            ORDER BY branch_number
            """
            branches_df = pd.read_sql_query(branches_query, conn)
            
            # Load SLR vs DLR comparison data for visualization
            slr_query = """
            SELECT base_case_id, contingency_case_id, From_Bus, To_Bus, MVA as SLR_MVA, 
                   RATE as SLR_RATE, VIO as SLR_VIO
            FROM SLR_Branches 
            WHERE base_case_id = 42 AND contingency_case_id = 123
            ORDER BY branch_number
            """
            slr_df = pd.read_sql_query(slr_query, conn)
            
            dlr_query = """
            SELECT base_case_id, contingency_case_id, From_Bus, To_Bus, MVA as DLR_MVA, 
                   RATE as DLR_RATE, VIO as DLR_VIO
            FROM DLR_Branches 
            WHERE base_case_id = 42 AND contingency_case_id = 123
            ORDER BY branch_number
            """
            dlr_df = pd.read_sql_query(dlr_query, conn)
            
            conn.close()
            
            # Merge SLR and DLR data for comparison
            if not slr_df.empty and not dlr_df.empty:
                comparison_df = pd.merge(slr_df, dlr_df, on=['From_Bus', 'To_Bus'], 
                                       suffixes=('_SLR', '_DLR'), how='inner')
            else:
                comparison_df = pd.DataFrame()
            
            # Add coordinates for bus visualization (simple grid layout)
            buses_df['x_coord'] = (buses_df['BUS_NUMBER'] % 12) * 30
            buses_df['y_coord'] = (buses_df['BUS_NUMBER'] // 12) * 25
            
            print(f"Loaded {len(buses_df)} buses, {len(branches_df)} branches, {len(comparison_df)} comparison cases")
            return buses_df, branches_df, comparison_df
            
        except Exception as e:
            print(f"Database error: {e}")
            # Return empty dataframes as fallback
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    def get_layout(self):
        """Get the layout for the power visualization tab"""
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H3("Power System Visualization", 
                           className="text-center mb-4",
                           style={"color": "#0D8767"})
                ], width=12)
            ]),
            
            dbc.Row([
                dbc.Col([
                    # Visualization selector
                    html.Div([
                        html.H4("📈 Select Visualization:"),
                        dcc.Dropdown(
                            id='power-viz-selector',
                            options=[
                                {'label': '🏠 Main Network View', 'value': 'network'},
                                {'label': '⚡ Voltage Analysis', 'value': 'voltage'},
                                {'label': '📊 Loading Analysis', 'value': 'loading'},
                                {'label': '⚠️ Violation Analysis', 'value': 'violations'},
                                {'label': '🔄 SLR vs DLR Comparison', 'value': 'comparison'},
                                {'label': '🏭 Generator Analysis', 'value': 'generators'}
                            ],
                            value='network',
                            style={'width': '100%'}
                        )
                    ], className="mb-4", style={
                        "padding": "15px",
                        "backgroundColor": "#e3f2fd",
                        "borderRadius": "5px"
                    }),
                    
                    # AI Chat Interface toggle
                    dbc.Button(
                        "🤖 Toggle AI Assistant",
                        id="power-viz-chat-toggle",
                        color="primary",
                        className="mb-4",
                        style={"width": "100%"}
                    ),
                    
                    # Case and contingency ID inputs
                    dbc.Card([
                        dbc.CardHeader("Case Selection"),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Base Case ID:"),
                                    dcc.Input(
                                        id="power-viz-case-id",
                                        type="number",
                                        value=0,
                                        min=0,
                                        style={"width": "100%"}
                                    )
                                ], width=6),
                                dbc.Col([
                                    html.Label("Contingency ID:"),
                                    dcc.Input(
                                        id="power-viz-contingency-id",
                                        type="number",
                                        placeholder="Optional",
                                        min=0,
                                        style={"width": "100%"}
                                    )
                                ], width=6)
                            ]),
                            dbc.Button(
                                "Update View",
                                id="power-viz-update-btn",
                                color="success",
                                className="mt-3",
                                style={"width": "100%"}
                            )
                        ])
                    ], className="mb-4")
                ], width=3),
                
                dbc.Col([
                    # Main visualization area
                    dbc.Card([
                        dbc.CardBody([
                            dcc.Loading(
                                id="power-viz-loading",
                                type="circle",
                                children=[dcc.Graph(
                                    id="power-viz-graph",
                                    figure=self.create_initial_figure(),
                                    style={"height": "600px"}
                                )]
                            )
                        ])
                    ]),
                    
                    # Description area
                    dbc.Card([
                        dbc.CardHeader("Visualization Description"),
                        dbc.CardBody([
                            html.Div(
                                id="power-viz-description",
                                children=self.get_default_description(),
                                style={"height": "150px", "overflowY": "auto"}
                            )
                        ])
                    ], className="mt-4")
                ], width=9)
            ]),
            
            # AI Chat Interface (initially hidden)
            dbc.Collapse(
                dbc.Card([
                    dbc.CardHeader([
                        html.H4("🤖 AI Power Systems Assistant", className="d-inline"),
                        dbc.Button(
                            "✕", 
                            id="power-viz-chat-close",
                            color="link",
                            className="float-right"
                        )
                    ]),
                    dbc.CardBody([
                        html.Div(
                            id="power-viz-chat-messages",
                            children=[
                                html.Div(
                                    "Hi! I'm your power system assistant. I can help you analyze power systems data. Ask me about voltages, loadings, violations, or SLR/DLR comparisons!",
                                    className="mb-3 p-3 bg-light rounded"
                                )
                            ],
                            style={"height": "300px", "overflowY": "auto"}
                        ),
                        dbc.InputGroup([
                            dbc.Input(
                                id="power-viz-chat-input",
                                placeholder="Ask me about power systems...",
                                type="text"
                            ),
                            dbc.InputGroupAddon(
                                dbc.Button("Send", id="power-viz-chat-send", color="primary"),
                                addon_type="append"
                            )
                        ])
                    ])
                ]),
                id="power-viz-chat-container",
                is_open=False
            )
        ], fluid=True)

    def create_initial_figure(self):
        """Create initial power system visualization figure"""
        try:
            # Use the power_viz_with_database.py function if available
            if power_viz:
                if hasattr(power_viz, 'create_power_system_plot'):
                    return power_viz.create_power_system_plot(self.buses_df, self.branches_df)
            
            # Fallback to a minimal implementation
            fig = go.Figure()
            
            # Check if we have bus data
            if not self.buses_df.empty:
                # Add bus points with real voltage data
                fig.add_trace(go.Scatter(
                    x=self.buses_df['x_coord'],
                    y=self.buses_df['y_coord'],
                    mode='markers',
                    marker=dict(
                        size=10,  
                        color=self.buses_df['VM'],     # Color based on voltage magnitude
                        colorscale='RdYlGn',
                        showscale=True,
                        colorbar=dict(title="Voltage Magnitude (p.u.)")
                    ),
                    text=self.buses_df.apply(
                        lambda row: f"Bus {int(row['BUS_NUMBER'])}<br>Voltage: {row['VM']:.3f} p.u.",
                        axis=1
                    ),
                    hovertemplate='%{text}<extra></extra>',
                    name='Buses'
                ))
            
                # Add transmission lines if branch data is available
                if not self.branches_df.empty:
                    for _, branch in self.branches_df.head(50).iterrows():  # Show first 50 lines only
                        from_bus_data = self.buses_df[self.buses_df['BUS_NUMBER'] == branch['From_Bus']]
                        to_bus_data = self.buses_df[self.buses_df['BUS_NUMBER'] == branch['To_Bus']]
                        
                        if not from_bus_data.empty and not to_bus_data.empty:
                            # Line color based on loading percentage
                            loading_pct = (branch['MVA'] / branch['RATE']) * 100 if branch['RATE'] > 0 else 0
                            line_color = 'red' if loading_pct > 90 else 'orange' if loading_pct > 75 else 'green'
                            
                            fig.add_trace(go.Scatter(
                                x=[from_bus_data.iloc[0]['x_coord'], to_bus_data.iloc[0]['x_coord']],
                                y=[from_bus_data.iloc[0]['y_coord'], to_bus_data.iloc[0]['y_coord']],
                                mode='lines',
                                line=dict(color=line_color, width=2),
                                hovertemplate=f'Line {int(branch["From_Bus"])}-{int(branch["To_Bus"])}<br>Loading: {loading_pct:.1f}%<extra></extra>',
                                showlegend=False
                            ))
            
            # If no data, add a message to the figure
            if self.buses_df.empty or self.branches_df.empty:
                fig.add_annotation(
                    text="No power system data available. Please check database connection.",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=20)
                )
            
            # Update layout
            fig.update_layout(
                title="IEEE 118-Bus Power System Network",
                showlegend=True,
                height=600,
                template="plotly_white",
                margin=dict(l=20, r=20, t=40, b=20)
            )
            
            return fig
        except Exception as e:
            # Return a basic figure with error message if something goes wrong
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error creating visualization: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="red")
            )
            fig.update_layout(title="Visualization Error")
            return fig

    def get_default_description(self):
        """Get default description for the visualization"""
        return html.Div([
            html.H5("Power System Visualization"),
            html.P([
                "This visualization shows an IEEE 118-bus power system model with real-time data from the database. ",
                html.Br(),
                "Use the dropdown to switch between different visualization types, and the AI assistant for analysis."
            ]),
            html.Ul([
                html.Li("Bus colors represent voltage magnitude (green = good, red = violations)"),
                html.Li("Line colors indicate loading percentage (green = normal, red = overloaded)"),
                html.Li("Explore different visualization types using the dropdown above")
            ])
        ])

    def update_visualization(self, viz_type, case_id=None, contingency_id=None):
        """Update the visualization based on selected type and case IDs"""
        try:
            # Use functions from power_viz_with_database.py if available
            if power_viz:
                if hasattr(power_viz, 'update_visualization'):
                    return power_viz.update_visualization(viz_type, case_id, contingency_id)
                
            # Create figures based on visualization type
            if viz_type == 'voltage':
                # Create voltage-focused visualization
                fig = self.create_voltage_visualization(case_id, contingency_id)
                description = self.get_voltage_description()
                
            elif viz_type == 'loading':
                # Create loading-focused visualization
                fig = self.create_loading_visualization(case_id, contingency_id)
                description = self.get_loading_description()
                
            elif viz_type == 'violations':
                # Create violation-focused visualization
                fig = self.create_violations_visualization(case_id, contingency_id)
                description = self.get_violations_description()
                
            elif viz_type == 'comparison':
                # Create SLR vs DLR comparison visualization
                fig = self.create_comparison_visualization()
                description = self.get_comparison_description()
                
            elif viz_type == 'generators':
                # Create generator analysis visualization
                fig = self.create_generators_visualization(case_id, contingency_id)
                description = self.get_generators_description()
                
            else:
                # Default to network visualization
                fig = self.create_network_visualization(case_id, contingency_id)
                description = self.get_network_description()
            
            return fig, description
            
        except Exception as e:
            # Return a basic figure with error message if something goes wrong
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error updating visualization: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="red")
            )
            fig.update_layout(title="Visualization Error")
            
            description = html.Div([
                html.H5("Error Updating Visualization", style={"color": "red"}),
                html.P(f"An error occurred: {str(e)}"),
                html.P("Please check case IDs or try a different visualization type.")
            ])
            
            return fig, description

    def create_voltage_visualization(self, case_id=None, contingency_id=None):
        """Create voltage-focused visualization"""
        try:
            # Use power_viz function if available
            if power_viz and hasattr(power_viz, 'create_voltage_analysis_plot'):
                if case_id is not None:
                    # Load case-specific data from database
                    buses_df, _ = self.load_case_data(case_id, contingency_id)
                    return power_viz.create_voltage_analysis_plot(buses_df, case_id)
                else:
                    return power_viz.create_voltage_analysis_plot(self.buses_df)
                    
            # Simple implementation
            fig = go.Figure()
            
            # Determine which data to use
            if case_id is not None:
                buses_df, _ = self.load_case_data(case_id, contingency_id)
            else:
                buses_df = self.buses_df
            
            if buses_df.empty:
                fig.add_annotation(
                    text="No voltage data available for the selected case.",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=16)
                )
                return fig
                
            # Create histogram of voltage magnitudes
            fig.add_trace(go.Histogram(
                x=buses_df['VM'],
                nbinsx=20,
                marker_color='skyblue',
                name='Voltage Distribution'
            ))
            
            # Add voltage limits as vertical lines
            fig.add_vline(x=0.95, line_dash="dash", line_color="red", 
                        annotation_text="Low Voltage Limit (0.95 p.u.)")
            fig.add_vline(x=1.05, line_dash="dash", line_color="red",
                        annotation_text="High Voltage Limit (1.05 p.u.)")
            
            # Add case ID to title if provided
            title_prefix = f"Case {case_id}"
            if contingency_id is not None:
                title_prefix += f", Contingency {contingency_id}"
            title = f"{title_prefix} - " if case_id is not None else ""
            title += "Bus Voltage Analysis"
            
            fig.update_layout(
                title=title,
                xaxis_title="Voltage Magnitude (p.u.)",
                yaxis_title="Number of Buses",
                height=600
            )
            
            return fig
            
        except Exception as e:
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error creating voltage visualization: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="red")
            )
            return fig

    def create_loading_visualization(self, case_id=None, contingency_id=None):
        """Create loading-focused visualization"""
        try:
            # Use power_viz function if available
            if power_viz and hasattr(power_viz, 'create_loading_analysis_plot'):
                if case_id is not None:
                    # Load case-specific data from database
                    _, branches_df = self.load_case_data(case_id, contingency_id)
                    return power_viz.create_loading_analysis_plot(branches_df, case_id)
                else:
                    return power_viz.create_loading_analysis_plot(self.branches_df)
            
            # Simple implementation
            fig = go.Figure()
            
            # Determine which data to use
            if case_id is not None:
                _, branches_df = self.load_case_data(case_id, contingency_id)
            else:
                branches_df = self.branches_df
                
            if branches_df.empty:
                fig.add_annotation(
                    text="No loading data available for the selected case.",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=16)
                )
                return fig
                
            # Calculate loading percentages
            loading_pct = (branches_df['MVA'] / branches_df['RATE'] * 100).fillna(0)
            
            # Create scatter plot of loading percentages
            fig.add_trace(go.Scatter(
                x=list(range(len(loading_pct))),
                y=loading_pct,
                mode='markers',
                marker=dict(
                    size=8,
                    color=loading_pct,
                    colorscale='RdYlGn_r',
                    showscale=True,
                    colorbar=dict(title="Loading (%)")
                ),
                text=[f"Line {row['From_Bus']}-{row['To_Bus']}: {pct:.1f}%" 
                     for (_, row), pct in zip(branches_df.iterrows(), loading_pct)],
                hovertemplate='%{text}<extra></extra>',
                name='Branch Loading'
            ))
            
            # Add critical loading lines
            fig.add_hline(y=100, line_dash="dash", line_color="red",
                        annotation_text="100% Loading (Critical)")
            fig.add_hline(y=90, line_dash="dash", line_color="orange",
                        annotation_text="90% Loading (Warning)")
            
            # Add case ID to title if provided
            title_prefix = f"Case {case_id}"
            if contingency_id is not None:
                title_prefix += f", Contingency {contingency_id}"
            title = f"{title_prefix} - " if case_id is not None else ""
            title += "Transmission Line Loading Analysis"
            
            fig.update_layout(
                title=title,
                xaxis_title="Branch Index",
                yaxis_title="Loading Percentage (%)",
                height=600
            )
            
            return fig
            
        except Exception as e:
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error creating loading visualization: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="red")
            )
            return fig

    def create_violations_visualization(self, case_id=None, contingency_id=None):
        """Create violation-focused visualization"""
        try:
            # Use power_viz function if available
            if power_viz and hasattr(power_viz, 'create_violation_analysis_plot'):
                if case_id is not None:
                    # Load case-specific data from database
                    _, branches_df = self.load_case_data(case_id, contingency_id)
                    return power_viz.create_violation_analysis_plot(branches_df, case_id)
                else:
                    return power_viz.create_violation_analysis_plot(self.branches_df)
            
            # Simple implementation
            fig = go.Figure()
            
            # Determine which data to use
            if case_id is not None:
                _, branches_df = self.load_case_data(case_id, contingency_id)
            else:
                branches_df = self.branches_df
                
            if branches_df.empty:
                fig.add_annotation(
                    text="No violation data available for the selected case.",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=16)
                )
                return fig
                
            # Filter violated branches (>100% loading)
            loading_pct = (branches_df['MVA'] / branches_df['RATE'] * 100).fillna(0)
            violated_branches = branches_df[loading_pct > 100].copy()
            violated_loading = loading_pct[loading_pct > 100]
            
            if len(violated_branches) > 0:
                fig.add_trace(go.Bar(
                    x=[f"{int(row['From_Bus'])}-{int(row['To_Bus'])}" for _, row in violated_branches.iterrows()],
                    y=violated_loading,
                    marker_color='red',
                    name='Overloaded Lines',
                    text=[f"{val:.1f}%" for val in violated_loading],
                    textposition='outside'
                ))
                
                title = f"Violation Analysis - {len(violated_branches)} Overloaded Lines"
            else:
                fig.add_annotation(
                    text="No violations detected in current analysis",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=16)
                )
                title = "Violation Analysis - No Violations Found"
            
            # Add case ID to title if provided
            if case_id is not None and "No Violations" not in title:
                title_prefix = f"Case {case_id}"
                if contingency_id is not None:
                    title_prefix += f", Contingency {contingency_id}"
                title = f"{title_prefix} - {title}"
                
            fig.update_layout(
                title=title,
                xaxis_title="Transmission Line",
                yaxis_title="Loading Percentage (%)",
                height=600
            )
            
            return fig
            
        except Exception as e:
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error creating violations visualization: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="red")
            )
            return fig

    def create_comparison_visualization(self):
        """Create SLR vs DLR comparison visualization"""
        try:
            # Use power_viz function if available
            if power_viz and hasattr(power_viz, 'create_slr_dlr_comparison'):
                return power_viz.create_slr_dlr_comparison(self.comparison_df)
            
            # Simple implementation
            fig = go.Figure()
            
            if self.comparison_df.empty:
                # Return empty figure if no comparison data
                fig.add_annotation(
                    text="No SLR/DLR comparison data available",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=16)
                )
                fig.update_layout(title="SLR vs DLR Comparison", height=600)
                return fig
            
            # SLR violations
            fig.add_trace(go.Scatter(
                x=self.comparison_df.index,
                y=self.comparison_df['SLR_VIO'],
                mode='markers',
                name='SLR Violations (%)',
                marker=dict(color='red', size=8),
                text=self.comparison_df.apply(lambda row: f"Line {int(row['From_Bus'])}-{int(row['To_Bus'])}<br>SLR: {row['SLR_VIO']:.1f}%", axis=1),
                hovertemplate='%{text}<extra></extra>'
            ))
            
            # DLR violations
            fig.add_trace(go.Scatter(
                x=self.comparison_df.index,
                y=self.comparison_df['DLR_VIO'],
                mode='markers',
                name='DLR Violations (%)',
                marker=dict(color='blue', size=8),
                text=self.comparison_df.apply(lambda row: f"Line {int(row['From_Bus'])}-{int(row['To_Bus'])}<br>DLR: {row['DLR_VIO']:.1f}%", axis=1),
                hovertemplate='%{text}<extra></extra>'
            ))
            
            fig.update_layout(
                title=f"SLR vs DLR Violation Analysis - {len(self.comparison_df)} Cases",
                xaxis_title="Branch Index",
                yaxis_title="Violation Percentage (%)",
                height=600,
                template="plotly_white"
            )
            
            return fig
            
        except Exception as e:
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error creating comparison visualization: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="red")
            )
            return fig

    def create_generators_visualization(self, case_id=None, contingency_id=None):
        """Create generator analysis visualization"""
        try:
            # Use power_viz function if available
            if power_viz and hasattr(power_viz, 'create_generator_analysis_plot'):
                return power_viz.create_generator_analysis_plot(case_id, contingency_id)
            
            # Simple implementation - default to network view since generator analysis is complex
            fig = go.Figure()
            fig.add_annotation(
                text="Generator analysis visualization requires the full power_viz_with_database.py module",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
            fig.update_layout(title="Generator Analysis (Not Available)", height=600)
            return fig
            
        except Exception as e:
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error creating generator visualization: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="red")
            )
            return fig

    def create_network_visualization(self, case_id=None, contingency_id=None):
        """Create network visualization"""
        try:
            # Use power_viz function if available
            if power_viz and hasattr(power_viz, 'create_power_system_plot'):
                if case_id is not None:
                    # Load case-specific data from database
                    buses_df, branches_df = self.load_case_data(case_id, contingency_id)
                    return power_viz.create_power_system_plot(buses_df, branches_df, case_id)
                else:
                    return power_viz.create_power_system_plot(self.buses_df, self.branches_df)
            
            # Simple implementation (similar to create_initial_figure but with case-specific data)
            fig = go.Figure()
            
            # Determine which data to use
            if case_id is not None:
                buses_df, branches_df = self.load_case_data(case_id, contingency_id)
            else:
                buses_df, branches_df = self.buses_df, self.branches_df
                
            # Check if we have bus data
            if buses_df.empty or branches_df.empty:
                fig.add_annotation(
                    text="No network data available for the selected case.",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=16)
                )
                return fig
                
            # Add bus points with real voltage data
            fig.add_trace(go.Scatter(
                x=buses_df['x_coord'] if 'x_coord' in buses_df.columns else buses_df['BUS_NUMBER'],
                y=buses_df['y_coord'] if 'y_coord' in buses_df.columns else buses_df['VM'],
                mode='markers',
                marker=dict(
                    size=10,  
                    color=buses_df['VM'],     # Color based on voltage magnitude
                    colorscale='RdYlGn',
                    showscale=True,
                    colorbar=dict(title="Voltage Magnitude (p.u.)")
                ),
                text=buses_df.apply(
                    lambda row: f"Bus {int(row['BUS_NUMBER'])}<br>Voltage: {row['VM']:.3f} p.u.",
                    axis=1
                ),
                hovertemplate='%{text}<extra></extra>',
                name='Buses'
            ))
            
            # Add transmission lines
            for _, branch in branches_df.head(50).iterrows():  # Show first 50 lines only
                from_bus_data = buses_df[buses_df['BUS_NUMBER'] == branch['From_Bus']]
                to_bus_data = buses_df[buses_df['BUS_NUMBER'] == branch['To_Bus']]
                
                if not from_bus_data.empty and not to_bus_data.empty:
                    # Line color based on loading percentage
                    loading_pct = (branch['MVA'] / branch['RATE']) * 100 if branch['RATE'] > 0 else 0
                    line_color = 'red' if loading_pct > 90 else 'orange' if loading_pct > 75 else 'green'
                    
                    # Get coordinates (either from x_coord/y_coord or use BUS_NUMBER/VM as fallback)
                    from_x = from_bus_data.iloc[0]['x_coord'] if 'x_coord' in from_bus_data.columns else from_bus_data.iloc[0]['BUS_NUMBER']
                    from_y = from_bus_data.iloc[0]['y_coord'] if 'y_coord' in from_bus_data.columns else from_bus_data.iloc[0]['VM']
                    to_x = to_bus_data.iloc[0]['x_coord'] if 'x_coord' in to_bus_data.columns else to_bus_data.iloc[0]['BUS_NUMBER']
                    to_y = to_bus_data.iloc[0]['y_coord'] if 'y_coord' in to_bus_data.columns else to_bus_data.iloc[0]['VM']
                    
                    fig.add_trace(go.Scatter(
                        x=[from_x, to_x],
                        y=[from_y, to_y],
                        mode='lines',
                        line=dict(color=line_color, width=2),
                        hovertemplate=f'Line {int(branch["From_Bus"])}-{int(branch["To_Bus"])}<br>Loading: {loading_pct:.1f}%<extra></extra>',
                        showlegend=False
                    ))
            
            # Add case ID to title if provided
            title_prefix = f"Case {case_id}"
            if contingency_id is not None:
                title_prefix += f", Contingency {contingency_id}"
            title = f"{title_prefix} - " if case_id is not None else ""
            title += "IEEE 118-Bus Power System Network"
            
            fig.update_layout(
                title=title,
                showlegend=True,
                height=600,
                template="plotly_white"
            )
            
            return fig
            
        except Exception as e:
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error creating network visualization: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="red")
            )
            return fig

    def load_case_data(self, case_id, contingency_id=None):
        """Load case-specific data from the database"""
        try:
            conn = sqlite3.connect(self.database_path)
            
            if contingency_id is not None:
                # Get contingency-specific data
                bus_query = f"""
                SELECT * FROM ContingencyBusData 
                WHERE base_case_id = {case_id} AND contingency_case_id = {contingency_id}
                """
                branch_query = f"""
                SELECT * FROM ContingencyBranchData 
                WHERE base_case_id = {case_id} AND contingency_case_id = {contingency_id}
                """
            else:
                # Get base case data
                bus_query = f"""
                SELECT * FROM BaseBusData 
                WHERE base_case_id = {case_id}
                """
                branch_query = f"""
                SELECT * FROM BaseBranchData 
                WHERE base_case_id = {case_id}
                """
            
            buses_df = pd.read_sql_query(bus_query, conn)
            branches_df = pd.read_sql_query(branch_query, conn)
            
            # Add coordinates for visualization
            if not buses_df.empty and 'x_coord' not in buses_df.columns:
                buses_df['x_coord'] = (buses_df['BUS_NUMBER'] % 12) * 30
                buses_df['y_coord'] = (buses_df['BUS_NUMBER'] // 12) * 25
            
            conn.close()
            return buses_df, branches_df
            
        except Exception as e:
            print(f"Error loading case data: {e}")
            return pd.DataFrame(), pd.DataFrame()

    def get_voltage_description(self):
        """Get description for voltage visualization"""
        return html.Div([
            html.H5("⚡ Voltage Analysis"),
            html.P([
                "This visualization shows the distribution of bus voltage magnitudes across the power system. ",
                html.Br(),
                "Voltage is typically maintained within ±5% of nominal (0.95-1.05 p.u.) to ensure proper equipment operation."
            ]),
            html.Ul([
                html.Li("Red dashed lines show voltage limits (0.95 and 1.05 p.u.)"),
                html.Li("Voltages outside these limits may indicate power quality issues"),
                html.Li("Low voltages can lead to increased losses and potential voltage collapse"),
                html.Li("High voltages may damage equipment and reduce system stability")
            ])
        ])

    def get_loading_description(self):
        """Get description for loading visualization"""
        return html.Div([
            html.H5("📊 Loading Analysis"),
            html.P([
                "This visualization shows the loading percentage of each transmission line in the power system. ",
                html.Br(),
                "Loading is calculated as the ratio of apparent power flow (MVA) to the line's thermal rating."
            ]),
            html.Ul([
                html.Li("Red dashed line shows the critical 100% loading limit"),
                html.Li("Orange dashed line shows the warning level at 90% loading"),
                html.Li("Colors indicate stress level (green = normal, yellow = warning, red = overloaded)"),
                html.Li("Overloaded lines may overheat, sag excessively, or trip offline")
            ])
        ])

    def get_violations_description(self):
        """Get description for violations visualization"""
        return html.Div([
            html.H5("⚠️ Violation Analysis"),
            html.P([
                "This visualization highlights only the overloaded transmission lines in the system. ",
                html.Br(),
                "A violation occurs when the apparent power flow (MVA) exceeds the line's thermal rating."
            ]),
            html.Ul([
                html.Li("Only lines above 100% loading are shown"),
                html.Li("Higher percentages indicate more severe violations"),
                html.Li("Violations require immediate attention to prevent equipment damage"),
                html.Li("No violations shown means all lines are operating within limits")
            ])
        ])

    def get_comparison_description(self):
        """Get description for comparison visualization"""
        return html.Div([
            html.H5("🔄 SLR vs DLR Comparison"),
            html.P([
                "This visualization compares Static Line Rating (SLR) and Dynamic Line Rating (DLR) methodologies. ",
                html.Br(),
                "Each point represents a transmission line and its violation percentage under each method."
            ]),
            html.Ul([
                html.Li("Red points (SLR) show violations with traditional fixed ratings"),
                html.Li("Blue points (DLR) show violations with weather-adjusted ratings"),
                html.Li("DLR typically results in lower violation percentages than SLR"),
                html.Li("The difference between points indicates the benefit of using DLR")
            ])
        ])

    def get_generators_description(self):
        """Get description for generators visualization"""
        return html.Div([
            html.H5("🏭 Generator Analysis"),
            html.P([
                "This visualization shows generator dispatch and redispatch information. ",
                html.Br(),
                "It compares initial and adjusted generation levels for different generator buses."
            ]),
            html.Ul([
                html.Li("Generator redispatch is used to relieve transmission congestion"),
                html.Li("Bars show the difference between initial and adjusted generation"),
                html.Li("Positive changes indicate increased generation"),
                html.Li("Negative changes indicate decreased generation")
            ])
        ])

    def get_network_description(self):
        """Get description for network visualization"""
        return html.Div([
            html.H5("🏠 Network Visualization"),
            html.P([
                "This visualization shows the complete power system network topology. ",
                html.Br(),
                "It displays buses and transmission lines with their real-time operating conditions."
            ]),
            html.Ul([
                html.Li("Bus colors represent voltage magnitude (green = good, red = violations)"),
                html.Li("Bus sizes may indicate load or generation level"),
                html.Li("Line colors indicate loading percentage (green = normal, orange = warning, red = overloaded)"),
                html.Li("Hover over elements to see detailed information")
            ])
        ])

    def process_ai_chat(self, user_message, current_viz_type):
        """Process AI chat messages and return response"""
        if not user_message:
            return "Please enter a message to continue the conversation."
            
        # Use power_viz function if available
        if power_viz and hasattr(power_viz, 'get_ai_response'):
            try:
                response = power_viz.get_ai_response(user_message, current_viz_type)
                # Handle different return formats from get_ai_response
                if isinstance(response, tuple):
                    # Format varies, could be (response_text, viz_command, case_id) 
                    # or (response_text, viz_command, case_id, contingency_id)
                    return response[0]  # Just return the text part
                else:
                    return response
            except Exception as e:
                print(f"Error using power_viz AI response: {e}")
        
        # Simple fallback responses if power_viz is not available
        simple_responses = {
            'voltage': "The voltage analysis shows bus voltages across the system. Most buses should operate within 0.95-1.05 p.u. for proper power quality.",
            'loading': "Line loading analysis helps identify potentially overloaded transmission lines. Lines above 90% loading may need monitoring.",
            'violations': "Violation analysis highlights equipment operating beyond safe limits. Immediate action may be needed for overloaded lines.",
            'comparison': "SLR vs DLR comparison shows how dynamic line ratings can increase transmission capacity compared to static ratings.",
            'generators': "Generator analysis shows how power plants are dispatched to meet demand while respecting system constraints.",
            'network': "The network view shows the complete power system topology with real-time operating conditions."
        }
        
        # Generate a basic response based on the visualization type and user query
        if "voltage" in user_message.lower():
            return simple_responses['voltage']
        elif "load" in user_message.lower():
            return simple_responses['loading']
        elif "violat" in user_message.lower():
            return simple_responses['violations']
        elif "compar" in user_message.lower() or "slr" in user_message.lower() or "dlr" in user_message.lower():
            return simple_responses['comparison']
        elif "generat" in user_message.lower():
            return simple_responses['generators']
        elif "network" in user_message.lower() or "topology" in user_message.lower():
            return simple_responses['network']
        else:
            return f"I'm a simplified AI assistant for power system analysis. I can help explain visualizations and power system concepts. Currently showing {current_viz_type} visualization."


# Function to register callbacks for PowerVizComponent
def register_power_viz_callbacks(app):
    """Register the callbacks for the PowerVizComponent"""
    
    @app.callback(
        Output("power-viz-graph", "figure"),
        Output("power-viz-description", "children"),
        [
            Input("power-viz-selector", "value"),
            Input("power-viz-update-btn", "n_clicks"),
            Input("power-viz-chat-send", "n_clicks")
        ],
        [
            State("power-viz-case-id", "value"),
            State("power-viz-contingency-id", "value"),
            State("power-viz-chat-input", "value")
        ]
    )
    def update_power_viz(viz_type, update_clicks, chat_clicks, case_id, contingency_id, chat_input):
        """Update power visualization based on user interactions"""
        ctx = callback_context
        power_viz_component = get_power_viz_component()
        
        if not ctx.triggered:
            # No trigger, initial load
            return power_viz_component.create_initial_figure(), power_viz_component.get_default_description()
            
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        # If chat triggered the update, check if it contains a visualization command
        if trigger_id == "power-viz-chat-send" and chat_input:
            # Check if chat message contains visualization commands
            if "voltage" in chat_input.lower():
                return power_viz_component.update_visualization('voltage', case_id, contingency_id)
            elif "load" in chat_input.lower():
                return power_viz_component.update_visualization('loading', case_id, contingency_id)
            elif "violat" in chat_input.lower():
                return power_viz_component.update_visualization('violations', case_id, contingency_id)
            elif "compar" in chat_input.lower() or "slr vs dlr" in chat_input.lower():
                return power_viz_component.update_visualization('comparison', case_id, contingency_id)
            elif "generat" in chat_input.lower():
                return power_viz_component.update_visualization('generators', case_id, contingency_id)
            elif "network" in chat_input.lower() or "show network" in chat_input.lower():
                return power_viz_component.update_visualization('network', case_id, contingency_id)
            else:
                # No visualization command, return current state
                return dash.no_update, dash.no_update
        
        # Update triggered by selector or button
        return power_viz_component.update_visualization(viz_type, case_id, contingency_id)
    
    @app.callback(
        Output("power-viz-chat-container", "is_open"),
        [Input("power-viz-chat-toggle", "n_clicks"), 
         Input("power-viz-chat-close", "n_clicks")],
        [State("power-viz-chat-container", "is_open")]
    )
    def toggle_chat(toggle_clicks, close_clicks, is_open):
        """Toggle AI chat interface visibility"""
        ctx = callback_context
        if not ctx.triggered:
            return is_open
            
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if trigger_id == "power-viz-chat-toggle":
            return not is_open
        elif trigger_id == "power-viz-chat-close":
            return False
        return is_open
    
    @app.callback(
        Output("power-viz-chat-messages", "children"),
        Output("power-viz-chat-input", "value"),
        [Input("power-viz-chat-send", "n_clicks")],
        [State("power-viz-chat-input", "value"),
         State("power-viz-chat-messages", "children"),
         State("power-viz-selector", "value")]
    )
    def update_chat(n_clicks, user_message, current_messages, current_viz_type):
        """Update chat messages when user sends a message"""
        if not n_clicks or not user_message:
            return current_messages, ""
            
        power_viz_component = get_power_viz_component()
        
        # Add user message
        user_msg = html.Div(
            f"You: {user_message}",
            className="mb-2 p-2 bg-light rounded text-right"
        )
        
        # Get AI response
        ai_response = power_viz_component.process_ai_chat(user_message, current_viz_type)
        
        # Add AI response
        ai_msg = html.Div(
            f"AI: {ai_response}",
            className="mb-2 p-2 bg-primary text-white rounded"
        )
        
        # Update messages
        updated_messages = current_messages + [user_msg, ai_msg]
        
        return updated_messages, ""


# Global instance of PowerVizComponent
_power_viz_component = None

def get_power_viz_component():
    """Get the global PowerVizComponent instance"""
    global _power_viz_component
    if _power_viz_component is None:
        _power_viz_component = PowerVizComponent()
    return _power_viz_component