"""
Power System Statistical Visualization Tool
==========================================

Interactive visualization tool for power system statistical analyses.
Features dropdown menus to select different statistical analyses and
creates comprehensive visualizations.

Usage: Run this file to start the Dash web application.
"""

import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import plotly.figure_factory as ff
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import os
import sys

# Import the statistical analyzer
try:
    from power_system_statistical_analyzer import PowerSystemStatisticalAnalyzer
    print("✅ Statistical analyzer imported successfully")
except ImportError:
    print("❌ Could not import statistical analyzer. Please ensure the file is in the same directory.")
    sys.exit(1)

class PowerSystemStatisticalVisualizer:
    """
    Visualization engine for power system statistical analyses
    """
    
    def __init__(self, database_path):
        self.database_path = database_path
        self.analyzer = PowerSystemStatisticalAnalyzer(database_path)
        
        # Initialize Dash app
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.app.title = "Power System Statistical Analysis Visualizer"
        
        # Cache for analysis results to avoid recomputation
        self.analysis_cache = {}
        
        self.setup_layout()
        self.setup_callbacks()
    
    def setup_layout(self):
        """Setup the Dash app layout"""
        
        self.app.layout = dbc.Container([
            # Header
            dbc.Row([
                dbc.Col([
                    html.H1("📊 Power System Statistical Analysis Visualizer", 
                           className="text-center mb-4",
                           style={"color": "#0D8767", "fontWeight": "bold"}),
                    html.P("Comprehensive statistical analysis and visualization for power system data",
                          className="text-center text-muted mb-4")
                ])
            ]),
            
            # Control Panel
            dbc.Card([
                dbc.CardHeader("🎛️ Analysis Controls"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("📈 Select Analysis Type:", className="fw-bold"),
                            dcc.Dropdown(
                                id="analysis-type-dropdown",
                                options=[
                                    {"label": "🔗 Correlation Analysis", "value": "correlation"},
                                    {"label": "🎲 Monte Carlo Risk Assessment", "value": "monte_carlo"},
                                    {"label": "📊 Sensitivity Analysis", "value": "sensitivity"},
                                    {"label": "🎯 Clustering Analysis", "value": "clustering"},
                                    {"label": "⚡ Reliability Statistics", "value": "reliability"},
                                    {"label": "💰 Economic Analysis", "value": "economic"},
                                    {"label": "🔋 Power Quality Analysis", "value": "power_quality"},
                                    {"label": "🌟 Comprehensive Overview", "value": "comprehensive"}
                                ],
                                value="correlation",
                                style={"marginBottom": "15px"}
                            )
                        ], width=6),
                        
                        dbc.Col([
                            html.Label("⚙️ Analysis Parameters:", className="fw-bold"),
                            html.Div(id="parameter-controls"),
                            html.Hr(),
                            dbc.Card([
                                dbc.CardBody([
                                    html.Label("📊 Dataset Scope:", className="fw-bold mb-2"),
                                    dbc.RadioItems(
                                        id="scope-selector",
                                        options=[
                                            {"label": "🎯 Sample Analysis (5 cases)", "value": "sample"},
                                            {"label": "🌍 Comprehensive Analysis (ALL 577 cases)", "value": "all"}
                                        ],
                                        value="sample",
                                        inline=True
                                    ),
                                    html.Small("⚠️ Comprehensive analysis may take several minutes", 
                                             className="text-warning")
                                ])
                            ], color="light", className="mt-2")
                        ], width=6)
                    ]),
                    
                    dbc.Row([
                        dbc.Col([
                            dbc.Button("🚀 Run Analysis", id="run-analysis-btn", 
                                     color="primary", className="mt-3", size="lg")
                        ], width=12, className="text-center")
                    ])
                ])
            ], className="mb-4"),
            
            # Loading indicator
            dcc.Loading(
                id="loading",
                type="default",
                children=[
                    # Results display area
                    html.Div(id="analysis-results"),
                ]
            ),
            
            # Footer
            html.Hr(),
            html.P("Power System Statistical Analysis Tool | Built with Dash & Plotly", 
                  className="text-center text-muted small")
            
        ], fluid=True)
    
    def setup_callbacks(self):
        """Setup Dash callbacks"""
        
        @self.app.callback(
            Output("parameter-controls", "children"),
            Input("analysis-type-dropdown", "value")
        )
        def update_parameter_controls(analysis_type):
            """Update parameter controls based on selected analysis"""
            
            if analysis_type == "monte_carlo":
                return [
                    html.Label("Number of Simulations:", className="small"),
                    dcc.Slider(
                        id="monte-carlo-sims",
                        min=100, max=2000, step=100, value=1000,
                        marks={i: str(i) for i in range(100, 2001, 500)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ]
            
            elif analysis_type == "clustering":
                return [
                    html.Label("Number of Clusters:", className="small"),
                    dcc.Slider(
                        id="clustering-clusters",
                        min=2, max=8, step=1, value=3,
                        marks={i: str(i) for i in range(2, 9)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ]
            
            elif analysis_type == "sensitivity":
                return [
                    html.Label("Perturbation %:", className="small"),
                    dcc.Slider(
                        id="sensitivity-perturbation",
                        min=1, max=20, step=1, value=5,
                        marks={i: f"{i}%" for i in range(1, 21, 5)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ]
            
            else:
                return [
                    html.Label("Base Case IDs:", className="small"),
                    dcc.Dropdown(
                        id="base-case-ids",
                        options=[
                            {"label": f"Case {i}", "value": i} for i in [42, 43, 44, 45, 46]
                        ],
                        value=[42, 43, 44, 45, 46],
                        multi=True
                    )
                ]
        
        @self.app.callback(
            Output("analysis-results", "children"),
            [Input("run-analysis-btn", "n_clicks")],
            [dash.dependencies.State("analysis-type-dropdown", "value"),
             dash.dependencies.State("monte-carlo-sims", "value"),
             dash.dependencies.State("clustering-clusters", "value"),
             dash.dependencies.State("sensitivity-perturbation", "value"),
             dash.dependencies.State("base-case-ids", "value"),
             dash.dependencies.State("scope-selector", "value")]
        )
        def run_analysis_and_visualize(n_clicks, analysis_type, monte_sims, n_clusters, 
                                      sensitivity_pert, base_cases, scope):
            """Run selected analysis and create visualizations"""
            
            if not n_clicks:
                return self.create_welcome_card()
            
            try:
                # Determine base cases based on scope
                if scope == "all":
                    analysis_base_cases = None  # Will use all base cases
                    use_all_cases = True
                    progress_msg = "🌍 Running comprehensive analysis on ALL 577 base cases..."
                else:
                    analysis_base_cases = base_cases or [42, 43, 44, 45, 46]
                    use_all_cases = False
                    progress_msg = f"🎯 Running sample analysis on {len(analysis_base_cases)} base cases..."
                
                # Show progress message
                print(progress_msg)
                
                # Get analysis results
                if analysis_type == "correlation":
                    results = self.analyzer.correlation_analysis(analysis_base_cases)
                    return self.visualize_correlation_analysis(results)
                
                elif analysis_type == "monte_carlo":
                    if use_all_cases:
                        results = self.analyzer.monte_carlo_risk_assessment(
                            base_case_id=42, n_simulations=monte_sims or 1000, analyze_all_cases=True)
                    else:
                        results = self.analyzer.monte_carlo_risk_assessment(
                            base_case_id=42, n_simulations=monte_sims or 1000)
                    return self.visualize_monte_carlo_analysis(results)
                
                elif analysis_type == "sensitivity":
                    results = self.analyzer.sensitivity_analysis(
                        base_case_id=42, perturbation_percent=sensitivity_pert or 5)
                    return self.visualize_sensitivity_analysis(results)
                
                elif analysis_type == "clustering":
                    results = self.analyzer.clustering_analysis(
                        base_case_ids=analysis_base_cases, 
                        n_clusters=n_clusters or 5)
                    return self.visualize_clustering_analysis(results)
                
                elif analysis_type == "reliability":
                    results = self.analyzer.reliability_statistics(analysis_base_cases)
                    return self.visualize_reliability_analysis(results)
                
                elif analysis_type == "economic":
                    results = self.analyzer.economic_analysis(analysis_base_cases or [42, 43, 44, 45, 46])
                    return self.visualize_economic_analysis(results)
                
                elif analysis_type == "power_quality":
                    results = self.analyzer.power_quality_analysis(analysis_base_cases or [42, 43, 44, 45, 46])
                    return self.visualize_power_quality_analysis(results)
                
                elif analysis_type == "comprehensive":
                    results = self.analyzer.comprehensive_analysis()
                    return self.visualize_comprehensive_analysis(results)
                
                else:
                    return dbc.Alert("Invalid analysis type selected", color="danger")
                    
            except Exception as e:
                return dbc.Alert(f"Error running analysis: {str(e)}", color="danger")
    
    def create_welcome_card(self):
        """Create welcome card"""
        return dbc.Card([
            dbc.CardHeader("👋 Welcome to Power System Statistical Analysis"),
            dbc.CardBody([
                html.H4("Get Started", className="card-title"),
                html.P("Select an analysis type from the dropdown above and click 'Run Analysis' to begin."),
                html.Ul([
                    html.Li("🔗 Correlation Analysis - Find relationships between system parameters"),
                    html.Li("🎲 Monte Carlo Risk Assessment - Probabilistic risk evaluation"),
                    html.Li("📊 Sensitivity Analysis - Parameter impact assessment"),
                    html.Li("🎯 Clustering Analysis - Group similar operating conditions"),
                    html.Li("⚡ Reliability Statistics - System reliability metrics"),
                    html.Li("💰 Economic Analysis - Generation cost analysis"),
                    html.Li("🔋 Power Quality Analysis - Voltage and power quality metrics"),
                    html.Li("🌟 Comprehensive Overview - All analyses combined")
                ])
            ])
        ])
    
    def visualize_correlation_analysis(self, results):
        """Create visualizations for correlation analysis"""
        if not results:
            return dbc.Alert("No correlation analysis results available", color="warning")
        
        components = []
        
        # Correlation Matrix Heatmap
        if 'correlation_matrix' in results:
            corr_data = pd.DataFrame(results['correlation_matrix'])
            
            fig_heatmap = px.imshow(corr_data, 
                                   color_continuous_scale='RdBu_r',
                                   aspect="auto",
                                   title="🔗 Correlation Matrix of Power System Parameters")
            fig_heatmap.update_layout(height=500)
            
            components.append(dbc.Card([
                dbc.CardHeader("Correlation Matrix"),
                dbc.CardBody([dcc.Graph(figure=fig_heatmap)])
            ], className="mb-4"))
        
        # Strong Correlations Table
        if 'strong_correlations' in results and results['strong_correlations']:
            strong_corr_df = pd.DataFrame(results['strong_correlations'])
            
            components.append(dbc.Card([
                dbc.CardHeader("Strong Correlations (|r| > 0.7)"),
                dbc.CardBody([
                    dbc.Table.from_dataframe(strong_corr_df, striped=True, bordered=True, hover=True)
                ])
            ], className="mb-4"))
        
        # PCA Analysis
        if 'pca_analysis' in results and results['pca_analysis']:
            pca_data = results['pca_analysis']
            if 'explained_variance_ratio' in pca_data:
                
                fig_pca = go.Figure(data=[
                    go.Bar(x=[f'PC{i+1}' for i in range(len(pca_data['explained_variance_ratio']))],
                           y=pca_data['explained_variance_ratio'],
                           text=[f'{v:.2%}' for v in pca_data['explained_variance_ratio']],
                           textposition='auto')
                ])
                fig_pca.update_layout(title="📊 PCA Explained Variance Ratio",
                                     xaxis_title="Principal Components",
                                     yaxis_title="Explained Variance Ratio")
                
                components.append(dbc.Card([
                    dbc.CardHeader("Principal Component Analysis"),
                    dbc.CardBody([dcc.Graph(figure=fig_pca)])
                ], className="mb-4"))
        
        return html.Div(components)
    
    def visualize_monte_carlo_analysis(self, results):
        """Create visualizations for Monte Carlo analysis"""
        if not results:
            return dbc.Alert("No Monte Carlo analysis results available", color="warning")
        
        components = []
        
        if 'simulation_results' in results:
            sim_df = pd.DataFrame(results['simulation_results'])
            
            # Risk Distribution Histogram
            fig_hist = make_subplots(rows=2, cols=2,
                                   subplot_titles=('Voltage Violations', 'Overload Risk',
                                                 'Generation Deficit', 'Total Load Distribution'))
            
            fig_hist.add_trace(go.Histogram(x=sim_df['voltage_violations'], name='Voltage Violations'),
                              row=1, col=1)
            fig_hist.add_trace(go.Histogram(x=sim_df['overload_risk'], name='Overload Risk'),
                              row=1, col=2)
            fig_hist.add_trace(go.Histogram(x=sim_df['generation_deficit'], name='Generation Deficit'),
                              row=2, col=1)
            fig_hist.add_trace(go.Histogram(x=sim_df['total_load'], name='Total Load'),
                              row=2, col=2)
            
            fig_hist.update_layout(height=600, title_text="🎲 Monte Carlo Risk Assessment Results")
            
            components.append(dbc.Card([
                dbc.CardHeader("Monte Carlo Simulation Results"),
                dbc.CardBody([dcc.Graph(figure=fig_hist)])
            ], className="mb-4"))
        
        # Risk Statistics
        if 'risk_statistics' in results:
            risk_stats = results['risk_statistics']
            
            metrics_cards = dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{risk_stats.get('high_risk_probability', 0):.2%}", 
                                   className="card-title text-danger"),
                            html.P("High Risk Probability", className="card-text")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{risk_stats.get('avg_voltage_violations', 0):.1f}", 
                                   className="card-title text-warning"),
                            html.P("Avg Voltage Violations", className="card-text")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{risk_stats.get('load_volatility', 0):.3f}", 
                                   className="card-title text-info"),
                            html.P("Load Volatility", className="card-text")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{risk_stats.get('generation_deficit_probability', 0):.2%}", 
                                   className="card-title text-success"),
                            html.P("Generation Deficit Prob", className="card-text")
                        ])
                    ])
                ], width=3)
            ])
            
            components.append(dbc.Card([
                dbc.CardHeader("Risk Statistics Summary"),
                dbc.CardBody([metrics_cards])
            ], className="mb-4"))
        
        return html.Div(components)
    
    def visualize_sensitivity_analysis(self, results):
        """Create visualizations for sensitivity analysis"""
        if not results:
            return dbc.Alert("No sensitivity analysis results available", color="warning")
        
        components = []
        
        if 'sensitivity_results' in results:
            sens_data = results['sensitivity_results']
            
            # Create sensitivity plot
            parameters = list(sens_data.keys())
            metrics = []
            
            if parameters:
                metrics = list(sens_data[parameters[0]].keys())
                
                fig_sens = go.Figure()
                
                for param in parameters:
                    sensitivity_values = [sens_data[param].get(metric, 0) for metric in metrics]
                    fig_sens.add_trace(go.Bar(name=param, x=metrics, y=sensitivity_values))
                
                fig_sens.update_layout(title="📊 Parameter Sensitivity Analysis",
                                      xaxis_title="System Metrics",
                                      yaxis_title="Sensitivity Coefficient",
                                      barmode='group')
                
                components.append(dbc.Card([
                    dbc.CardHeader("Sensitivity Analysis Results"),
                    dbc.CardBody([dcc.Graph(figure=fig_sens)])
                ], className="mb-4"))
        
        return html.Div(components)
    
    def visualize_clustering_analysis(self, results):
        """Create visualizations for clustering analysis"""
        if not results:
            return dbc.Alert("No clustering analysis results available", color="warning")
        
        components = []
        
        if 'cluster_results' in results:
            cluster_df = pd.DataFrame(results['cluster_results'])
            
            # PCA Cluster Plot
            fig_cluster = px.scatter(cluster_df, x='pca_x', y='pca_y', color='cluster',
                                   hover_data=['case_id', 'avg_voltage', 'total_load'],
                                   title="🎯 Operating Conditions Clustering (PCA View)")
            fig_cluster.update_layout(height=500)
            
            components.append(dbc.Card([
                dbc.CardHeader("Clustering Analysis - PCA Visualization"),
                dbc.CardBody([dcc.Graph(figure=fig_cluster)])
            ], className="mb-4"))
            
            # Cluster characteristics
            if 'silhouette_score' in results:
                score_card = dbc.Alert([
                    html.H4("Clustering Quality Metrics"),
                    html.P(f"Silhouette Score: {results['silhouette_score']:.3f}"),
                    html.P(f"Optimal Clusters: {results.get('optimal_clusters', 'N/A')}")
                ], color="info")
                
                components.append(score_card)
        
        return html.Div(components)
    
    def visualize_reliability_analysis(self, results):
        """Create visualizations for reliability analysis"""
        if not results:
            return dbc.Alert("No reliability analysis results available", color="warning")
        
        components = []
        
        if 'contingency_analysis' in results:
            reliability_df = pd.DataFrame(results['contingency_analysis'])
            
            # Violation Rate by Case
            fig_reliability = px.bar(reliability_df, x='base_case_id', y='violation_rate',
                                   color='contingency_id',
                                   title="⚡ Violation Rates by Base Case and Contingency")
            
            components.append(dbc.Card([
                dbc.CardHeader("Reliability Analysis"),
                dbc.CardBody([dcc.Graph(figure=fig_reliability)])
            ], className="mb-4"))
        
        return html.Div(components)
    
    def visualize_economic_analysis(self, results):
        """Create visualizations for economic analysis"""
        if not results:
            return dbc.Alert("No economic analysis results available", color="warning")
        
        components = []
        
        if 'economic_analysis' in results:
            economic_df = pd.DataFrame(results['economic_analysis'])
            
            # Cost Analysis
            fig_economic = px.bar(economic_df, x='case_id', y='total_cost_usd',
                                title="💰 Total System Cost by Case")
            
            components.append(dbc.Card([
                dbc.CardHeader("Economic Analysis"),
                dbc.CardBody([dcc.Graph(figure=fig_economic)])
            ], className="mb-4"))
        
        return html.Div(components)
    
    def visualize_power_quality_analysis(self, results):
        """Create visualizations for power quality analysis"""
        if not results:
            return dbc.Alert("No power quality analysis results available", color="warning")
        
        components = []
        
        if 'power_quality_analysis' in results:
            quality_df = pd.DataFrame(results['power_quality_analysis'])
            
            # Voltage Quality Index
            fig_quality = px.line(quality_df, x='case_id', y='voltage_quality_index',
                                title="🔋 Power Quality Index by Case")
            
            components.append(dbc.Card([
                dbc.CardHeader("Power Quality Analysis"),
                dbc.CardBody([dcc.Graph(figure=fig_quality)])
            ], className="mb-4"))
        
        return html.Div(components)
    
    def visualize_comprehensive_analysis(self, results):
        """Create comprehensive overview visualization"""
        if not results or 'analyses' not in results:
            return dbc.Alert("No comprehensive analysis results available", color="warning")
        
        components = []
        
        # Create summary cards for each analysis
        analyses = results['analyses']
        
        for analysis_name, analysis_results in analyses.items():
            if analysis_results:
                card = dbc.Card([
                    dbc.CardHeader(f"✅ {analysis_name.replace('_', ' ').title()}"),
                    dbc.CardBody([
                        html.P("Analysis completed successfully", className="text-success"),
                        html.Small(f"Results available: {len(analysis_results)} items")
                    ])
                ])
                components.append(card)
        
        if components:
            return dbc.Row([dbc.Col(card, width=6) for card in components])
        else:
            return dbc.Alert("No analysis results available", color="warning")
    
    def run_server(self, debug=True, port=8060):
        """Run the Dash server"""
        print(f"🚀 Starting Power System Statistical Visualizer...")
        print(f"📱 Access at: http://127.0.0.1:{port}")
        print(f"🔗 Database: {self.database_path}")
        
        self.app.run(debug=debug, host="127.0.0.1", port=port)

def main():
    """Main function to run the visualizer"""
    
    # Try to find the database
    possible_paths = [
        "ndata.db",
        "C:/Users/nira771/SULI_FALL/ndata.db",
        "../SULI_FALL/ndata.db",
        "C:/Users/nira771/Project finalized/Codes/final/data.db"
    ]
    
    database_path = None
    for path in possible_paths:
        if os.path.exists(path):
            database_path = path
            break
    
    if not database_path:
        print("❌ Database not found. Please ensure ndata.db is available.")
        print("Tried paths:", possible_paths)
        return
    
    print(f"✅ Found database at: {database_path}")
    
    # Create and run visualizer
    visualizer = PowerSystemStatisticalVisualizer(database_path)
    visualizer.run_server(debug=False, port=8060)

if __name__ == "__main__":
    main()